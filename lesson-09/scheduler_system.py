"""
자동매매 시스템용 스케줄링 시스템

요구사항 반영:
1) 정확한 시간 기반 실행 (APScheduler + KST 타임존, Cron/Interval 트리거)
2) 우선순위 기반 작업 관리 (PriorityQueue 디스패처 + 워커 스레드)
3) 작업 실패 시 재시도 로직 (지수 백오프 + 지터, 최대 재시도)
4) 작업 간 의존성 관리 (간단 DAG, 완료 상태 영속화)
5) 동적 스케줄 변경 지원 (YAML 설정 핫 리로드)

주의: 본 모듈은 전략/주문/리스크 등 도메인 로직을 호출하기 위한 인프라입니다.
여기서는 실제 거래 로직 대신 안전한 더미 작업을 제공합니다.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import random
import signal
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone


# =========================
# 로깅 설정
# =========================
logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
logger.addHandler(_handler)


# =========================
# 예외/재시도/백오프 정책
# =========================


class NetworkError(Exception):
    """네트워크 연결 문제"""


class ApiServerError(Exception):
    """API 서버 5xx 등"""


class BadDataError(Exception):
    """유효하지 않은 데이터 수신"""

@dataclass
class RetryPolicy:
    """재시도 정책 정의

    - max_retries: 최대 재시도 횟수
    - base_delay_sec: 최초 지연
    - max_delay_sec: 최대 지연 상한
    - jitter_frac: 지연에 랜덤 지터 적용 비율(0~1)
    """

    max_retries: int = 3
    base_delay_sec: float = 0.5
    max_delay_sec: float = 8.0
    jitter_frac: float = 0.2

    def compute_delay(self, attempt_idx: int) -> float:
        """지수 백오프 + 지터 계산"""
        delay = min(self.base_delay_sec * (2 ** attempt_idx), self.max_delay_sec)
        jitter = delay * self.jitter_frac * (random.random() * 2 - 1)
        return max(0.0, delay + jitter)


def default_should_retry(exc: Exception) -> bool:
    """예외 타입별 재시도 여부 결정
    - NetworkError, ApiServerError: 재시도 대상
    - BadDataError, ValueError, MemoryError: 재시도하지 않음
    - 그 외: 1회 정도 재시도 허용(보수적)
    """

    if isinstance(exc, (NetworkError, ApiServerError)):
        return True
    if isinstance(exc, (BadDataError, ValueError, MemoryError)):
        return False
    return True


def with_retry(policy: RetryPolicy, should_retry: Callable[[Exception], bool]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """함수에 재시도 로직을 데코레이터로 적용(예외 유형 기반)"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if not should_retry(exc) or attempt >= policy.max_retries:
                        logger.error("작업 실패(재시도 불가 또는 한도 초과): %s", func.__name__, exc_info=exc)
                        break
                    delay = policy.compute_delay(attempt)
                    logger.warning(
                        "작업 실패(%s: %s), %d회차 재시도 전 %.2fs 대기",
                        func.__name__, type(exc).__name__, attempt + 1, delay,
                    )
                    time.sleep(delay)
            if last_exc is not None:
                raise last_exc
        return wrapper
    return decorator


# =========================
# 작업 정의 및 디스패치
# =========================
TaskCallable = Callable[[Dict[str, Any]], None]


@dataclass(order=True)
class PrioritizedTask:
    """우선순위 큐에 넣을 작업 단위"""

    priority: int
    scheduled_at_epoch: float
    task_id: str = field(compare=False)
    func: TaskCallable = field(compare=False)
    payload: Dict[str, Any] = field(compare=False, default_factory=dict)
    depends_on: Tuple[str, ...] = field(compare=False, default_factory=tuple)


class DependencyStore:
    """작업 완료 상태를 간단히 저장/조회 (파일 기반 영속화)

    - 성공적으로 완료된 작업의 최근 완료 타임스탬프를 저장
    - 의존성 확인 시 ID 기준으로 성공 여부 판단
    """

    def __init__(self, state_path: str) -> None:
        self._state_path = state_path
        self._lock = threading.RLock()
        self._state: Dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except Exception:  # noqa: BLE001
                logger.exception("의존성 상태 파일 로드 실패, 초기화합니다: %s", self._state_path)
                self._state = {}

    def _save(self) -> None:
        tmp = f"{self._state_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._state_path)

    def mark_completed(self, task_id: str) -> None:
        with self._lock:
            self._state[task_id] = time.time()
            self._save()

    def has_completed(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._state


class PriorityDispatcher:
    """우선순위 기반 작업 디스패처

    - APScheduler는 트리거링만 담당, 실제 실행은 디스패처에서 직렬/병렬 제어
    - 스레드 워커들이 PriorityQueue에서 작업을 가져와 실행
    - 작업 간 의존성 만족 시에만 실행
    """

    def __init__(
        self,
        dependency_store: DependencyStore,
        num_workers: int = 3,
        default_retry_policy: Optional[RetryPolicy] = None,
        queue_maxsize: int = 1000,
        should_retry: Callable[[Exception], bool] = default_should_retry,
    ) -> None:
        self._queue: "queue.PriorityQueue[PrioritizedTask]" = queue.PriorityQueue(maxsize=queue_maxsize)
        self._stop_event = threading.Event()
        self._workers: List[threading.Thread] = []
        self._dependency_store = dependency_store
        self._default_retry_policy = default_retry_policy or RetryPolicy()
        self._should_retry = should_retry

        for idx in range(num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"dispatcher-worker-{idx}", daemon=True)
            t.start()
            self._workers.append(t)

    def submit(self, task: PrioritizedTask) -> None:
        logger.info("작업 큐 등록: id=%s priority=%d", task.task_id, task.priority)
        try:
            # 백프레셔: 꽉 찼으면 최대 2초 대기 후 드롭
            self._queue.put(task, timeout=2.0)
        except queue.Full:
            logger.error("작업 큐 포화로 작업 드롭: id=%s priority=%d", task.task_id, task.priority)

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                task: PrioritizedTask = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if task.depends_on:
                missing: List[str] = [d for d in task.depends_on if not self._dependency_store.has_completed(d)]
                if missing:
                    # 의존성 미충족: 잠시 뒤 재등록(낮은 우선순위 유지)
                    logger.info("의존성 대기: %s -> 대기중: %s", task.task_id, ",".join(missing))
                    time.sleep(0.5)
                    self._queue.put(task)
                    self._queue.task_done()
                    continue

            # 재시도 정책 적용(예외 유형 기반)
            execute = with_retry(self._default_retry_policy, self._should_retry)(task.func)
            try:
                execute(task.payload)
                self._dependency_store.mark_completed(task.task_id)
                logger.info("작업 성공: %s", task.task_id)
            except Exception as exc:  # noqa: BLE001
                # 메모리 부족 등 치명적 예외는 즉시 디스패처 중지 신호
                if isinstance(exc, MemoryError):
                    logger.critical("메모리 부족 감지, 디스패처를 중지합니다: %s", task.task_id, exc_info=exc)
                    self._stop_event.set()
                logger.exception("작업 실패: %s", task.task_id)
            finally:
                self._queue.task_done()

    def shutdown(self) -> None:
        self._stop_event.set()
        # 큐를 깨워 종료 유도
        for _ in self._workers:
            self._queue.put(
                PrioritizedTask(priority=9999, scheduled_at_epoch=time.time(), task_id="__stop__", func=lambda _: None)
            )
        for t in self._workers:
            t.join(timeout=3)


# =========================
# 작업 구현(도메인 더미)
# =========================
def _now_kst() -> str:
    return datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")


def job_start_trading(payload: Dict[str, Any]) -> None:
    """거래 시작 작업(더미)
    실제 구현에서는 트레이딩 시스템 상태를 활성화하고 전략/시세 수집을 가동합니다.
    """

    logger.info("[거래 시작] %s | payload=%s", _now_kst(), payload)


def job_stop_trading(payload: Dict[str, Any]) -> None:
    """거래 종료 작업(더미)
    실제 구현에서는 신규 주문 차단, 포지션 정리(정책에 따름), 안전 셧다운을 수행합니다.
    """

    logger.info("[거래 종료] %s | payload=%s", _now_kst(), payload)


def job_evaluate_conditions(payload: Dict[str, Any]) -> None:
    """주기적 거래 조건 평가(더미)
    실제 구현에서는 활성 전략에 대해 시그널 산출 및 주문 파이프라인을 호출합니다.
    """

    logger.info("[조건 평가] %s | symbols=%s", _now_kst(), payload.get("symbols", []))


def job_hourly_status_report(payload: Dict[str, Any]) -> None:
    """시간별 상태 보고(더미)
    실제 구현에서는 PnL/포지션/에러/리소스/레이트리밋 보고서를 생성, 알림 전송합니다.
    """

    logger.info("[상태 보고] %s | detail=%s", _now_kst(), payload.get("detail", "summary"))


def job_midnight_maintenance(payload: Dict[str, Any]) -> None:
    """자정 데이터 정리/백업(더미)"""

    logger.info("[자정 정리/백업] %s | vacuum=%s backup=%s", _now_kst(), True, True)


def job_system_health_check(payload: Dict[str, Any]) -> None:
    """시스템 헬스체크(더미)"""

    logger.info("[헬스체크] %s | ping=%s", _now_kst(), "ok")


TASK_REGISTRY: Dict[str, TaskCallable] = {
    "start_trading": job_start_trading,
    "stop_trading": job_stop_trading,
    "evaluate_conditions": job_evaluate_conditions,
    "hourly_status_report": job_hourly_status_report,
    "midnight_maintenance": job_midnight_maintenance,
    "system_health_check": job_system_health_check,
}


# =========================
# 스케줄 매니저
# =========================
class ScheduleManager:
    """APScheduler 기반 스케줄 관리 + 동적 리로드

    - YAML 설정을 기반으로 작업 등록/갱신/삭제
    - 작업은 실제 실행 시 PriorityDispatcher로 전달
    """

    def __init__(
        self,
        config_path: str,
        dispatcher: PriorityDispatcher,
        tz: str = "Asia/Seoul",
    ) -> None:
        self._config_path = config_path
        self._dispatcher = dispatcher
        self._tz = timezone(tz)
        self._sched = BackgroundScheduler(timezone=self._tz)
        self._config_mtime = 0.0
        self._lock = threading.RLock()
        self._watcher_thread = threading.Thread(target=self._watch_config_loop, daemon=True)

    def start(self) -> None:
        with self._lock:
            self._apply_config()
            self._sched.start()
            self._watcher_thread.start()
        logger.info("스케줄러 시작")

    def shutdown(self) -> None:
        with self._lock:
            self._sched.shutdown(wait=False)
        logger.info("스케줄러 중지")

    def _watch_config_loop(self) -> None:
        # 파일 변경 감시(간단 폴링) → 변경 시 리로드
        while True:
            try:
                mtime = os.path.getmtime(self._config_path)
            except FileNotFoundError:
                time.sleep(1.0)
                continue
            if mtime > self._config_mtime:
                logger.info("스케줄 설정 변경 감지 → 리로드")
                with self._lock:
                    self._apply_config()
            time.sleep(1.0)

    def _apply_config(self) -> None:
        cfg = self._load_yaml()
        self._sched.remove_all_jobs()

        jobs = cfg.get("jobs", [])
        for job_cfg in jobs:
            self._register_job(job_cfg)

        self._config_mtime = os.path.getmtime(self._config_path) if os.path.exists(self._config_path) else time.time()

    def _load_yaml(self) -> Dict[str, Any]:
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _register_job(self, job_cfg: Dict[str, Any]) -> None:
        # 필수: id, task, trigger
        job_id: str = job_cfg["id"]
        task_key: str = job_cfg["task"]
        trigger: str = job_cfg.get("trigger", "cron")
        priority: int = int(job_cfg.get("priority", 5))
        depends_on: Tuple[str, ...] = tuple(job_cfg.get("depends_on", []))
        payload: Dict[str, Any] = job_cfg.get("payload", {})

        if task_key not in TASK_REGISTRY:
            logger.error("알 수 없는 task 키: %s (job_id=%s)", task_key, job_id)
            return

        def _enqueue() -> None:
            self._dispatcher.submit(
                PrioritizedTask(
                    priority=priority,
                    scheduled_at_epoch=time.time(),
                    task_id=job_id,
                    func=TASK_REGISTRY[task_key],
                    payload=payload,
                    depends_on=depends_on,
                )
            )

        if trigger == "cron":
            # cron 필드: second/minute/hour/day/month/day_of_week 지원
            fields = {k: v for k, v in job_cfg.get("cron", {}).items() if v is not None}
            trig = CronTrigger(timezone=self._tz, **fields)
            self._sched.add_job(_enqueue, trig, id=job_id, replace_existing=True)
        elif trigger == "interval":
            fields = {k: int(v) for k, v in job_cfg.get("interval", {}).items()}
            trig = IntervalTrigger(timezone=self._tz, **fields)
            self._sched.add_job(_enqueue, trig, id=job_id, replace_existing=True)
        else:
            logger.error("지원하지 않는 트리거 타입: %s (job_id=%s)", trigger, job_id)


# =========================
# 기본 진입점
# =========================
def build_default_config_if_missing(config_path: str) -> None:
    """기본 스케줄 설정 파일이 없으면 생성"""

    if os.path.exists(config_path):
        return
    default_cfg = {
        "jobs": [
            {
                "id": "start_trading_daily",
                "task": "start_trading",
                "trigger": "cron",
                "cron": {"hour": 9, "minute": 0, "second": 0},
                "priority": 1,
            },
            {
                "id": "stop_trading_daily",
                "task": "stop_trading",
                "trigger": "cron",
                "cron": {"hour": 23, "minute": 0, "second": 0},
                "priority": 1,
            },
            {
                "id": "evaluate_conditions_every_5m",
                "task": "evaluate_conditions",
                "trigger": "interval",
                "interval": {"minutes": 5},
                "priority": 3,
                "depends_on": ["start_trading_daily"],
                "payload": {"symbols": ["KRW-BTC", "KRW-ETH"]},
            },
            {
                "id": "hourly_status_report",
                "task": "hourly_status_report",
                "trigger": "cron",
                "cron": {"minute": 0, "second": 5},
                "priority": 5,
                "payload": {"detail": "summary"},
            },
            {
                "id": "midnight_maintenance",
                "task": "midnight_maintenance",
                "trigger": "cron",
                "cron": {"hour": 0, "minute": 0, "second": 10},
                "priority": 2,
                "depends_on": ["stop_trading_daily"],
            },
            {
                "id": "system_health_check",
                "task": "system_health_check",
                "trigger": "interval",
                "interval": {"minutes": 1},
                "priority": 0,
            },
        ]
    }
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_cfg, f, allow_unicode=True, sort_keys=False)


def main() -> None:
    # 경로 설정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "schedule_config.yaml")
    state_path = os.path.join(base_dir, ".scheduler_state.json")

    build_default_config_if_missing(config_path)

    # 의존성 저장소 & 디스패처
    dep_store = DependencyStore(state_path)
    dispatcher = PriorityDispatcher(dep_store, num_workers=4, default_retry_policy=RetryPolicy())

    # 스케줄 매니저
    mgr = ScheduleManager(config_path=config_path, dispatcher=dispatcher)

    # 종료 시그널 처리
    stop_event = threading.Event()

    def _graceful_shutdown(signum: int, _frame: Any) -> None:
        logger.info("종료 시그널 수신: %s", signum)
        mgr.shutdown()
        dispatcher.shutdown()
        stop_event.set()

    signal.signal(signal.SIGINT, _graceful_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _graceful_shutdown)

    # 시작
    mgr.start()
    logger.info("실시간 스케줄링 시스템 구동 완료")

    # 대기(Windows 서비스/도커 환경 고려해 이벤트 대기 루프 사용)
    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    finally:
        _graceful_shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()



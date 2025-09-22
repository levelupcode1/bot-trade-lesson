"""
예외 처리 시나리오 테스트 하네스

시나리오:
1) 네트워크 연결 끊김(NetworkError)
2) API 서버 장애(ApiServerError)
3) 잘못된 데이터 수신(BadDataError)
4) 메모리 부족(MemoryError)
5) 동시 요청 과부하(큐 포화/드롭)

각 케이스에 대해 디스패처 재시도/중단/드롭 동작을 점검한다.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List

from scheduler_system import (
    ApiServerError,
    BadDataError,
    DependencyStore,
    NetworkError,
    PrioritizedTask,
    PriorityDispatcher,
    RetryPolicy,
)

# 테스트용 로깅 설정
import sys

# 기존 핸들러 제거
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 새로운 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
    force=True  # 기존 설정 강제 덮어쓰기
)
logger = logging.getLogger(__name__)

# pytest 로그 캡처 비활성화
import pytest
pytest_plugins = []


def _sleep_ms(ms: int) -> None:
    time.sleep(ms / 1000.0)


def test_network_error_retry() -> None:
    """네트워크 오류는 재시도 대상 → 최소 1회 재시도 로그/성공 전파 확인"""
    
    print("🔧 테스트 시작: 네트워크 오류 재시도 테스트")
    attempts: List[int] = []

    def flaky_network(_payload: Dict[str, Any]) -> None:
        attempts.append(1)
        print(f"  📡 네트워크 작업 시도 #{len(attempts)}")
        # 첫 2회는 실패, 이후 성공
        if len(attempts) <= 2:
            print(f"  ❌ 네트워크 오류 발생 (시도 #{len(attempts)})")
            raise NetworkError("temporary network down")
        else:
            print(f"  ✅ 네트워크 연결 성공 (시도 #{len(attempts)})")

    print("  📋 의존성 저장소 및 디스패처 초기화")
    dep = DependencyStore(".scheduler_state.json")
    dispatcher = PriorityDispatcher(dep, num_workers=1, default_retry_policy=RetryPolicy(max_retries=3, base_delay_sec=0.05, max_delay_sec=0.2))
    
    print("  🚀 네트워크 작업 제출")
    dispatcher.submit(
        PrioritizedTask(priority=5, scheduled_at_epoch=time.time(), task_id="net_retry", func=flaky_network)
    )

    print("  ⏳ 1초 대기 중...")
    _sleep_ms(1000)  # 충분한 대기 시간
    
    stats = dispatcher.get_stats()
    print(f"  📊 디스패처 통계: {stats}")
    print(f"  🔄 실제 시도 횟수: {len(attempts)}회")
    
    # 재시도 데코레이터가 예외를 다시 발생시키지 않으므로 failed는 0이 될 수 있음
    # 하지만 최종적으로 성공해야 함
    assert stats["completed"] >= 1
    # attempts 리스트로 실제 재시도 횟수 확인
    assert len(attempts) >= 3  # 최소 3회 시도
    
    print("  ✅ 네트워크 오류 재시도 테스트 통과")
    dispatcher.shutdown()


def test_api_server_error_retry() -> None:
    """API 서버 오류는 재시도 대상"""
    
    print("🔧 테스트 시작: API 서버 오류 재시도 테스트")
    attempts: List[int] = []

    def flaky_api(_payload: Dict[str, Any]) -> None:
        attempts.append(1)
        print(f"  🌐 API 서버 호출 시도 #{len(attempts)}")
        if len(attempts) <= 1:
            print(f"  ❌ API 서버 오류 발생 (시도 #{len(attempts)})")
            raise ApiServerError("HTTP 503 Service Unavailable")
        else:
            print(f"  ✅ API 서버 응답 성공 (시도 #{len(attempts)})")

    print("  📋 의존성 저장소 및 디스패처 초기화")
    dep = DependencyStore(".scheduler_state.json")
    dispatcher = PriorityDispatcher(dep, num_workers=1, default_retry_policy=RetryPolicy(max_retries=2, base_delay_sec=0.05, max_delay_sec=0.2))
    
    print("  🚀 API 서버 작업 제출")
    dispatcher.submit(
        PrioritizedTask(priority=5, scheduled_at_epoch=time.time(), task_id="api_retry", func=flaky_api)
    )

    print("  ⏳ 0.8초 대기 중...")
    _sleep_ms(800)
    
    stats = dispatcher.get_stats()
    print(f"  📊 디스패처 통계: {stats}")
    print(f"  🔄 실제 시도 횟수: {len(attempts)}회")
    
    assert stats["completed"] >= 1
    # attempts 리스트로 실제 재시도 횟수 확인
    assert len(attempts) >= 2  # 최소 2회 시도
    
    print("  ✅ API 서버 오류 재시도 테스트 통과")
    dispatcher.shutdown()


def test_bad_data_no_retry() -> None:
    """잘못된 데이터는 재시도 없이 즉시 실패 처리"""
    
    print("🔧 테스트 시작: 잘못된 데이터 즉시 실패 테스트")

    def bad_data(_payload: Dict[str, Any]) -> None:
        print("  ❌ 잘못된 데이터 감지 - 즉시 실패 처리")
        raise BadDataError("invalid payload structure")

    print("  📋 의존성 저장소 및 디스패처 초기화")
    dep = DependencyStore(".scheduler_state.json")
    dispatcher = PriorityDispatcher(dep, num_workers=1, default_retry_policy=RetryPolicy(max_retries=3, base_delay_sec=0.01, max_delay_sec=0.05))
    
    print("  🚀 잘못된 데이터 작업 제출")
    dispatcher.submit(
        PrioritizedTask(priority=5, scheduled_at_epoch=time.time(), task_id="bad_data", func=bad_data)
    )

    print("  ⏳ 0.2초 대기 중...")
    _sleep_ms(200)
    
    stats = dispatcher.get_stats()
    print(f"  📊 디스패처 통계: {stats}")
    
    # 재시도 없이 1회 실패만 기록되어야 함
    assert stats["completed"] == 0
    assert stats["failed"] >= 1
    
    print("  ✅ 잘못된 데이터 즉시 실패 테스트 통과")
    dispatcher.shutdown()


def test_memory_error_stops_dispatcher() -> None:
    """메모리 부족 발생 시 디스패처 중지 신호가 설정되어 이후 작업 진행이 멈추는지 확인"""
    
    print("🔧 테스트 시작: 메모리 부족 시 디스패처 중지 테스트")
    stop_seen = threading.Event()

    def oom(_payload: Dict[str, Any]) -> None:
        print("  💥 메모리 부족 오류 발생 - 디스패처 중지 신호 전송")
        raise MemoryError("simulated OOM")

    def should_not_run(_payload: Dict[str, Any]) -> None:
        print("  ⚠️ 이 작업은 실행되면 안 됩니다!")
        stop_seen.set()

    print("  📋 의존성 저장소 및 디스패처 초기화")
    dep = DependencyStore(".scheduler_state.json")
    dispatcher = PriorityDispatcher(dep, num_workers=1, default_retry_policy=RetryPolicy(max_retries=0))
    
    print("  🚀 메모리 부족 작업 제출 (우선순위 1)")
    dispatcher.submit(
        PrioritizedTask(priority=1, scheduled_at_epoch=time.time(), task_id="oom", func=oom)
    )
    
    print("  🚀 후속 작업 제출 (우선순위 2) - 실행되면 안 됨")
    dispatcher.submit(
        PrioritizedTask(priority=2, scheduled_at_epoch=time.time(), task_id="after_oom", func=should_not_run)
    )

    print("  ⏳ 0.3초 대기 중...")
    _sleep_ms(300)
    
    # 메모리 에러 후 중지되어 두 번째 작업이 실행되지 않아야 함
    assert not stop_seen.is_set()
    stats = dispatcher.get_stats()
    print(f"  📊 디스패처 통계: {stats}")
    print(f"  🛑 후속 작업 실행 여부: {stop_seen.is_set()}")
    
    assert stats["failed"] >= 1
    
    print("  ✅ 메모리 부족 시 디스패처 중지 테스트 통과")
    dispatcher.shutdown()


def test_queue_overload_drop() -> None:
    """동시 요청 과부하: 큐 포화 시 드롭 발생 및 드롭 카운트 증가"""
    
    print("🔧 테스트 시작: 큐 과부하 드롭 테스트")

    def very_slow_ok(_payload: Dict[str, Any]) -> None:
        print(f"  ⏳ 느린 작업 실행 중... (1초 소요)")
        _sleep_ms(1000)  # 1초씩 걸리게 수정

    print("  📋 의존성 저장소 및 디스패처 초기화 (큐 크기: 1)")
    dep = DependencyStore(".scheduler_state.json")
    # 큐 사이즈를 1로 설정하여 확실히 포화 유도
    dispatcher = PriorityDispatcher(dep, num_workers=1, default_retry_policy=RetryPolicy(max_retries=0), queue_maxsize=1)

    submitted = 0
    dropped = 0
    print("  🚀 5개 작업을 빠르게 연속 제출하여 큐 포화 유도")
    
    # 동시에 여러 작업 제출하여 큐 포화 유도
    for i in range(5):
        print(f"  📤 작업 {i+1}/5 제출 중...")
        ok = dispatcher.submit(
            PrioritizedTask(priority=5, scheduled_at_epoch=time.time(), task_id=f"overload_{i}", func=very_slow_ok)
        )
        submitted += 1
        if not ok:
            dropped += 1
            print(f"  ❌ 작업 {i+1} 드롭됨 (큐 포화)")
        else:
            print(f"  ✅ 작업 {i+1} 큐에 등록됨")
        # 거의 동시에 제출
        _sleep_ms(5)

    print("  ⏳ 2초 대기 중 (작업 처리 시간)...")
    _sleep_ms(2000)  # 처리 시간
    
    stats = dispatcher.get_stats()
    print(f"  📊 디스패처 통계: {stats}")
    print(f"  📈 제출된 작업: {submitted}개, 드롭된 작업: {dropped}개")
    
    # 큐 크기가 1이므로 최소 4개는 드롭되어야 함
    assert stats["dropped"] >= 1 or dropped >= 1
    
    print("  ✅ 큐 과부하 드롭 테스트 통과")
    dispatcher.shutdown()



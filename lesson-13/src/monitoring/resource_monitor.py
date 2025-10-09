#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 리소스 모니터

최적화 포인트:
1. CPU/메모리 사용량 추적
2. 스레드/프로세스 모니터링
3. 네트워크 I/O 추적
4. 자동 리소스 최적화
"""

import psutil
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from collections import deque


@dataclass
class ResourceSnapshot:
    """리소스 스냅샷"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    thread_count: int
    io_read_mb: float
    io_write_mb: float


class ResourceMonitor:
    """시스템 리소스 모니터"""
    
    def __init__(self, 
                 check_interval: int = 5,
                 history_size: int = 720):  # 1시간 (5초 * 720)
        """
        Args:
            check_interval: 체크 간격 (초)
            history_size: 히스토리 크기
        """
        self.check_interval = check_interval
        self.history_size = history_size
        
        self.logger = logging.getLogger(__name__)
        
        # 프로세스 정보
        self.process = psutil.Process(os.getpid())
        
        # 리소스 히스토리
        self.history = deque(maxlen=history_size)
        
        # 임계값
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 70.0,
            'thread_count': 50
        }
        
        # 제어
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 통계
        self.stats = {
            'peak_cpu': 0.0,
            'peak_memory': 0.0,
            'avg_cpu': 0.0,
            'avg_memory': 0.0,
            'warnings': 0
        }
        
        self.logger.info("리소스 모니터 초기화")
    
    def start(self):
        """모니터링 시작"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info("리소스 모니터링 시작")
    
    def stop(self):
        """모니터링 중지"""
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        self.logger.info("리소스 모니터링 중지")
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while not self._stop_event.is_set():
            try:
                snapshot = self._capture_snapshot()
                self.history.append(snapshot)
                
                # 통계 업데이트
                self._update_stats(snapshot)
                
                # 임계값 확인
                self._check_thresholds(snapshot)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"리소스 모니터링 오류: {e}")
                time.sleep(self.check_interval)
    
    def _capture_snapshot(self) -> ResourceSnapshot:
        """리소스 스냅샷 캡처"""
        # CPU 사용률
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        # 메모리 사용률
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()
        
        # 스레드 수
        thread_count = self.process.num_threads()
        
        # I/O 카운터
        try:
            io_counters = self.process.io_counters()
            io_read_mb = io_counters.read_bytes / 1024 / 1024
            io_write_mb = io_counters.write_bytes / 1024 / 1024
        except AttributeError:
            # Windows에서는 지원 안 될 수 있음
            io_read_mb = io_write_mb = 0.0
        
        return ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            thread_count=thread_count,
            io_read_mb=io_read_mb,
            io_write_mb=io_write_mb
        )
    
    def _update_stats(self, snapshot: ResourceSnapshot):
        """통계 업데이트"""
        # 피크 값
        self.stats['peak_cpu'] = max(self.stats['peak_cpu'], snapshot.cpu_percent)
        self.stats['peak_memory'] = max(self.stats['peak_memory'], snapshot.memory_mb)
        
        # 평균 값 (이동 평균)
        if self.history:
            cpu_values = [s.cpu_percent for s in self.history]
            memory_values = [s.memory_mb for s in self.history]
            
            self.stats['avg_cpu'] = sum(cpu_values) / len(cpu_values)
            self.stats['avg_memory'] = sum(memory_values) / len(memory_values)
    
    def _check_thresholds(self, snapshot: ResourceSnapshot):
        """임계값 확인"""
        warnings = []
        
        if snapshot.cpu_percent > self.thresholds['cpu_percent']:
            warnings.append(f"높은 CPU 사용률: {snapshot.cpu_percent:.1f}%")
        
        if snapshot.memory_percent > self.thresholds['memory_percent']:
            warnings.append(f"높은 메모리 사용률: {snapshot.memory_percent:.1f}%")
        
        if snapshot.thread_count > self.thresholds['thread_count']:
            warnings.append(f"많은 스레드 수: {snapshot.thread_count}")
        
        if warnings:
            self.stats['warnings'] += 1
            for warning in warnings:
                self.logger.warning(f"⚠️ 리소스 경고: {warning}")
    
    def get_current_usage(self) -> Dict:
        """현재 리소스 사용량"""
        if not self.history:
            return {}
        
        latest = self.history[-1]
        
        return {
            'timestamp': latest.timestamp.isoformat(),
            'cpu_percent': f"{latest.cpu_percent:.1f}%",
            'memory_mb': f"{latest.memory_mb:.1f}MB",
            'memory_percent': f"{latest.memory_percent:.1f}%",
            'thread_count': latest.thread_count,
            'io_read_mb': f"{latest.io_read_mb:.1f}MB",
            'io_write_mb': f"{latest.io_write_mb:.1f}MB"
        }
    
    def get_summary(self) -> Dict:
        """리소스 사용 요약"""
        return {
            'current': self.get_current_usage(),
            'statistics': {
                'peak_cpu': f"{self.stats['peak_cpu']:.1f}%",
                'peak_memory': f"{self.stats['peak_memory']:.1f}MB",
                'avg_cpu': f"{self.stats['avg_cpu']:.1f}%",
                'avg_memory': f"{self.stats['avg_memory']:.1f}MB",
                'warnings': self.stats['warnings']
            },
            'thresholds': {
                'cpu': f"{self.thresholds['cpu_percent']:.0f}%",
                'memory': f"{self.thresholds['memory_percent']:.0f}%",
                'threads': self.thresholds['thread_count']
            }
        }
    
    def get_history(self, minutes: int = 60) -> List[ResourceSnapshot]:
        """리소스 히스토리 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [s for s in self.history if s.timestamp >= cutoff_time]
    
    def optimize_resources(self):
        """리소스 자동 최적화"""
        import gc
        
        # 가비지 컬렉션
        collected = gc.collect()
        
        self.logger.info(f"리소스 최적화: {collected}개 객체 수집")
        
        return {
            'collected_objects': collected,
            'gc_stats': gc.get_stats()
        }
    
    def set_threshold(self, resource: str, value: float):
        """임계값 설정"""
        if resource in self.thresholds:
            self.thresholds[resource] = value
            self.logger.info(f"임계값 설정: {resource} = {value}")


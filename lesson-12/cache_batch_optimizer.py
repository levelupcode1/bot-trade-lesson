#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 데이터 분석 시스템 캐싱 및 배치 처리 모듈
고성능 캐싱, 배치 처리, 메모리 최적화를 위한 통합 시스템
"""

import pandas as pd
import numpy as np
import pickle
import hashlib
import json
import sqlite3
import threading
import time
import gc
import psutil
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import lru_cache, wraps
import sqlite3
from contextlib import contextmanager
import queue
import heapq

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """캐시 설정 클래스"""
    max_memory_mb: int = 500
    max_disk_mb: int = 2000
    default_ttl: int = 3600  # 1시간
    compression_enabled: bool = True
    cache_dir: str = "cache/"
    enable_persistence: bool = True
    batch_size: int = 1000
    max_concurrent_batches: int = 4

@dataclass
class BatchConfig:
    """배치 처리 설정 클래스"""
    max_batch_size: int = 10000
    min_batch_size: int = 100
    batch_timeout: float = 5.0  # 초
    max_workers: int = None
    enable_parallel: bool = True
    memory_threshold_mb: int = 400

class MemoryCache:
    """메모리 캐시 클래스"""
    
    def __init__(self, max_size_mb: int = 500):
        self.max_size_mb = max_size_mb
        self.cache = {}
        self.access_times = {}
        self.sizes = {}
        self.total_size_bytes = 0
        self.lock = threading.RLock()
        self.process = psutil.Process()
    
    def _get_key_hash(self, key: Any) -> str:
        """키 해시 생성"""
        if isinstance(key, (str, int, float)):
            return str(key)
        return hashlib.md5(str(key).encode()).hexdigest()
    
    def _calculate_size(self, value: Any) -> int:
        """값의 메모리 크기 계산"""
        try:
            return len(pickle.dumps(value))
        except:
            return sys.getsizeof(value)
    
    def _evict_lru(self):
        """LRU 방식으로 캐시 제거"""
        if not self.access_times:
            return
        
        # 가장 오래된 항목 찾기
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_item(oldest_key)
    
    def _remove_item(self, key: str):
        """캐시 항목 제거"""
        if key in self.cache:
            size = self.sizes.get(key, 0)
            del self.cache[key]
            del self.access_times[key]
            del self.sizes[key]
            self.total_size_bytes -= size
    
    def _check_memory_limit(self):
        """메모리 제한 확인 및 정리"""
        current_memory_mb = self.process.memory_info().rss / 1024 / 1024
        
        # 메모리 사용량이 임계값을 초과하면 캐시 정리
        while (self.total_size_bytes > self.max_size_mb * 1024 * 1024 or 
               current_memory_mb > self.max_size_mb * 1.5):
            
            if not self.cache:
                break
            
            self._evict_lru()
            current_memory_mb = self.process.memory_info().rss / 1024 / 1024
    
    def get(self, key: Any) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self.lock:
            key_hash = self._get_key_hash(key)
            
            if key_hash in self.cache:
                # 접근 시간 업데이트
                self.access_times[key_hash] = time.time()
                return self.cache[key_hash]
            
            return None
    
    def set(self, key: Any, value: Any, ttl: int = None):
        """캐시에 값 저장"""
        with self.lock:
            key_hash = self._get_key_hash(key)
            size = self._calculate_size(value)
            
            # 기존 항목 제거
            if key_hash in self.cache:
                self._remove_item(key_hash)
            
            # 새 항목 추가
            self.cache[key_hash] = value
            self.access_times[key_hash] = time.time()
            self.sizes[key_hash] = size
            self.total_size_bytes += size
            
            # 메모리 제한 확인
            self._check_memory_limit()
    
    def clear(self):
        """캐시 전체 정리"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.sizes.clear()
            self.total_size_bytes = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.lock:
            return {
                'items_count': len(self.cache),
                'total_size_mb': self.total_size_bytes / 1024 / 1024,
                'max_size_mb': self.max_size_mb,
                'hit_ratio': 0.0,  # 별도 추적 필요
                'oldest_item': min(self.access_times.values()) if self.access_times else None,
                'newest_item': max(self.access_times.values()) if self.access_times else None
            }

class DiskCache:
    """디스크 캐시 클래스"""
    
    def __init__(self, cache_dir: str = "cache/", max_size_mb: int = 2000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
        self.lock = threading.RLock()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """메타데이터 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'entries': {}, 'total_size': 0}
    
    def _save_metadata(self):
        """메타데이터 저장"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"메타데이터 저장 오류: {e}")
    
    def _get_key_path(self, key: str) -> Path:
        """키에 해당하는 파일 경로 반환"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _cleanup_expired(self):
        """만료된 캐시 정리"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.metadata['entries'].items():
            if entry['expires_at'] < current_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str):
        """캐시 항목 제거"""
        if key in self.metadata['entries']:
            entry = self.metadata['entries'][key]
            file_path = self._get_key_path(key)
            
            if file_path.exists():
                file_path.unlink()
            
            self.metadata['total_size'] -= entry['size']
            del self.metadata['entries'][key]
    
    def _evict_lru(self):
        """LRU 방식으로 캐시 제거"""
        if not self.metadata['entries']:
            return
        
        # 가장 오래된 항목 찾기
        oldest_key = min(
            self.metadata['entries'].keys(),
            key=lambda k: self.metadata['entries'][k]['last_accessed']
        )
        self._remove_entry(oldest_key)
    
    def _check_size_limit(self):
        """크기 제한 확인"""
        while (self.metadata['total_size'] > self.max_size_mb * 1024 * 1024 and 
               self.metadata['entries']):
            self._evict_lru()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self.lock:
            if key not in self.metadata['entries']:
                return None
            
            entry = self.metadata['entries'][key]
            
            # 만료 확인
            if entry['expires_at'] < time.time():
                self._remove_entry(key)
                return None
            
            # 파일에서 데이터 로드
            file_path = self._get_key_path(key)
            if not file_path.exists():
                self._remove_entry(key)
                return None
            
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                # 접근 시간 업데이트
                self.metadata['entries'][key]['last_accessed'] = time.time()
                self._save_metadata()
                
                return data
            except Exception as e:
                logger.error(f"캐시 파일 로드 오류: {e}")
                self._remove_entry(key)
                return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장"""
        with self.lock:
            # 만료된 항목 정리
            self._cleanup_expired()
            
            # 기존 항목 제거
            if key in self.metadata['entries']:
                self._remove_entry(key)
            
            # 파일에 데이터 저장
            file_path = self._get_key_path(key)
            try:
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)
                
                file_size = file_path.stat().st_size
                
                # 메타데이터 업데이트
                self.metadata['entries'][key] = {
                    'created_at': time.time(),
                    'expires_at': time.time() + ttl,
                    'last_accessed': time.time(),
                    'size': file_size
                }
                self.metadata['total_size'] += file_size
                
                # 크기 제한 확인
                self._check_size_limit()
                
                # 메타데이터 저장
                self._save_metadata()
                
            except Exception as e:
                logger.error(f"캐시 파일 저장 오류: {e}")
                if file_path.exists():
                    file_path.unlink()
    
    def clear(self):
        """캐시 전체 정리"""
        with self.lock:
            for key in list(self.metadata['entries'].keys()):
                self._remove_entry(key)
            self._save_metadata()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.lock:
            self._cleanup_expired()
            return {
                'items_count': len(self.metadata['entries']),
                'total_size_mb': self.metadata['total_size'] / 1024 / 1024,
                'max_size_mb': self.max_size_mb,
                'cache_dir': str(self.cache_dir)
            }

class OptimizedCacheManager:
    """최적화된 캐시 관리자"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = MemoryCache(config.max_memory_mb)
        self.disk_cache = DiskCache(config.cache_dir, config.max_disk_mb) if config.enable_persistence else None
        self.hit_counts = {'memory': 0, 'disk': 0, 'miss': 0}
        self.lock = threading.RLock()
    
    def get(self, key: Any) -> Optional[Any]:
        """캐시에서 값 조회"""
        key_str = str(key)
        
        # 메모리 캐시 확인
        value = self.memory_cache.get(key)
        if value is not None:
            with self.lock:
                self.hit_counts['memory'] += 1
            return value
        
        # 디스크 캐시 확인
        if self.disk_cache:
            value = self.disk_cache.get(key_str)
            if value is not None:
                # 메모리 캐시에도 저장
                self.memory_cache.set(key, value, self.config.default_ttl)
                with self.lock:
                    self.hit_counts['disk'] += 1
                return value
        
        # 캐시 미스
        with self.lock:
            self.hit_counts['miss'] += 1
        return None
    
    def set(self, key: Any, value: Any, ttl: int = None):
        """캐시에 값 저장"""
        if ttl is None:
            ttl = self.config.default_ttl
        
        # 메모리 캐시에 저장
        self.memory_cache.set(key, value, ttl)
        
        # 디스크 캐시에도 저장 (큰 데이터만)
        if self.disk_cache and self._should_store_on_disk(value):
            self.disk_cache.set(str(key), value, ttl)
    
    def _should_store_on_disk(self, value: Any) -> bool:
        """디스크에 저장할지 결정"""
        try:
            size = len(pickle.dumps(value))
            return size > 1024 * 1024  # 1MB 이상
        except:
            return False
    
    def clear(self):
        """모든 캐시 정리"""
        self.memory_cache.clear()
        if self.disk_cache:
            self.disk_cache.clear()
        
        with self.lock:
            self.hit_counts = {'memory': 0, 'disk': 0, 'miss': 0}
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats() if self.disk_cache else {}
        
        total_hits = sum(self.hit_counts.values())
        hit_ratio = (self.hit_counts['memory'] + self.hit_counts['disk']) / total_hits if total_hits > 0 else 0
        
        return {
            'memory_cache': memory_stats,
            'disk_cache': disk_stats,
            'hit_counts': self.hit_counts.copy(),
            'hit_ratio': hit_ratio,
            'total_requests': total_hits
        }

class BatchProcessor:
    """배치 처리 클래스"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.batch_queue = queue.Queue()
        self.results = {}
        self.batch_lock = threading.Lock()
        self.executor = None
        self.running = False
        self.max_workers = config.max_workers or min(mp.cpu_count(), 8)
    
    def start(self):
        """배치 처리 시작"""
        if self.running:
            return
        
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._start_batch_processor()
    
    def stop(self):
        """배치 처리 중지"""
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=True)
    
    def _start_batch_processor(self):
        """배치 처리 스레드 시작"""
        def process_batches():
            while self.running:
                try:
                    batch_data = self.batch_queue.get(timeout=1.0)
                    if batch_data:
                        self._process_single_batch(batch_data)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"배치 처리 오류: {e}")
        
        thread = threading.Thread(target=process_batches, daemon=True)
        thread.start()
    
    def _process_single_batch(self, batch_data: Dict[str, Any]):
        """단일 배치 처리"""
        try:
            batch_id = batch_data['batch_id']
            func = batch_data['func']
            items = batch_data['items']
            
            # 병렬 처리
            if self.config.enable_parallel and len(items) > self.config.min_batch_size:
                with self.batch_lock:
                    future = self.executor.submit(self._process_parallel, func, items)
                    result = future.result(timeout=30)
            else:
                result = self._process_sequential(func, items)
            
            # 결과 저장
            self.results[batch_id] = result
            
        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")
            self.results[batch_data['batch_id']] = {'error': str(e)}
    
    def _process_parallel(self, func: Callable, items: List[Any]) -> List[Any]:
        """병렬 배치 처리"""
        chunk_size = max(1, len(items) // self.max_workers)
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._process_chunk, func, chunk) for chunk in chunks]
            results = []
            
            for future in futures:
                try:
                    result = future.result(timeout=60)
                    results.extend(result)
                except Exception as e:
                    logger.error(f"병렬 처리 오류: {e}")
                    results.extend([None] * len(chunk))
            
            return results
    
    def _process_chunk(self, func: Callable, chunk: List[Any]) -> List[Any]:
        """청크 처리"""
        results = []
        for item in chunk:
            try:
                result = func(item)
                results.append(result)
            except Exception as e:
                logger.error(f"청크 항목 처리 오류: {e}")
                results.append(None)
        return results
    
    def _process_sequential(self, func: Callable, items: List[Any]) -> List[Any]:
        """순차 배치 처리"""
        results = []
        for item in items:
            try:
                result = func(item)
                results.append(result)
            except Exception as e:
                logger.error(f"순차 처리 오류: {e}")
                results.append(None)
        return results
    
    def submit_batch(self, func: Callable, items: List[Any], batch_id: str = None) -> str:
        """배치 제출"""
        if not batch_id:
            batch_id = f"batch_{int(time.time() * 1000)}"
        
        batch_data = {
            'batch_id': batch_id,
            'func': func,
            'items': items,
            'submitted_at': time.time()
        }
        
        self.batch_queue.put(batch_data)
        return batch_id
    
    def get_result(self, batch_id: str, timeout: float = 30.0) -> Any:
        """배치 결과 조회"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if batch_id in self.results:
                result = self.results.pop(batch_id)  # 결과 조회 후 제거
                return result
            time.sleep(0.1)
        
        raise TimeoutError(f"배치 {batch_id} 결과 타임아웃")

class OptimizedCacheBatchSystem:
    """최적화된 캐싱 및 배치 처리 통합 시스템"""
    
    def __init__(self, cache_config: CacheConfig = None, batch_config: BatchConfig = None):
        self.cache_config = cache_config or CacheConfig()
        self.batch_config = batch_config or BatchConfig()
        
        self.cache_manager = OptimizedCacheManager(self.cache_config)
        self.batch_processor = BatchProcessor(self.batch_config)
        
        # 성능 모니터링
        self.performance_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_operations': 0,
            'total_processing_time': 0.0
        }
        
        logger.info("최적화된 캐싱 및 배치 처리 시스템 초기화 완료")
    
    def start(self):
        """시스템 시작"""
        self.batch_processor.start()
        logger.info("캐싱 및 배치 처리 시스템 시작")
    
    def stop(self):
        """시스템 중지"""
        self.batch_processor.stop()
        logger.info("캐싱 및 배치 처리 시스템 중지")
    
    def cached_function(self, ttl: int = None, batch_size: int = None):
        """캐시된 함수 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 캐시 키 생성
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # 캐시에서 조회
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    self.performance_stats['cache_hits'] += 1
                    return cached_result
                
                # 함수 실행
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 캐시에 저장
                self.cache_manager.set(cache_key, result, ttl or self.cache_config.default_ttl)
                
                # 성능 통계 업데이트
                self.performance_stats['cache_misses'] += 1
                self.performance_stats['total_processing_time'] += execution_time
                
                return result
            
            return wrapper
        return decorator
    
    def batch_processed_function(self, batch_size: int = None):
        """배치 처리된 함수 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(items: List[Any]):
                if not items:
                    return []
                
                batch_size_actual = batch_size or self.batch_config.max_batch_size
                
                # 작은 배치는 직접 처리
                if len(items) <= batch_size_actual:
                    start_time = time.time()
                    results = [func(item) for item in items]
                    execution_time = time.time() - start_time
                    
                    self.performance_stats['batch_operations'] += 1
                    self.performance_stats['total_processing_time'] += execution_time
                    
                    return results
                
                # 큰 배치는 배치 처리
                batch_id = self.batch_processor.submit_batch(func, items)
                result = self.batch_processor.get_result(batch_id)
                
                self.performance_stats['batch_operations'] += 1
                return result
            
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """캐시 키 생성"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        cache_stats = self.cache_manager.get_stats()
        
        return {
            'cache_performance': cache_stats,
            'processing_stats': self.performance_stats.copy(),
            'system_status': {
                'cache_enabled': True,
                'batch_processing_enabled': self.batch_processor.running,
                'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024
            }
        }
    
    def cleanup_resources(self):
        """리소스 정리"""
        self.stop()
        self.cache_manager.clear()
        gc.collect()
        logger.info("캐싱 및 배치 처리 시스템 리소스 정리 완료")

# 사용 예시
if __name__ == "__main__":
    import time
    import sys
    
    # 시스템 설정
    cache_config = CacheConfig(
        max_memory_mb=200,
        max_disk_mb=1000,
        cache_dir="optimized_cache/",
        default_ttl=1800
    )
    
    batch_config = BatchConfig(
        max_batch_size=1000,
        min_batch_size=10,
        max_workers=4
    )
    
    # 시스템 초기화
    system = OptimizedCacheBatchSystem(cache_config, batch_config)
    system.start()
    
    # 테스트 함수들
    @system.cached_function(ttl=300)
    def expensive_calculation(n: int) -> int:
        """비용이 큰 계산"""
        time.sleep(0.1)  # 시뮬레이션
        return sum(i * i for i in range(n))
    
    @system.batch_processed_function(batch_size=100)
    def process_item(item: int) -> int:
        """항목 처리"""
        time.sleep(0.01)  # 시뮬레이션
        return item * 2
    
    # 테스트 실행
    print("=== 캐싱 및 배치 처리 시스템 테스트 ===")
    
    # 1. 캐싱 테스트
    print("\n1. 캐싱 테스트")
    start_time = time.time()
    
    # 첫 번째 실행 (캐시 미스)
    result1 = expensive_calculation(1000)
    first_run_time = time.time() - start_time
    
    # 두 번째 실행 (캐시 히트)
    start_time = time.time()
    result2 = expensive_calculation(1000)
    second_run_time = time.time() - start_time
    
    print(f"첫 번째 실행: {first_run_time:.3f}초, 결과: {result1}")
    print(f"두 번째 실행: {second_run_time:.3f}초, 결과: {result2}")
    print(f"속도 향상: {first_run_time / second_run_time:.1f}배")
    
    # 2. 배치 처리 테스트
    print("\n2. 배치 처리 테스트")
    test_items = list(range(500))
    
    start_time = time.time()
    batch_results = process_item(test_items)
    batch_time = time.time() - start_time
    
    print(f"배치 처리: {len(batch_results)}개 항목, {batch_time:.3f}초")
    print(f"평균 처리 시간: {batch_time / len(batch_results) * 1000:.2f}ms/항목")
    
    # 3. 성능 통계
    print("\n3. 성능 통계")
    stats = system.get_performance_stats()
    
    print("캐시 통계:")
    cache_stats = stats['cache_performance']
    print(f"- 메모리 캐시: {cache_stats['memory_cache']['items_count']}개 항목")
    print(f"- 디스크 캐시: {cache_stats['disk_cache']['items_count']}개 항목")
    print(f"- 캐시 적중률: {cache_stats['hit_ratio']:.1%}")
    
    print("\n처리 통계:")
    proc_stats = stats['processing_stats']
    print(f"- 캐시 히트: {proc_stats['cache_hits']}회")
    print(f"- 캐시 미스: {proc_stats['cache_misses']}회")
    print(f"- 배치 작업: {proc_stats['batch_operations']}회")
    print(f"- 총 처리 시간: {proc_stats['total_processing_time']:.3f}초")
    
    # 4. 시스템 상태
    print("\n4. 시스템 상태")
    system_status = stats['system_status']
    print(f"- 캐시 활성화: {system_status['cache_enabled']}")
    print(f"- 배치 처리 활성화: {system_status['batch_processing_enabled']}")
    print(f"- 메모리 사용량: {system_status['memory_usage_mb']:.1f}MB")
    
    # 리소스 정리
    system.cleanup_resources()
    print("\n테스트 완료!")




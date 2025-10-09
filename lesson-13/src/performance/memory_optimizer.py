#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메모리 사용량 최적화

개선사항:
1. deque로 메모리 누수 방지
2. NumPy dtype 최적화
3. 객체 풀 패턴
4. 명시적 메모리 관리
"""

import numpy as np
import pandas as pd
from collections import deque
from typing import Dict, List, Any, Optional
import logging
import gc
import sys
from dataclasses import dataclass
import weakref


class ObjectPool:
    """객체 풀 패턴으로 메모리 할당 최소화"""
    
    def __init__(self, factory, max_size: int = 100):
        """
        Args:
            factory: 객체 생성 함수
            max_size: 풀 최대 크기
        """
        self.factory = factory
        self.max_size = max_size
        self.pool = deque(maxlen=max_size)
        self.in_use = set()
    
    def acquire(self):
        """객체 획득"""
        if self.pool:
            obj = self.pool.popleft()
        else:
            obj = self.factory()
        
        self.in_use.add(id(obj))
        return obj
    
    def release(self, obj):
        """객체 반환"""
        if id(obj) in self.in_use:
            self.in_use.remove(id(obj))
            
            if len(self.pool) < self.max_size:
                self.pool.append(obj)


class MemoryOptimizer:
    """메모리 최적화 관리자"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("메모리 최적화기 초기화")
    
    @staticmethod
    def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame dtype 최적화
        
        기존: float64 - 8 bytes
        개선: float32 - 4 bytes (50% 메모리 절감)
        """
        optimized = df.copy()
        
        for col in optimized.columns:
            col_type = optimized[col].dtype
            
            if col_type == 'float64':
                # float32로 변환 (정밀도 충분)
                optimized[col] = optimized[col].astype('float32')
            
            elif col_type == 'int64':
                # 더 작은 int 타입 사용
                col_min = optimized[col].min()
                col_max = optimized[col].max()
                
                if col_min >= 0:
                    if col_max < 255:
                        optimized[col] = optimized[col].astype('uint8')
                    elif col_max < 65535:
                        optimized[col] = optimized[col].astype('uint16')
                    elif col_max < 4294967295:
                        optimized[col] = optimized[col].astype('uint32')
                else:
                    if col_min > -128 and col_max < 127:
                        optimized[col] = optimized[col].astype('int8')
                    elif col_min > -32768 and col_max < 32767:
                        optimized[col] = optimized[col].astype('int16')
                    elif col_min > -2147483648 and col_max < 2147483647:
                        optimized[col] = optimized[col].astype('int32')
        
        # 메모리 사용량 출력
        before = df.memory_usage(deep=True).sum() / 1024 / 1024
        after = optimized.memory_usage(deep=True).sum() / 1024 / 1024
        reduction = (before - after) / before * 100
        
        logging.info(f"메모리 최적화: {before:.2f}MB → {after:.2f}MB ({reduction:.1f}% 감소)")
        
        return optimized
    
    @staticmethod
    def create_efficient_buffer(maxsize: int = 10000) -> deque:
        """효율적인 링 버퍼 생성
        
        기존: List (무한 증가) - 메모리 누수
        개선: deque(maxlen) - 메모리 고정
        """
        return deque(maxlen=maxsize)
    
    @staticmethod
    def numpy_memory_pool(shape: Tuple[int, ...], 
                         dtype: np.dtype = np.float32,
                         pool_size: int = 10) -> 'NumPyPool':
        """NumPy 배열 풀
        
        배열 재사용으로 할당 오버헤드 제거
        """
        return NumPyPool(shape, dtype, pool_size)
    
    @staticmethod
    def analyze_memory_usage(obj: Any) -> Dict:
        """객체 메모리 사용량 분석"""
        return {
            'total_size': sys.getsizeof(obj),
            'type': type(obj).__name__,
            'refcount': sys.getrefcount(obj)
        }
    
    @staticmethod
    def garbage_collect_aggressive():
        """공격적 가비지 컬렉션
        
        주기적으로 실행하여 메모리 정리
        """
        # 모든 세대 수집
        collected = gc.collect(2)
        
        # 통계
        stats = gc.get_stats()
        
        return {
            'collected_objects': collected,
            'gc_stats': stats
        }
    
    @staticmethod
    def optimize_data_structure(data: List[Dict]) -> np.ndarray:
        """데이터 구조 최적화
        
        기존: List[Dict] - 비효율적
        개선: NumPy structured array - 3배 메모리 절감
        """
        if not data:
            return np.array([])
        
        # 구조화 배열 dtype 정의
        first_item = data[0]
        dtype = []
        
        for key, value in first_item.items():
            if isinstance(value, float):
                dtype.append((key, 'float32'))
            elif isinstance(value, int):
                dtype.append((key, 'int32'))
            elif isinstance(value, str):
                dtype.append((key, 'U20'))  # 최대 20자
        
        # 구조화 배열 생성
        structured_array = np.zeros(len(data), dtype=dtype)
        
        for i, item in enumerate(data):
            for key in item:
                structured_array[i][key] = item[key]
        
        return structured_array


class NumPyPool:
    """NumPy 배열 풀"""
    
    def __init__(self, shape, dtype, pool_size):
        self.shape = shape
        self.dtype = dtype
        self.pool = [np.zeros(shape, dtype=dtype) for _ in range(pool_size)]
        self.available = deque(range(pool_size))
        self.in_use = {}
    
    def acquire(self) -> np.ndarray:
        """배열 획득"""
        if self.available:
            idx = self.available.popleft()
            arr = self.pool[idx]
            arr.fill(0)  # 초기화
            self.in_use[id(arr)] = idx
            return arr
        else:
            # 풀 고갈 - 새로 생성
            return np.zeros(self.shape, dtype=self.dtype)
    
    def release(self, arr: np.ndarray):
        """배열 반환"""
        arr_id = id(arr)
        if arr_id in self.in_use:
            idx = self.in_use.pop(arr_id)
            self.available.append(idx)


class MemoryMonitor:
    """메모리 모니터링"""
    
    def __init__(self):
        self.snapshots = []
    
    def snapshot(self, label: str = ""):
        """메모리 스냅샷"""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        snapshot = {
            'label': label,
            'timestamp': pd.Timestamp.now(),
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def compare(self, label1: str, label2: str) -> Dict:
        """두 스냅샷 비교"""
        snap1 = next((s for s in self.snapshots if s['label'] == label1), None)
        snap2 = next((s for s in self.snapshots if s['label'] == label2), None)
        
        if not snap1 or not snap2:
            return {}
        
        diff_mb = snap2['rss_mb'] - snap1['rss_mb']
        diff_pct = (diff_mb / snap1['rss_mb']) * 100
        
        return {
            'label1': label1,
            'label2': label2,
            'diff_mb': diff_mb,
            'diff_percent': diff_pct,
            'is_leak': diff_mb > 10  # 10MB 이상 증가 시 누수 의심
        }
    
    def generate_report(self) -> str:
        """메모리 사용 리포트"""
        if not self.snapshots:
            return "No snapshots"
        
        report = "메모리 사용 리포트\n"
        report += "=" * 60 + "\n"
        
        for snap in self.snapshots:
            report += f"{snap['label']:20s}: {snap['rss_mb']:8.2f}MB ({snap['percent']:5.2f}%)\n"
        
        return report


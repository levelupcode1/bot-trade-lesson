/**
 * useRealtimeData Hook
 * 실시간 거래 데이터를 관리하는 커스텀 훅
 */

import { useState, useEffect, useCallback } from 'react';

export const useRealtimeData = () => {
  const [positions, setPositions] = useState([]);
  const [activities, setActivities] = useState([]);
  const [systemStatus, setSystemStatus] = useState({
    trading: 'running',
    mcp: 'running',
    websocket: 'running',
    notification: 'running',
    cpu: 15,
    memory: 32,
    apiLatency: 85
  });
  const [stats, setStats] = useState({
    totalProfit: 15.8,
    dailyProfit: 250000,
    totalTrades: 142,
    winRate: 68.5,
    avgProfit: 2.3,
    avgLoss: -1.2,
    sharpeRatio: 1.85,
    maxDrawdown: -8.2
  });

  // 실시간 포지션 업데이트 시뮬레이션
  useEffect(() => {
    const initialPositions = [
      {
        id: 1,
        coin: 'BTC',
        amount: 0.015,
        avgPrice: 85000000,
        currentPrice: 85150000,
        value: 1277250,
        pnl: 0.18,
        strategy: '변동성 돌파',
        entryTime: '14:25:30'
      },
      {
        id: 2,
        coin: 'ETH',
        amount: 0.5,
        avgPrice: 5200000,
        currentPrice: 5150000,
        value: 2575000,
        pnl: -0.96,
        strategy: 'MA 크로스',
        entryTime: '13:10:15'
      },
      {
        id: 3,
        coin: 'XRP',
        amount: 1000,
        avgPrice: 850,
        currentPrice: 875,
        value: 875000,
        pnl: 2.94,
        strategy: 'RSI 전략',
        entryTime: '12:05:42'
      }
    ];
    setPositions(initialPositions);

    // 5초마다 가격 업데이트
    const interval = setInterval(() => {
      setPositions(prev => prev.map(pos => {
        const priceChange = (Math.random() - 0.5) * pos.currentPrice * 0.001;
        const newPrice = pos.currentPrice + priceChange;
        const newValue = pos.amount * newPrice;
        const newPnl = ((newPrice - pos.avgPrice) / pos.avgPrice) * 100;

        return {
          ...pos,
          currentPrice: Math.round(newPrice),
          value: Math.round(newValue),
          pnl: Number(newPnl.toFixed(2))
        };
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // 활동 로그 업데이트
  useEffect(() => {
    const initialActivities = [
      {
        id: 1,
        type: 'buy',
        title: 'BTC 매수 체결',
        description: '0.015 BTC @ 85,150,000 KRW',
        timestamp: Date.now() - 120000
      },
      {
        id: 2,
        type: 'signal',
        title: 'MA 크로스 매수 신호',
        description: 'ETH에서 골든크로스 감지',
        timestamp: Date.now() - 300000
      },
      {
        id: 3,
        type: 'sell',
        title: 'SOL 매도 체결',
        description: '5 SOL @ 145,000 KRW (+3.2%)',
        timestamp: Date.now() - 600000
      },
      {
        id: 4,
        type: 'system',
        title: '전략 실행 시작',
        description: '변동성 돌파 전략 활성화',
        timestamp: Date.now() - 900000
      }
    ];
    setActivities(initialActivities);
  }, []);

  // 시스템 상태 업데이트
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        cpu: Math.min(100, Math.max(10, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.min(100, Math.max(20, prev.memory + (Math.random() - 0.5) * 5)),
        apiLatency: Math.min(500, Math.max(50, prev.apiLatency + (Math.random() - 0.5) * 50))
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // 새 활동 추가
  const addActivity = useCallback((activity) => {
    setActivities(prev => [
      {
        ...activity,
        id: Date.now(),
        timestamp: Date.now()
      },
      ...prev
    ].slice(0, 20)); // 최근 20개만 유지
  }, []);

  return {
    positions,
    activities,
    systemStatus,
    stats,
    addActivity
  };
};

// 시간 포맷 헬퍼
export const formatTimeAgo = (timestamp) => {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  
  if (seconds < 60) return `${seconds}초 전`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}분 전`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}시간 전`;
  return `${Math.floor(seconds / 86400)}일 전`;
};


/**
 * NotificationCenter Component
 * 실시간 알림 및 메시지 센터
 */

import React, { useState } from 'react';
import { formatTimeAgo } from '../../hooks/useRealtimeData';
import './NotificationCenter.css';

const NotificationCenter = () => {
  const [notifications] = useState([
    {
      id: 1,
      type: 'success',
      title: '✅ 매수 체결 완료',
      message: 'BTC 0.015 @ 85,150,000 KRW\n변동성 돌파 전략',
      timestamp: Date.now() - 120000,
      read: false
    },
    {
      id: 2,
      type: 'warning',
      title: '⚠️ 손절가 접근 경고',
      message: 'ETH가 손절가(-5%)에 근접했습니다\n현재: -4.2%',
      timestamp: Date.now() - 300000,
      read: false
    },
    {
      id: 3,
      type: 'info',
      title: 'ℹ️ 전략 실행 중',
      message: 'MA 교차 전략이 매수 신호를 감지했습니다',
      timestamp: Date.now() - 600000,
      read: true
    },
    {
      id: 4,
      type: 'error',
      title: '❌ API 연결 오류',
      message: '업비트 API 연결에 일시적인 문제가 발생했습니다\n자동으로 재연결 시도 중...',
      timestamp: Date.now() - 900000,
      read: true
    },
    {
      id: 5,
      type: 'success',
      title: '✅ 매도 체결 완료',
      message: 'SOL 5 @ 145,000 KRW (+3.2%)\nRSI 전략',
      timestamp: Date.now() - 1200000,
      read: true
    }
  ]);

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="notification-center">
      <div className="notification-header">
        <h3 className="section-title">🔔 알림</h3>
        {unreadCount > 0 && (
          <span className="unread-badge">{unreadCount}</span>
        )}
      </div>

      <div className="notification-list">
        {notifications.map(notification => (
          <div 
            key={notification.id} 
            className={`notification-item ${notification.type} ${notification.read ? 'read' : 'unread'}`}
          >
            <div className="notification-content">
              <div className="notification-title">{notification.title}</div>
              <div className="notification-message">
                {notification.message.split('\n').map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
              <div className="notification-time">
                {formatTimeAgo(notification.timestamp)}
              </div>
            </div>
            {!notification.read && <div className="notification-dot" />}
          </div>
        ))}
      </div>

      <button className="clear-all-btn">
        모두 지우기
      </button>
    </div>
  );
};

export default NotificationCenter;


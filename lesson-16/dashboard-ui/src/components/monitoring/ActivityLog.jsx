/**
 * ActivityLog Component
 * 거래 활동 로그 표시
 */

import React from 'react';
import { formatTimeAgo } from '../../hooks/useRealtimeData';
import './ActivityLog.css';

const ActivityLog = ({ activities }) => {
  const getActivityIcon = (type) => {
    switch (type) {
      case 'buy':
        return '💰';
      case 'sell':
        return '💸';
      case 'signal':
        return '📊';
      case 'system':
        return '⚙️';
      default:
        return '📋';
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'buy':
        return 'buy';
      case 'sell':
        return 'sell';
      case 'signal':
        return 'signal';
      case 'system':
        return 'system';
      default:
        return '';
    }
  };

  return (
    <div className="activity-log-card">
      <div className="card-header">
        <h3 className="section-title">📋 거래 활동 로그</h3>
        <button className="refresh-btn" title="새로고침">
          🔄
        </button>
      </div>
      
      <div className="activity-list">
        {activities.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📭</span>
            <p>활동 기록이 없습니다</p>
          </div>
        ) : (
          activities.map(activity => (
            <div key={activity.id} className={`activity-item ${getActivityColor(activity.type)}`}>
              <div className="activity-icon">
                {getActivityIcon(activity.type)}
              </div>
              
              <div className="activity-content">
                <div className="activity-title">{activity.title}</div>
                <div className="activity-description">{activity.description}</div>
              </div>
              
              <div className="activity-time">
                {formatTimeAgo(activity.timestamp)}
              </div>
            </div>
          ))
        )}
      </div>
      
      <button className="view-all-btn">
        전체 로그 보기 →
      </button>
    </div>
  );
};

export default ActivityLog;


/**
 * StatsCard Component
 * 통계 정보를 표시하는 카드 컴포넌트
 */

import React from 'react';
import './StatsCard.css';

const StatsCard = ({ title, value, trend, icon, color = 'primary' }) => {
  const getColorClass = () => {
    switch (color) {
      case 'success':
        return 'text-success';
      case 'danger':
        return 'text-danger';
      case 'warning':
        return 'text-warning';
      case 'primary':
      default:
        return 'text-primary';
    }
  };

  return (
    <div className="stats-card">
      <div className="stats-card-header">
        <span className="stats-card-title">{title}</span>
        {icon && <span className={`stats-card-icon ${getColorClass()}`}>{icon}</span>}
      </div>
      <div className={`stats-card-value ${getColorClass()}`}>
        {value}
      </div>
      {trend && (
        <div className={`stats-card-trend ${trend === 'up' ? 'text-success' : 'text-danger'}`}>
          {trend === 'up' ? '↗' : '↘'} {trend === 'up' ? '상승' : '하락'}
        </div>
      )}
    </div>
  );
};

export default StatsCard;


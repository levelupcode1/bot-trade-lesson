/**
 * SystemStatus Component
 * 시스템 상태 및 성능 지표 표시
 */

import React from 'react';
import './SystemStatus.css';

const SystemStatus = ({ status }) => {
  return (
    <div className="system-status-card">
      <h3 className="section-title">⚙️ 시스템 상태</h3>
      
      <div className="status-grid">
        <StatusIndicator 
          label="거래 시스템"
          status={status.trading}
          icon="🔄"
        />
        <StatusIndicator 
          label="MCP 서버"
          status={status.mcp}
          icon="🔌"
        />
        <StatusIndicator 
          label="WebSocket"
          status={status.websocket}
          icon="📡"
        />
        <StatusIndicator 
          label="알림 시스템"
          status={status.notification}
          icon="🔔"
        />
      </div>
      
      <div className="system-metrics">
        <div className="metric">
          <div className="metric-header">
            <span className="metric-label">CPU 사용률</span>
            <span className="metric-value">{Math.round(status.cpu)}%</span>
          </div>
          <div className="metric-bar">
            <div 
              className={`metric-fill ${status.cpu > 80 ? 'danger' : status.cpu > 60 ? 'warning' : 'success'}`}
              style={{ width: `${status.cpu}%` }} 
            />
          </div>
        </div>
        
        <div className="metric">
          <div className="metric-header">
            <span className="metric-label">메모리 사용</span>
            <span className="metric-value">{Math.round(status.memory)}%</span>
          </div>
          <div className="metric-bar">
            <div 
              className={`metric-fill ${status.memory > 80 ? 'danger' : status.memory > 60 ? 'warning' : 'success'}`}
              style={{ width: `${status.memory}%` }} 
            />
          </div>
        </div>
        
        <div className="metric">
          <div className="metric-header">
            <span className="metric-label">API 응답시간</span>
            <span className="metric-value">{Math.round(status.apiLatency)}ms</span>
          </div>
          <div className="metric-bar">
            <div 
              className={`metric-fill ${status.apiLatency > 200 ? 'danger' : status.apiLatency > 100 ? 'warning' : 'success'}`}
              style={{ width: `${Math.min((status.apiLatency / 500) * 100, 100)}%` }} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const StatusIndicator = ({ label, status, icon }) => {
  const getStatusText = (status) => {
    switch (status) {
      case 'running':
        return '실행 중';
      case 'error':
        return '오류';
      case 'stopped':
        return '중지';
      default:
        return '알 수 없음';
    }
  };

  return (
    <div className="status-indicator">
      <span className="status-icon">{icon}</span>
      <div className="status-info">
        <span className="status-label">{label}</span>
        <span className={`status-value ${status}`}>
          {getStatusText(status)}
        </span>
      </div>
      <div className={`status-dot ${status}`} />
    </div>
  );
};

export default SystemStatus;


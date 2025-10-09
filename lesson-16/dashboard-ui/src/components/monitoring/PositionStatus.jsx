/**
 * PositionStatus Component
 * 현재 보유 포지션 상태 표시
 */

import React from 'react';
import './PositionStatus.css';

const PositionStatus = ({ positions }) => {
  const totalValue = positions.reduce((sum, pos) => sum + pos.value, 0);
  const totalPnL = positions.reduce((sum, pos) => {
    const pnlValue = (pos.value * pos.pnl) / 100;
    return sum + pnlValue;
  }, 0);
  const totalPnLPercent = ((totalPnL / (totalValue - totalPnL)) * 100).toFixed(2);

  return (
    <div className="position-status-card">
      <h3 className="section-title">📈 현재 포지션 상태</h3>
      
      <div className="position-summary">
        <div className="summary-item">
          <span className="label">총 포지션</span>
          <span className="value">{positions.length}개</span>
        </div>
        <div className="summary-item">
          <span className="label">평가금액</span>
          <span className="value">{totalValue.toLocaleString()} KRW</span>
        </div>
        <div className="summary-item">
          <span className="label">평가손익</span>
          <span className={`value ${totalPnL >= 0 ? 'profit' : 'loss'}`}>
            {totalPnL >= 0 ? '+' : ''}{totalPnL.toLocaleString()} KRW ({totalPnLPercent}%)
          </span>
        </div>
      </div>

      <div className="position-list">
        {positions.map(position => (
          <div key={position.id} className="position-item">
            <div className="position-header">
              <div className="coin-info">
                <span className="coin-name">{position.coin}</span>
                <span className="strategy-tag">{position.strategy}</span>
              </div>
              <span className={`pnl ${position.pnl >= 0 ? 'profit' : 'loss'}`}>
                {position.pnl >= 0 ? '+' : ''}{position.pnl.toFixed(2)}%
              </span>
            </div>
            
            <div className="position-details">
              <div className="detail-row">
                <span>수량</span>
                <span>{position.amount}</span>
              </div>
              <div className="detail-row">
                <span>평단가</span>
                <span>{position.avgPrice.toLocaleString()} KRW</span>
              </div>
              <div className="detail-row">
                <span>현재가</span>
                <span className="highlight">{position.currentPrice.toLocaleString()} KRW</span>
              </div>
              <div className="detail-row">
                <span>평가금액</span>
                <span className="highlight">{position.value.toLocaleString()} KRW</span>
              </div>
            </div>

            <div className="position-footer">
              <span className="time">진입: {position.entryTime}</span>
              <button className="close-btn">청산</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PositionStatus;


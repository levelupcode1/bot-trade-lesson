/**
 * NavigationBar Component
 * Figma 디자인의 네비게이션 바
 */

import React, { useState } from 'react';
import './NavigationBar.css';

const NavigationBar = ({ onQuickTrade, onNotificationClick }) => {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [notificationCount, setNotificationCount] = useState(3);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'strategies', label: 'Strategies' },
    { id: 'settings', label: 'Settings' }
  ];

  return (
    <nav className="navigation-bar">
      <div className="nav-left">
        <div className="nav-logo">
          🤖 <span className="nav-logo-text">CryptoAutoTrader</span>
        </div>
      </div>

      <div className="nav-center">
        <div className="nav-menu">
          {menuItems.map(item => (
            <button
              key={item.id}
              className={`nav-menu-item ${activeMenu === item.id ? 'active' : ''}`}
              onClick={() => setActiveMenu(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="nav-right">
        <button className="quick-trade-btn" onClick={onQuickTrade}>
          <span>⚡</span>
          <span>빠른거래</span>
        </button>

        <button className="notification-btn" onClick={onNotificationClick}>
          <span>🔔</span>
          {notificationCount > 0 && (
            <span className="notification-badge">{notificationCount}</span>
          )}
        </button>
      </div>
    </nav>
  );
};

export default NavigationBar;


/**
 * DashboardLayout Component
 * 메인 대시보드 레이아웃 구조
 */

import React from 'react';
import './DashboardLayout.css';

const DashboardLayout = ({ children }) => {
  return (
    <div className="dashboard-layout">
      {children}
    </div>
  );
};

export const MainPanel = ({ children }) => (
  <div className="main-panel">{children}</div>
);

export const SidePanel = ({ children }) => (
  <div className="side-panel">{children}</div>
);

export default DashboardLayout;


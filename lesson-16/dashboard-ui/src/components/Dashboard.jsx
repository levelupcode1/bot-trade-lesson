/**
 * CompleteDashboard Component
 * 실시간 모니터링, 성과 분석, 제어 패널, 알림을 포함한 완전한 대시보드
 */

import React from 'react';
import NavigationBar from './NavigationBar';
import StatsCard from './StatsCard';
import DashboardLayout, { MainPanel, SidePanel } from '../layouts/DashboardLayout';
import PositionStatus from './monitoring/PositionStatus';
import ActivityLog from './monitoring/ActivityLog';
import SystemStatus from './monitoring/SystemStatus';
import NotificationCenter from './notifications/NotificationCenter';
import { useRealtimeData } from '../hooks/useRealtimeData';

const Dashboard = () => {
  const { positions, activities, systemStatus, stats } = useRealtimeData();

  return (
    <div className="dashboard-container">
      <NavigationBar />
      
      <DashboardLayout>
        <MainPanel>
          {/* 통계 카드 */}
          <div className="stats-row">
            <StatsCard
              title="총 수익률"
              value={`+${stats.totalProfit}%`}
              trend="up"
              color="success"
            />
            <StatsCard
              title="오늘 수익"
              value={`${stats.dailyProfit.toLocaleString()} KRW`}
              trend="up"
              color="success"
            />
            <StatsCard
              title="총 거래"
              value={`${stats.totalTrades} 회`}
              color="primary"
            />
            <StatsCard
              title="승률"
              value={`${stats.winRate}%`}
              trend="up"
              color="success"
            />
          </div>

          {/* 실시간 모니터링 */}
          <PositionStatus positions={positions} />
          <ActivityLog activities={activities} />
          <SystemStatus status={systemStatus} />
        </MainPanel>

        <SidePanel>
          {/* 알림 센터 */}
          <NotificationCenter />
        </SidePanel>
      </DashboardLayout>
    </div>
  );
};

export default Dashboard;


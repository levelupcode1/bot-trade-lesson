#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 모니터링 대시보드
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Optional
from threading import Thread
import os


class MonitoringDashboard:
    """웹 기반 모니터링 대시보드"""
    
    def __init__(self, 
                 data_collector,
                 performance_tracker,
                 alert_system,
                 port: int = 5000,
                 host: str = '0.0.0.0'):
        """
        Args:
            data_collector: 실시간 데이터 수집기
            performance_tracker: 성능 추적기
            alert_system: 알림 시스템
            port: 포트 번호
            host: 호스트 주소
        """
        self.data_collector = data_collector
        self.performance_tracker = performance_tracker
        self.alert_system = alert_system
        self.port = port
        self.host = host
        
        self.logger = logging.getLogger(__name__)
        
        # Flask 앱 생성
        self.app = Flask(__name__, 
                        template_folder=self._get_template_folder())
        
        # 라우트 등록
        self._register_routes()
        
        # 서버 스레드
        self.server_thread: Optional[Thread] = None
        
        self.logger.info(f"대시보드 초기화: http://{host}:{port}")
    
    def _get_template_folder(self) -> str:
        """템플릿 폴더 경로"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(current_dir, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        return templates_dir
    
    def _register_routes(self):
        """라우트 등록"""
        
        @self.app.route('/')
        def index():
            """메인 대시보드"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            """시스템 상태 API"""
            return jsonify({
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'data_collector': 'running' if hasattr(self.data_collector, '_collection_thread') else 'stopped',
                'alert_system': 'running' if hasattr(self.alert_system, '_alert_thread') else 'stopped'
            })
        
        @self.app.route('/api/performance')
        def api_performance():
            """성능 지표 API"""
            summary = self.performance_tracker.get_performance_summary()
            return jsonify(summary)
        
        @self.app.route('/api/market/<symbol>')
        def api_market(symbol):
            """시장 데이터 API"""
            latest = self.data_collector.get_latest_market_data(symbol)
            
            if latest:
                return jsonify({
                    'symbol': latest.symbol,
                    'price': latest.price,
                    'volume': latest.volume,
                    'change_24h': latest.change_24h,
                    'timestamp': latest.timestamp.isoformat()
                })
            else:
                return jsonify({'error': 'No data'}), 404
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """알림 API"""
            minutes = request.args.get('minutes', 60, type=int)
            recent_alerts = self.alert_system.get_recent_alerts(minutes)
            
            alerts_data = []
            for alert in recent_alerts:
                alerts_data.append({
                    'timestamp': alert.timestamp.isoformat(),
                    'level': alert.level.value,
                    'type': alert.alert_type.value,
                    'title': alert.title,
                    'message': alert.message
                })
            
            return jsonify({
                'total': len(alerts_data),
                'alerts': alerts_data,
                'summary': self.alert_system.get_alert_summary()
            })
        
        @self.app.route('/api/chart/<chart_type>')
        def api_chart(chart_type):
            """차트 데이터 API"""
            hours = request.args.get('hours', 24, type=int)
            
            if chart_type == 'equity':
                # 자산 곡선
                df = self.performance_tracker.get_metrics_dataframe(hours)
                
                if not df.empty:
                    return jsonify({
                        'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'values': df['total_return'].tolist()
                    })
                else:
                    return jsonify({'error': 'No data'}), 404
            
            elif chart_type == 'sharpe':
                # 샤프 비율
                df = self.performance_tracker.get_metrics_dataframe(hours)
                
                if not df.empty:
                    return jsonify({
                        'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'values': df['sharpe_ratio'].tolist()
                    })
                else:
                    return jsonify({'error': 'No data'}), 404
            
            elif chart_type == 'drawdown':
                # 낙폭
                df = self.performance_tracker.get_metrics_dataframe(hours)
                
                if not df.empty:
                    return jsonify({
                        'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'values': df['max_drawdown'].tolist()
                    })
                else:
                    return jsonify({'error': 'No data'}), 404
            
            else:
                return jsonify({'error': 'Unknown chart type'}), 400
    
    def start(self, debug: bool = False):
        """대시보드 시작"""
        def run_server():
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                use_reloader=False
            )
        
        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        self.logger.info(f"대시보드 시작: http://{self.host}:{self.port}")
    
    def stop(self):
        """대시보드 중지"""
        # Flask는 graceful shutdown이 어려움
        # 프로세스 종료 시 자동으로 중지됨
        self.logger.info("대시보드 중지")
    
    def create_dashboard_template(self):
        """대시보드 HTML 템플릿 생성"""
        template_path = os.path.join(self._get_template_folder(), 'dashboard.html')
        
        html_content = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>자동매매 모니터링 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #fff;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .status {
            display: inline-block;
            padding: 5px 15px;
            background: #10b981;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .card h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #667eea;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #3a3a3a;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #999;
        }
        
        .metric-value {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .positive {
            color: #10b981;
        }
        
        .negative {
            color: #ef4444;
        }
        
        .chart-container {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        canvas {
            max-height: 300px;
        }
        
        .alert {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid;
        }
        
        .alert-info {
            background: #1e3a8a;
            border-color: #3b82f6;
        }
        
        .alert-warning {
            background: #78350f;
            border-color: #f59e0b;
        }
        
        .alert-error {
            background: #7f1d1d;
            border-color: #ef4444;
        }
        
        .alert-critical {
            background: #7f1d1d;
            border-color: #dc2626;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .timestamp {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 자동매매 실시간 모니터링</h1>
        <span class="status" id="systemStatus">● 시스템 가동 중</span>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>📊 수익률</h2>
            <div id="returnsMetrics">로딩 중...</div>
        </div>
        
        <div class="card">
            <h2>⚠️ 리스크</h2>
            <div id="riskMetrics">로딩 중...</div>
        </div>
        
        <div class="card">
            <h2>💹 효율성</h2>
            <div id="efficiencyMetrics">로딩 중...</div>
        </div>
        
        <div class="card">
            <h2>📈 거래 통계</h2>
            <div id="tradingMetrics">로딩 중...</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>자산 곡선</h2>
        <canvas id="equityChart"></canvas>
    </div>
    
    <div class="chart-container">
        <h2>샤프 비율</h2>
        <canvas id="sharpeChart"></canvas>
    </div>
    
    <div class="card">
        <h2>🔔 최근 알림</h2>
        <div id="alerts">로딩 중...</div>
    </div>
    
    <script>
        // 차트 설정
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { 
                    grid: { color: '#3a3a3a' },
                    ticks: { color: '#999' }
                },
                y: { 
                    grid: { color: '#3a3a3a' },
                    ticks: { color: '#999' }
                }
            }
        };
        
        // 자산 곡선 차트
        const equityCtx = document.getElementById('equityChart').getContext('2d');
        const equityChart = new Chart(equityCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '총 수익률',
                    data: [],
                    borderColor: '#10b981',
                    tension: 0.4
                }]
            },
            options: chartOptions
        });
        
        // 샤프 비율 차트
        const sharpeCtx = document.getElementById('sharpeChart').getContext('2d');
        const sharpeChart = new Chart(sharpeCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '샤프 비율',
                    data: [],
                    borderColor: '#667eea',
                    tension: 0.4
                }]
            },
            options: chartOptions
        });
        
        // 데이터 업데이트
        async function updateDashboard() {
            try {
                // 성능 지표
                const perfResponse = await fetch('/api/performance');
                const perfData = await perfResponse.json();
                
                // 수익률
                document.getElementById('returnsMetrics').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">총 수익률</span>
                        <span class="metric-value ${parseFloat(perfData.returns?.total) >= 0 ? 'positive' : 'negative'}">
                            ${perfData.returns?.total || '0.00%'}
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">일간 수익률</span>
                        <span class="metric-value">${perfData.returns?.daily || '0.00%'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">월간 수익률</span>
                        <span class="metric-value">${perfData.returns?.monthly || '0.00%'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">연간 수익률</span>
                        <span class="metric-value">${perfData.returns?.annual || '0.00%'}</span>
                    </div>
                `;
                
                // 리스크
                document.getElementById('riskMetrics').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">변동성</span>
                        <span class="metric-value">${perfData.risk?.volatility || '0.00%'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">최대 낙폭</span>
                        <span class="metric-value negative">${perfData.risk?.max_drawdown || '0.00%'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">현재 낙폭</span>
                        <span class="metric-value">${perfData.risk?.current_drawdown || '0.00%'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">VaR (95%)</span>
                        <span class="metric-value">${perfData.risk?.var_95 || '0.00%'}</span>
                    </div>
                `;
                
                // 효율성
                document.getElementById('efficiencyMetrics').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">샤프 비율</span>
                        <span class="metric-value">${perfData.efficiency?.sharpe_ratio || '0.00'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">소르티노 비율</span>
                        <span class="metric-value">${perfData.efficiency?.sortino_ratio || '0.00'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">칼마 비율</span>
                        <span class="metric-value">${perfData.efficiency?.calmar_ratio || '0.00'}</span>
                    </div>
                `;
                
                // 거래 통계
                document.getElementById('tradingMetrics').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">총 거래</span>
                        <span class="metric-value">${perfData.trading?.total_trades || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">승률</span>
                        <span class="metric-value positive">${perfData.trading?.win_rate || '0.00%'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">수익 팩터</span>
                        <span class="metric-value">${perfData.trading?.profit_factor || '0.00'}</span>
                    </div>
                `;
                
                // 차트 업데이트
                const equityResponse = await fetch('/api/chart/equity?hours=24');
                if (equityResponse.ok) {
                    const equityData = await equityResponse.json();
                    equityChart.data.labels = equityData.timestamps;
                    equityChart.data.datasets[0].data = equityData.values.map(v => v * 100);
                    equityChart.update();
                }
                
                const sharpeResponse = await fetch('/api/chart/sharpe?hours=24');
                if (sharpeResponse.ok) {
                    const sharpeData = await sharpeResponse.json();
                    sharpeChart.data.labels = sharpeData.timestamps;
                    sharpeChart.data.datasets[0].data = sharpeData.values;
                    sharpeChart.update();
                }
                
                // 알림 업데이트
                const alertsResponse = await fetch('/api/alerts?minutes=60');
                const alertsData = await alertsResponse.json();
                
                let alertsHtml = '';
                if (alertsData.alerts && alertsData.alerts.length > 0) {
                    alertsData.alerts.slice(0, 10).forEach(alert => {
                        alertsHtml += `
                            <div class="alert alert-${alert.level}">
                                <strong>${alert.title}</strong><br>
                                ${alert.message}
                                <div class="timestamp">${new Date(alert.timestamp).toLocaleString('ko-KR')}</div>
                            </div>
                        `;
                    });
                } else {
                    alertsHtml = '<p style="color: #666;">알림 없음</p>';
                }
                
                document.getElementById('alerts').innerHTML = alertsHtml;
                
            } catch (error) {
                console.error('대시보드 업데이트 오류:', error);
            }
        }
        
        // 초기 로드
        updateDashboard();
        
        // 5초마다 업데이트
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"대시보드 템플릿 생성: {template_path}")


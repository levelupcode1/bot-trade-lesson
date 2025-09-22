#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비트코인 알림 파일 저장 기능 데모
실제 API 호출 없이 파일 저장 기능만 테스트합니다.
"""

import os
from datetime import datetime

def demo_file_logging():
    """파일 저장 기능 데모"""
    print("🧪 비트코인 알림 파일 저장 기능 데모")
    print("=" * 50)
    
    # 데모용 파일명
    demo_file = "demo_price_alerts.txt"
    
    # 기존 파일이 있으면 삭제
    if os.path.exists(demo_file):
        os.remove(demo_file)
        print(f"✅ 기존 데모 파일을 삭제했습니다: {demo_file}")
    
    # 파일 초기 설정
    with open(demo_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("비트코인 가격 알림 로그 (데모)\n")
        f.write("=" * 80 + "\n")
        f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"알림 임계값: 0.1%\n")
        f.write("=" * 80 + "\n\n")
    
    print(f"✅ 데모 파일이 생성되었습니다: {demo_file}")
    
    # 데모 알림들 생성
    demo_alerts = [
        {
            "id": 1,
            "base_price": 160000000,
            "current_price": 160160000,
            "change_percent": 0.1,
            "message": "첫 번째 0.1% 상승 알림"
        },
        {
            "id": 2,
            "base_price": 160160000,
            "current_price": 160320320,
            "change_percent": 0.1,
            "message": "두 번째 0.1% 상승 알림"
        },
        {
            "id": 3,
            "base_price": 160320320,
            "current_price": 160480641,
            "change_percent": 0.1,
            "message": "세 번째 0.1% 상승 알림"
        }
    ]
    
    total_change = 0.0
    
    # 각 알림을 파일에 저장
    for alert in demo_alerts:
        timestamp = datetime.now()
        change_amount = alert['current_price'] - alert['base_price']
        total_change += alert['change_percent']
        
        # 상세한 로그 엔트리 생성
        log_entry = f"🚨 알림 #{alert['id']} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_entry += "-" * 60 + "\n"
        log_entry += f"📊 알림 내용:\n"
        log_entry += f"🎯 비트코인 가격이 {alert['change_percent']:.2f}% 상승했습니다!\n"
        log_entry += f"📈 기준 가격: {alert['base_price']:,.0f}원\n"
        log_entry += f"📈 현재 가격: {alert['current_price']:,.0f}원\n"
        log_entry += f"💰 상승 금액: {change_amount:,.0f}원\n"
        log_entry += f"⏰ 알림 시간: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 추가 정보 (데모용)
        log_entry += f"📈 추가 정보:\n"
        log_entry += f"   - 24시간 거래량: {1500 + alert['id']*100:.2f} BTC\n"
        log_entry += f"   - 24시간 변화율: {2.5 + alert['id']*0.5:.2f}%\n"
        log_entry += f"   - 24시간 변화금액: {alert['base_price']*0.025:,.0f}원\n"
        log_entry += "\n"
        
        # 통계 정보
        log_entry += f"📊 세션 통계:\n"
        log_entry += f"   - 총 알림 횟수: {alert['id']}회\n"
        log_entry += f"   - 누적 상승률: {total_change:.2f}%\n"
        log_entry += f"   - 평균 상승률: {(total_change/alert['id']):.2f}%\n"
        log_entry += "=" * 80 + "\n\n"
        
        # 파일에 저장
        with open(demo_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"✅ 알림 #{alert['id']} 저장됨: {alert['message']}")
    
    # 세션 종료 로그
    with open(demo_file, 'a', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"세션 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"총 알림 횟수: {len(demo_alerts)}회\n")
        f.write(f"누적 상승률: {total_change:.2f}%\n")
        f.write("=" * 80 + "\n\n")
    
    # 파일 정보 출력
    file_size = os.path.getsize(demo_file)
    print(f"\n📁 파일 정보:")
    print(f"   파일명: {demo_file}")
    print(f"   파일 크기: {file_size:,} bytes")
    print(f"   총 알림 수: {len(demo_alerts)}개")
    
    # 파일 내용 미리보기
    print(f"\n📖 파일 내용 미리보기:")
    print("-" * 50)
    
    with open(demo_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 처음 20줄만 표시
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {line.rstrip()}")
        
        if len(lines) > 20:
            print(f"... (총 {len(lines)}줄 중 20줄만 표시)")
    
    print(f"\n🎉 데모 완료! '{demo_file}' 파일을 확인해보세요.")
    print("실제 봇을 실행하려면: python bitcoin_price_alert_with_file.py")

if __name__ == "__main__":
    demo_file_logging()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업비트 API를 사용한 비트코인 현재가 조회 모듈
"""

import requests
import time
import logging
from typing import Optional, Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_bitcoin_price() -> Optional[Dict[str, Any]]:
    """
    업비트 API를 사용하여 비트코인(KRW-BTC)의 현재가를 조회합니다.
    
    실패 시 최대 3회까지 재시도하며, 각 재시도 간격은 1초입니다.
    Rate Limit 준수를 위해 요청 간 최소 0.1초 간격을 유지합니다.
    
    Returns:
        Optional[Dict[str, Any]]: 비트코인 가격 정보 딕셔너리 또는 None (실패 시)
            - price (float): 현재가
            - volume_24h (float): 24시간 거래량
            - change_rate (float): 24시간 변동률
            - change_price (float): 24시간 변동가
            - high_price (float): 24시간 최고가
            - low_price (float): 24시간 최저가
            - timestamp (str): 조회 시각
    """
    # 업비트 API 엔드포인트
    api_url = "https://api.upbit.com/v1/ticker"
    market = "KRW-BTC"
    max_retries = 3
    retry_interval = 1.0  # 재시도 간격 (초)
    rate_limit_interval = 0.1  # Rate Limit 준수 간격 (초)
    
    for attempt in range(1, max_retries + 1):
        try:
            # Rate Limit 준수를 위한 최소 간격 대기
            if attempt > 1:
                time.sleep(rate_limit_interval)
            
            # API 요청 파라미터 설정
            params = {'markets': market}
            
            logger.info(f"비트코인 가격 조회 시도 {attempt}/{max_retries}")
            
            # API 요청 실행
            response = requests.get(api_url, params=params, timeout=10)
            
            # HTTP 상태 코드 확인
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            # 응답 데이터 검증
            if not data or len(data) == 0:
                logger.warning("응답 데이터가 비어있습니다.")
                if attempt < max_retries:
                    logger.info(f"{retry_interval}초 후 재시도합니다...")
                    time.sleep(retry_interval)
                    continue
                return None
            
            # 비트코인 가격 데이터 추출
            ticker_data = data[0]
            
            # 가격 정보 구성
            price_info = {
                'price': float(ticker_data.get('trade_price', 0)),
                'volume_24h': float(ticker_data.get('acc_trade_volume_24h', 0)),
                'change_rate': float(ticker_data.get('signed_change_rate', 0)),
                'change_price': float(ticker_data.get('signed_change_price', 0)),
                'high_price': float(ticker_data.get('high_price', 0)),
                'low_price': float(ticker_data.get('low_price', 0)),
                'timestamp': ticker_data.get('timestamp', '')
            }
            
            logger.info(f"비트코인 현재가 조회 성공: {price_info['price']:,.0f}원")
            return price_info
            
        except requests.exceptions.Timeout as e:
            logger.error(f"API 요청 타임아웃 (시도 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"{retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
                continue
            return None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP 오류 발생 (시도 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"{retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
                continue
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 오류 (시도 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"{retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
                continue
            return None
            
        except ValueError as e:
            logger.error(f"JSON 파싱 오류 (시도 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"{retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
                continue
            return None
            
        except KeyError as e:
            logger.error(f"응답 데이터 키 오류 (시도 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"{retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
                continue
            return None
            
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생 (시도 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"{retry_interval}초 후 재시도합니다...")
                time.sleep(retry_interval)
                continue
            return None
    
    # 모든 재시도 실패
    logger.error("비트코인 가격 조회 실패: 최대 재시도 횟수 초과")
    return None


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 50)
    print("비트코인 현재가 조회 테스트")
    print("=" * 50)
    
    result = get_bitcoin_price()
    
    if result:
        print("\n✅ 조회 성공!")
        print(f"현재가: {result['price']:,.0f}원")
        print(f"24시간 변동률: {result['change_rate']*100:.2f}%")
        print(f"24시간 변동가: {result['change_price']:,.0f}원")
        print(f"24시간 최고가: {result['high_price']:,.0f}원")
        print(f"24시간 최저가: {result['low_price']:,.0f}원")
        print(f"24시간 거래량: {result['volume_24h']:,.2f} BTC")
    else:
        print("\n❌ 조회 실패")

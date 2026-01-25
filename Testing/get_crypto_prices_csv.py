#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoinGecko API를 사용한 암호화폐 가격 조회 및 CSV 저장 모듈
"""

import requests
import csv
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_crypto_prices_and_save_csv(
    csv_file_path: str = "crypto_prices.csv",
    ids: List[str] = None,
    vs_currencies: List[str] = None
) -> bool:
    """
    CoinGecko API를 사용하여 암호화폐 가격을 조회하고 CSV 파일로 저장합니다.
    
    Args:
        csv_file_path (str): CSV 파일 저장 경로 (기본값: "crypto_prices.csv")
        ids (List[str]): 조회할 암호화폐 ID 리스트 (기본값: ['bitcoin', 'ethereum', 'ripple'])
        vs_currencies (List[str]): 가격 표시 통화 리스트 (기본값: ['krw', 'usd'])
    
    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    # 기본값 설정
    if ids is None:
        ids = ['bitcoin', 'ethereum', 'ripple']
    if vs_currencies is None:
        vs_currencies = ['krw', 'usd']
    
    # CoinGecko API 엔드포인트
    api_url = "https://api.coingecko.com/api/v3/simple/price"
    
    # 코인 이름 매핑 (API ID -> 표시 이름)
    coin_name_mapping = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH',
        'ripple': 'XRP'
    }
    
    try:
        # API 요청 파라미터 설정
        params = {
            'ids': ','.join(ids),
            'vs_currencies': ','.join(vs_currencies)
        }
        
        logger.info(f"암호화폐 가격 조회 시작: {ids}")
        
        # API 요청 실행
        response = requests.get(api_url, params=params, timeout=10)
        
        # HTTP 상태 코드 확인
        response.raise_for_status()
        
        # JSON 응답 파싱
        data = response.json()
        
        # 응답 데이터 검증
        if not data or not isinstance(data, dict):
            logger.error("응답 데이터가 유효하지 않습니다.")
            return False
        
        # 타임스탬프 생성
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # CSV 파일 존재 여부 확인 (헤더 작성 여부 결정)
        file_exists = os.path.exists(csv_file_path)
        
        # CSV 파일 열기 (append 모드)
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
            # CSV 작성자 생성
            writer = csv.writer(csvfile)
            
            # 헤더 작성 (파일이 없을 경우에만)
            if not file_exists:
                header = ['timestamp', 'coin_name', 'price_krw', 'price_usd']
                writer.writerow(header)
                logger.info(f"CSV 파일 생성 및 헤더 작성: {csv_file_path}")
            
            # 각 코인별 데이터 처리
            saved_count = 0
            for coin_id in ids:
                # 코인 데이터 검증
                if coin_id not in data:
                    logger.warning(f"코인 데이터를 찾을 수 없습니다: {coin_id}")
                    continue
                
                coin_data = data[coin_id]
                
                # 가격 데이터 검증
                if not isinstance(coin_data, dict):
                    logger.warning(f"코인 데이터 형식이 올바르지 않습니다: {coin_id}")
                    continue
                
                # KRW 가격 추출 및 검증
                price_krw = coin_data.get('krw')
                if price_krw is None:
                    logger.warning(f"KRW 가격 데이터가 없습니다: {coin_id}")
                    price_krw = 0.0
                else:
                    try:
                        price_krw = float(price_krw)
                        if price_krw < 0:
                            logger.warning(f"KRW 가격이 음수입니다: {coin_id}, {price_krw}")
                            price_krw = 0.0
                    except (ValueError, TypeError) as e:
                        logger.error(f"KRW 가격 변환 오류: {coin_id}, {e}")
                        price_krw = 0.0
                
                # USD 가격 추출 및 검증
                price_usd = coin_data.get('usd')
                if price_usd is None:
                    logger.warning(f"USD 가격 데이터가 없습니다: {coin_id}")
                    price_usd = 0.0
                else:
                    try:
                        price_usd = float(price_usd)
                        if price_usd < 0:
                            logger.warning(f"USD 가격이 음수입니다: {coin_id}, {price_usd}")
                            price_usd = 0.0
                    except (ValueError, TypeError) as e:
                        logger.error(f"USD 가격 변환 오류: {coin_id}, {e}")
                        price_usd = 0.0
                
                # 코인 이름 가져오기
                coin_name = coin_name_mapping.get(coin_id, coin_id.upper())
                
                # CSV 행 작성
                row = [timestamp, coin_name, price_krw, price_usd]
                writer.writerow(row)
                
                saved_count += 1
                logger.info(
                    f"데이터 저장 완료: {coin_name} - "
                    f"KRW: {price_krw:,.0f}원, USD: ${price_usd:,.2f}"
                )
            
            if saved_count == 0:
                logger.error("저장된 데이터가 없습니다.")
                return False
            
            logger.info(f"총 {saved_count}개 코인 데이터가 CSV 파일에 저장되었습니다: {csv_file_path}")
            return True
            
    except requests.exceptions.Timeout as e:
        logger.error(f"API 요청 타임아웃: {e}")
        return False
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP 오류 발생: {e}")
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 오류: {e}")
        return False
        
    except ValueError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return False
        
    except IOError as e:
        logger.error(f"CSV 파일 쓰기 오류: {e}")
        return False
        
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
        return False


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("CoinGecko API 암호화폐 가격 조회 및 CSV 저장 테스트")
    print("=" * 60)
    
    # 기본 설정으로 실행
    csv_path = "crypto_prices.csv"
    coin_ids = ['bitcoin', 'ethereum', 'ripple']
    currencies = ['krw', 'usd']
    
    print(f"\n조회 대상 코인: {', '.join(coin_ids)}")
    print(f"가격 통화: {', '.join(currencies)}")
    print(f"CSV 파일 경로: {csv_path}")
    print("\n가격 조회 및 저장 중...\n")
    
    success = get_crypto_prices_and_save_csv(
        csv_file_path=csv_path,
        ids=coin_ids,
        vs_currencies=currencies
    )
    
    if success:
        print("\n✅ 가격 조회 및 CSV 저장 성공!")
        print(f"파일 위치: {os.path.abspath(csv_path)}")
        
        # 저장된 데이터 확인 (최근 3줄)
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print("\n최근 저장된 데이터:")
                print("-" * 60)
                for line in lines[-3:]:
                    print(line.strip())
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
    else:
        print("\n❌ 가격 조회 및 CSV 저장 실패")

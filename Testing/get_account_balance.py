#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업비트 API를 사용한 계좌 잔고 조회 모듈
"""

import os
import jwt
import uuid
import requests
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_jwt_token(access_key: str, secret_key: str) -> str:
    """
    업비트 API용 JWT 토큰을 생성합니다.
    
    Args:
        access_key (str): 업비트 Access Key
        secret_key (str): 업비트 Secret Key
    
    Returns:
        str: JWT 토큰 문자열
    
    Raises:
        ValueError: API 키가 유효하지 않을 경우
    """
    if not access_key or not secret_key:
        raise ValueError("Access Key와 Secret Key가 필요합니다.")
    
    try:
        # JWT 페이로드 생성
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),  # 고유한 랜덤 값
            'timestamp': int(datetime.now().timestamp() * 1000)  # 현재 시간 (밀리초)
        }
        
        # JWT 토큰 생성 (HS256 알고리즘 사용)
        jwt_token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        logger.debug("JWT 토큰 생성 완료")
        return jwt_token
        
    except Exception as e:
        logger.error(f"JWT 토큰 생성 실패: {e}")
        raise ValueError(f"JWT 토큰 생성 중 오류 발생: {e}")


def get_account_balance() -> Optional[List[Dict[str, Any]]]:
    """
    업비트 API를 사용하여 계좌 잔고를 조회합니다.
    
    환경 변수에서 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 읽어와서
    JWT 토큰을 생성하고 계좌 정보를 조회합니다.
    
    Returns:
        Optional[List[Dict[str, Any]]]: 계좌 잔고 정보 리스트 또는 None (실패 시)
            각 계좌 정보는 다음 키를 포함:
            - currency: 통화 코드 (예: KRW, BTC, ETH)
            - balance: 보유 잔고
            - locked: 주문 중 묶인 잔고
            - avg_buy_price: 평균 매수가
            - avg_buy_price_modified: 평균 매수가 수정 여부
            - unit_currency: 기준 통화 (KRW)
    
    Raises:
        ValueError: 환경 변수에 API 키가 설정되지 않은 경우
    """
    # 업비트 API 엔드포인트
    api_url = "https://api.upbit.com/v1/accounts"
    
    try:
        # 환경 변수에서 API 키 가져오기
        access_key = os.getenv('UPBIT_ACCESS_KEY')
        secret_key = os.getenv('UPBIT_SECRET_KEY')
        
        # API 키 검증
        if not access_key:
            error_msg = "환경 변수 UPBIT_ACCESS_KEY가 설정되지 않았습니다."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not secret_key:
            error_msg = "환경 변수 UPBIT_SECRET_KEY가 설정되지 않았습니다."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("계좌 잔고 조회 시작")
        
        # JWT 토큰 생성
        try:
            jwt_token = create_jwt_token(access_key, secret_key)
            logger.debug("JWT 토큰 생성 성공")
        except ValueError as e:
            logger.error(f"JWT 토큰 생성 실패: {e}")
            return None
        
        # Authorization 헤더 설정 (Bearer 토큰)
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        # API 요청 실행
        logger.info("업비트 API에 계좌 정보 요청 중...")
        response = requests.get(api_url, headers=headers, timeout=10)
        
        # HTTP 상태 코드 확인
        response.raise_for_status()
        
        # JSON 응답 파싱
        accounts_data = response.json()
        
        # 응답 데이터 검증
        if not isinstance(accounts_data, list):
            logger.error(f"응답 데이터 형식이 올바르지 않습니다: {type(accounts_data)}")
            return None
        
        logger.info(f"계좌 잔고 조회 성공: {len(accounts_data)}개 자산")
        
        # 잔고가 있는 계좌만 필터링 (선택사항)
        accounts_with_balance = [
            account for account in accounts_data
            if float(account.get('balance', 0)) > 0 or float(account.get('locked', 0)) > 0
        ]
        
        if accounts_with_balance:
            logger.info(f"잔고가 있는 계좌: {len(accounts_with_balance)}개")
        else:
            logger.info("잔고가 있는 계좌가 없습니다.")
        
        return accounts_data
        
    except ValueError as e:
        # 환경 변수 관련 오류는 그대로 전파
        logger.error(f"환경 변수 오류: {e}")
        raise
        
    except requests.exceptions.Timeout as e:
        logger.error(f"API 요청 타임아웃: {e}")
        return None
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else None
        error_msg = f"HTTP 오류 발생 (상태 코드: {status_code}): {e}"
        logger.error(error_msg)
        
        # 응답 본문이 있으면 로깅
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f"오류 상세: {error_detail}")
            except:
                logger.error(f"응답 본문: {e.response.text}")
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 오류: {e}")
        return None
        
    except ValueError as e:
        # JSON 파싱 오류
        logger.error(f"JSON 파싱 오류: {e}")
        return None
        
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
        return None


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("업비트 API 계좌 잔고 조회 테스트")
    print("=" * 60)
    
    # 환경 변수 확인
    access_key = os.getenv('UPBIT_ACCESS_KEY')
    secret_key = os.getenv('UPBIT_SECRET_KEY')
    
    if not access_key or not secret_key:
        print("\n⚠️  환경 변수가 설정되지 않았습니다.")
        print("다음 환경 변수를 설정해주세요:")
        print("  - UPBIT_ACCESS_KEY: 업비트 Access Key")
        print("  - UPBIT_SECRET_KEY: 업비트 Secret Key")
        print("\n설정 방법:")
        print("  Windows (PowerShell):")
        print("    $env:UPBIT_ACCESS_KEY='your_access_key'")
        print("    $env:UPBIT_SECRET_KEY='your_secret_key'")
        print("\n  Windows (CMD):")
        print("    set UPBIT_ACCESS_KEY=your_access_key")
        print("    set UPBIT_SECRET_KEY=your_secret_key")
        print("\n  Linux/Mac:")
        print("    export UPBIT_ACCESS_KEY='your_access_key'")
        print("    export UPBIT_SECRET_KEY='your_secret_key'")
    else:
        print(f"\n✅ 환경 변수 확인 완료")
        print(f"Access Key: {access_key[:8]}...")
        print(f"Secret Key: {'*' * len(secret_key)}")
        print("\n계좌 잔고 조회 중...\n")
        
        accounts = get_account_balance()
        
        if accounts:
            print("\n✅ 계좌 잔고 조회 성공!\n")
            print("-" * 60)
            
            # 잔고가 있는 계좌만 표시
            accounts_with_balance = [
                acc for acc in accounts
                if float(acc.get('balance', 0)) > 0 or float(acc.get('locked', 0)) > 0
            ]
            
            if accounts_with_balance:
                print(f"총 {len(accounts_with_balance)}개 자산 보유:\n")
                
                for account in accounts_with_balance:
                    currency = account.get('currency', 'N/A')
                    balance = float(account.get('balance', 0))
                    locked = float(account.get('locked', 0))
                    avg_buy_price = float(account.get('avg_buy_price', 0))
                    total_balance = balance + locked
                    
                    print(f"📊 {currency}")
                    print(f"   보유량: {balance:,.8f}")
                    if locked > 0:
                        print(f"   주문 중: {locked:,.8f}")
                    print(f"   총량: {total_balance:,.8f}")
                    
                    if currency == 'KRW':
                        print(f"   잔고: {balance:,.0f}원")
                    elif avg_buy_price > 0:
                        krw_value = total_balance * avg_buy_price
                        print(f"   평균매수가: {avg_buy_price:,.0f}원")
                        print(f"   평가금액: {krw_value:,.0f}원")
                    
                    print()
            else:
                print("보유 중인 자산이 없습니다.")
            
            print("-" * 60)
        else:
            print("\n❌ 계좌 잔고 조회 실패")
            print("로그를 확인하여 오류 원인을 파악하세요.")

"""
업비트 MCP 서버
실시간 가격 조회, 호가 정보, 잔고 조회 등의 기능을 제공하는 MCP 서버
"""

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
from mcp.server.stdio import stdio_server
import pyupbit
import json
import asyncio
import os
from datetime import datetime
from typing import Optional

# MCP 서버 인스턴스 생성
server = Server("upbit-trading-server")

# 환경변수에서 API 키 로드 (실제 거래용)
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY", "")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY", "")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="get_current_price",
            description="특정 암호화폐의 현재 시장 가격을 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "티커 심볼 (예: KRW-BTC, KRW-ETH)"
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="get_multiple_prices",
            description="여러 암호화폐의 현재 가격을 한 번에 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "티커 심볼 배열 (예: [\"KRW-BTC\", \"KRW-ETH\"])"
                    }
                },
                "required": ["tickers"]
            }
        ),
        Tool(
            name="get_orderbook",
            description="특정 암호화폐의 호가 정보(매수/매도 주문)를 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "티커 심볼"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "호가 깊이 (기본값: 5)",
                        "default": 5
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="get_balance",
            description="계정의 잔고 정보를 조회합니다 (API 키 필요)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_market_list",
            description="거래 가능한 모든 마켓 목록을 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "기준 통화 (KRW, BTC, USDT 등)",
                        "default": "KRW"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_ohlcv",
            description="특정 암호화폐의 OHLCV(시가/고가/저가/종가/거래량) 데이터를 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "티커 심볼"
                    },
                    "interval": {
                        "type": "string",
                        "description": "시간 간격 (day, minute1, minute3, minute5, minute10, minute15, minute30, minute60, minute240, week, month)",
                        "default": "day"
                    },
                    "count": {
                        "type": "integer",
                        "description": "조회할 캔들 수 (기본값: 200)",
                        "default": 200
                    }
                },
                "required": ["ticker"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행"""
    
    try:
        if name == "get_current_price":
            ticker = arguments["ticker"]
            price = pyupbit.get_current_price(ticker)
            
            if price is None:
                return [TextContent(
                    type="text",
                    text=f"❌ {ticker}의 가격을 조회할 수 없습니다. 티커를 확인해주세요."
                )]
            
            return [TextContent(
                type="text",
                text=f"💰 {ticker} 현재가: {price:,.0f} KRW\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )]
        
        elif name == "get_multiple_prices":
            tickers = arguments["tickers"]
            prices = pyupbit.get_current_price(tickers)
            
            if isinstance(prices, dict):
                result_lines = ["📊 현재 가격 정보:\n"]
                for ticker, price in prices.items():
                    if price:
                        result_lines.append(f"  • {ticker}: {price:,.0f} KRW")
                    else:
                        result_lines.append(f"  • {ticker}: 조회 실패")
                
                result_lines.append(f"\n⏰ 조회 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                return [TextContent(
                    type="text",
                    text="\n".join(result_lines)
                )]
            else:
                return [TextContent(
                    type="text",
                    text="❌ 가격 조회에 실패했습니다."
                )]
        
        elif name == "get_orderbook":
            ticker = arguments["ticker"]
            depth = arguments.get("depth", 5)
            
            orderbook = pyupbit.get_orderbook(ticker)
            
            if not orderbook:
                return [TextContent(
                    type="text",
                    text=f"❌ {ticker}의 호가 정보를 조회할 수 없습니다."
                )]
            
            result_lines = [f"📈 {ticker} 호가 정보\n"]
            result_lines.append("매도 호가 (ASK):")
            
            asks = orderbook[0]['orderbook_units'][:depth]
            asks.reverse()  # 높은 가격부터 표시
            
            for unit in asks:
                price = unit['ask_price']
                size = unit['ask_size']
                result_lines.append(f"  {price:>12,.0f} KRW | {size:>10.4f}")
            
            result_lines.append("\n" + "-" * 40 + "\n")
            result_lines.append("매수 호가 (BID):")
            
            bids = orderbook[0]['orderbook_units'][:depth]
            
            for unit in bids:
                price = unit['bid_price']
                size = unit['bid_size']
                result_lines.append(f"  {price:>12,.0f} KRW | {size:>10.4f}")
            
            total_ask_size = sum([u['ask_size'] for u in orderbook[0]['orderbook_units'][:depth]])
            total_bid_size = sum([u['bid_size'] for u in orderbook[0]['orderbook_units'][:depth]])
            
            result_lines.append(f"\n💹 총 매도량: {total_ask_size:.4f}")
            result_lines.append(f"💹 총 매수량: {total_bid_size:.4f}")
            result_lines.append(f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
        
        elif name == "get_balance":
            if not ACCESS_KEY or not SECRET_KEY:
                return [TextContent(
                    type="text",
                    text="❌ API 키가 설정되지 않았습니다.\n환경변수 UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY를 설정해주세요."
                )]
            
            upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)
            balances = upbit.get_balances()
            
            result_lines = ["💼 보유 자산 정보:\n"]
            total_krw = 0
            
            for balance in balances:
                currency = balance['currency']
                amount = float(balance['balance'])
                locked = float(balance['locked'])
                avg_buy_price = float(balance['avg_buy_price'])
                
                if amount > 0 or locked > 0:
                    if currency == 'KRW':
                        result_lines.append(f"  • {currency}: {amount:,.0f} KRW (주문중: {locked:,.0f} KRW)")
                        total_krw += amount
                    else:
                        ticker = f"KRW-{currency}"
                        current_price = pyupbit.get_current_price(ticker)
                        
                        if current_price:
                            value_krw = amount * current_price
                            profit_rate = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0
                            
                            result_lines.append(
                                f"  • {currency}: {amount:.4f} "
                                f"(평단가: {avg_buy_price:,.0f}, 현재가: {current_price:,.0f}, "
                                f"수익률: {profit_rate:+.2f}%, 평가금액: {value_krw:,.0f} KRW)"
                            )
                            total_krw += value_krw
            
            result_lines.append(f"\n💰 총 평가금액: {total_krw:,.0f} KRW")
            result_lines.append(f"⏰ 조회 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
        
        elif name == "get_market_list":
            currency = arguments.get("currency", "KRW")
            markets = pyupbit.get_tickers(fiat=currency)
            
            result_lines = [f"📋 {currency} 마켓 목록 ({len(markets)}개):\n"]
            
            for i, market in enumerate(markets, 1):
                coin = market.split('-')[1]
                result_lines.append(f"  {i:3d}. {market:12s} ({coin})")
                
                if i % 20 == 0:
                    result_lines.append("")  # 20개마다 빈 줄
            
            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
        
        elif name == "get_ohlcv":
            ticker = arguments["ticker"]
            interval = arguments.get("interval", "day")
            count = arguments.get("count", 200)
            
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            
            if df is None or df.empty:
                return [TextContent(
                    type="text",
                    text=f"❌ {ticker}의 OHLCV 데이터를 조회할 수 없습니다."
                )]
            
            # 최근 5개 데이터만 표시
            recent_data = df.tail(5)
            
            result_lines = [f"📊 {ticker} OHLCV 데이터 (간격: {interval}, 최근 5개):\n"]
            result_lines.append("날짜/시간              시가        고가        저가        종가        거래량")
            result_lines.append("-" * 80)
            
            for idx, row in recent_data.iterrows():
                result_lines.append(
                    f"{idx.strftime('%Y-%m-%d %H:%M')}  "
                    f"{row['open']:>10,.0f}  {row['high']:>10,.0f}  "
                    f"{row['low']:>10,.0f}  {row['close']:>10,.0f}  "
                    f"{row['volume']:>12,.2f}"
                )
            
            # 통계 정보
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            change = ((latest['close'] - prev['close']) / prev['close'] * 100)
            
            result_lines.append(f"\n📈 통계:")
            result_lines.append(f"  • 최신 종가: {latest['close']:,.0f} KRW")
            result_lines.append(f"  • 전일 대비: {change:+.2f}%")
            result_lines.append(f"  • 총 데이터 수: {len(df)}개")
            
            # JSON 형식으로도 제공
            json_data = df.to_json(orient='records', date_format='iso')
            
            result_lines.append(f"\n💾 전체 데이터 (JSON):")
            result_lines.append(f"총 {len(df)}개 레코드")
            
            return [
                TextContent(
                    type="text",
                    text="\n".join(result_lines)
                ),
                TextContent(
                    type="text",
                    text=f"\nJSON 데이터 (첫 3개):\n{json.dumps(json.loads(json_data)[:3], indent=2, ensure_ascii=False)}"
                )
            ]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ 알 수 없는 도구: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 오류 발생: {str(e)}"
        )]

@server.list_resources()
async def list_resources() -> list[Resource]:
    """사용 가능한 리소스 목록 반환"""
    return [
        Resource(
            uri="upbit://ohlcv/KRW-BTC",
            name="비트코인 일봉 데이터",
            mimeType="application/json",
            description="비트코인(BTC)의 일봉 OHLCV 데이터 (최근 200일)"
        ),
        Resource(
            uri="upbit://ohlcv/KRW-ETH",
            name="이더리움 일봉 데이터",
            mimeType="application/json",
            description="이더리움(ETH)의 일봉 OHLCV 데이터 (최근 200일)"
        ),
        Resource(
            uri="upbit://markets/all",
            name="전체 마켓 목록",
            mimeType="application/json",
            description="업비트의 모든 거래 가능한 마켓 목록"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> list[TextContent]:
    """리소스 읽기"""
    
    try:
        if uri.startswith("upbit://ohlcv/"):
            ticker = uri.split("/")[-1]
            df = pyupbit.get_ohlcv(ticker, count=200)
            
            if df is None:
                return [TextContent(
                    type="text",
                    text=f"❌ {ticker}의 데이터를 조회할 수 없습니다."
                )]
            
            json_data = df.to_json(orient='records', date_format='iso')
            
            return [TextContent(
                type="text",
                text=json_data
            )]
        
        elif uri == "upbit://markets/all":
            markets = pyupbit.get_tickers()
            
            market_data = {
                "total_count": len(markets),
                "markets": markets,
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(market_data, ensure_ascii=False, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ 알 수 없는 리소스: {uri}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 리소스 읽기 오류: {str(e)}"
        )]

async def main():
    """MCP 서버 실행"""
    print("🚀 업비트 MCP 서버 시작...", flush=True)
    print("📡 stdio를 통해 통신 대기 중...", flush=True)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  서버 종료", flush=True)
    except Exception as e:
        print(f"❌ 서버 오류: {e}", flush=True)


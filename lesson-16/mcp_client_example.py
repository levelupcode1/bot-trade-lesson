"""
MCP 클라이언트 예시
업비트 MCP 서버와 통신하는 클라이언트 예제
"""

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import json
from datetime import datetime

class UpbitMCPClient:
    """업비트 MCP 클라이언트 래퍼"""
    
    def __init__(self):
        self.session: ClientSession = None
    
    async def connect(self):
        """MCP 서버에 연결"""
        # 서버 실행 파라미터 설정
        server_params = StdioServerParameters(
            command="python",
            args=["upbit_mcp_server.py"],
            env=None
        )
        
        print("🔌 업비트 MCP 서버 연결 중...")
        
        # stdio를 통해 서버와 연결
        self.stdio_transport = await stdio_client(server_params)
        self.read_stream, self.write_stream = self.stdio_transport.__aenter__()
        
        # 세션 초기화
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()
        
        # 서버 초기화
        await self.session.initialize()
        
        print("✅ 연결 완료!")
        
        # 사용 가능한 도구 확인
        tools = await self.session.list_tools()
        print(f"\n📋 사용 가능한 도구 ({len(tools.tools)}개):")
        for tool in tools.tools:
            print(f"  • {tool.name}: {tool.description}")
    
    async def disconnect(self):
        """연결 종료"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_transport'):
            await self.stdio_transport.__aexit__(None, None, None)
        print("\n🔌 연결 종료")
    
    async def get_current_price(self, ticker: str):
        """현재 가격 조회"""
        result = await self.session.call_tool(
            "get_current_price",
            {"ticker": ticker}
        )
        return result.content[0].text
    
    async def get_multiple_prices(self, tickers: list[str]):
        """여러 코인 가격 조회"""
        result = await self.session.call_tool(
            "get_multiple_prices",
            {"tickers": tickers}
        )
        return result.content[0].text
    
    async def get_orderbook(self, ticker: str, depth: int = 5):
        """호가 정보 조회"""
        result = await self.session.call_tool(
            "get_orderbook",
            {"ticker": ticker, "depth": depth}
        )
        return result.content[0].text
    
    async def get_balance(self):
        """잔고 조회"""
        result = await self.session.call_tool(
            "get_balance",
            {}
        )
        return result.content[0].text
    
    async def get_market_list(self, currency: str = "KRW"):
        """마켓 목록 조회"""
        result = await self.session.call_tool(
            "get_market_list",
            {"currency": currency}
        )
        return result.content[0].text
    
    async def get_ohlcv(self, ticker: str, interval: str = "day", count: int = 200):
        """OHLCV 데이터 조회"""
        result = await self.session.call_tool(
            "get_ohlcv",
            {"ticker": ticker, "interval": interval, "count": count}
        )
        return result.content[0].text
    
    async def read_resource(self, uri: str):
        """리소스 읽기"""
        result = await self.session.read_resource(uri)
        return result.contents[0].text

async def demo_basic_usage():
    """기본 사용 예제"""
    client = UpbitMCPClient()
    
    try:
        await client.connect()
        
        print("\n" + "=" * 60)
        print("💰 1. 비트코인 현재 가격 조회")
        print("=" * 60)
        price = await client.get_current_price("KRW-BTC")
        print(price)
        
        print("\n" + "=" * 60)
        print("📊 2. 여러 코인 가격 조회")
        print("=" * 60)
        prices = await client.get_multiple_prices([
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL"
        ])
        print(prices)
        
        print("\n" + "=" * 60)
        print("📈 3. 비트코인 호가 정보 조회")
        print("=" * 60)
        orderbook = await client.get_orderbook("KRW-BTC", depth=5)
        print(orderbook)
        
        print("\n" + "=" * 60)
        print("📋 4. KRW 마켓 목록 조회 (일부)")
        print("=" * 60)
        markets = await client.get_market_list("KRW")
        # 처음 20줄만 출력
        print("\n".join(markets.split("\n")[:22]))
        print("... (생략)")
        
        print("\n" + "=" * 60)
        print("📊 5. 비트코인 일봉 데이터 조회")
        print("=" * 60)
        ohlcv = await client.get_ohlcv("KRW-BTC", interval="day", count=7)
        print(ohlcv)
        
    finally:
        await client.disconnect()

async def demo_trading_analysis():
    """거래 분석 예제"""
    client = UpbitMCPClient()
    
    try:
        await client.connect()
        
        print("\n" + "=" * 60)
        print("🔍 거래 분석: 비트코인 (KRW-BTC)")
        print("=" * 60)
        
        # 1. 현재 가격
        price_info = await client.get_current_price("KRW-BTC")
        print(f"\n{price_info}")
        
        # 2. 호가 정보로 매수/매도 압력 분석
        orderbook_info = await client.get_orderbook("KRW-BTC", depth=10)
        print(f"\n{orderbook_info}")
        
        # 3. 과거 데이터로 추세 분석
        print("\n📊 과거 데이터 분석 중...")
        ohlcv_data = await client.read_resource("upbit://ohlcv/KRW-BTC")
        
        # JSON 파싱
        candles = json.loads(ohlcv_data)
        
        # 최근 7일 데이터로 간단한 분석
        recent_candles = candles[-7:]
        
        print("\n📈 최근 7일 추세:")
        for candle in recent_candles:
            date = candle['index'].split('T')[0]
            close = candle['close']
            volume = candle['volume']
            print(f"  {date}: {close:>12,.0f} KRW (거래량: {volume:>10,.2f})")
        
        # 간단한 추세 계산
        first_close = recent_candles[0]['close']
        last_close = recent_candles[-1]['close']
        change_pct = ((last_close - first_close) / first_close) * 100
        
        trend = "상승" if change_pct > 0 else "하락"
        print(f"\n📊 7일 추세: {trend} ({change_pct:+.2f}%)")
        
        # 평균 거래량
        avg_volume = sum([c['volume'] for c in recent_candles]) / len(recent_candles)
        print(f"💹 평균 거래량: {avg_volume:,.2f}")
        
    finally:
        await client.disconnect()

async def demo_real_time_monitoring():
    """실시간 모니터링 예제"""
    client = UpbitMCPClient()
    
    try:
        await client.connect()
        
        print("\n" + "=" * 60)
        print("📡 실시간 가격 모니터링 (10초 간격, 5회)")
        print("=" * 60)
        
        tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        
        for i in range(5):
            print(f"\n🔄 업데이트 #{i+1} - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 60)
            
            prices = await client.get_multiple_prices(tickers)
            print(prices)
            
            if i < 4:  # 마지막 반복에서는 대기하지 않음
                await asyncio.sleep(10)
        
        print("\n✅ 모니터링 완료")
        
    finally:
        await client.disconnect()

async def demo_parallel_queries():
    """병렬 쿼리 예제"""
    client = UpbitMCPClient()
    
    try:
        await client.connect()
        
        print("\n" + "=" * 60)
        print("⚡ 병렬 데이터 조회")
        print("=" * 60)
        
        # 여러 작업을 동시에 실행
        tasks = [
            client.get_current_price("KRW-BTC"),
            client.get_current_price("KRW-ETH"),
            client.get_orderbook("KRW-BTC", depth=3),
            client.get_market_list("KRW"),
        ]
        
        print("\n⏳ 4개의 쿼리를 병렬로 실행 중...")
        start_time = datetime.now()
        
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"✅ 완료! (소요시간: {elapsed:.2f}초)\n")
        
        print("📊 결과:")
        print("\n1️⃣ BTC 가격:")
        print(results[0])
        
        print("\n2️⃣ ETH 가격:")
        print(results[1])
        
        print("\n3️⃣ BTC 호가:")
        print("\n".join(results[2].split("\n")[:15]))  # 일부만 출력
        
        print("\n4️⃣ 마켓 목록:")
        print("\n".join(results[3].split("\n")[:10]))  # 일부만 출력
        print("... (생략)")
        
    finally:
        await client.disconnect()

def main():
    """메인 함수"""
    print("""
╔══════════════════════════════════════════════════════════╗
║          업비트 MCP 클라이언트 데모                      ║
╚══════════════════════════════════════════════════════════╝

다음 예제 중 하나를 선택하세요:

1. 기본 사용 예제 (가격, 호가, 마켓 목록 등)
2. 거래 분석 예제 (추세 분석)
3. 실시간 모니터링 (10초 간격, 5회)
4. 병렬 쿼리 예제 (성능 최적화)
0. 종료
    """)
    
    while True:
        choice = input("\n선택 (0-4): ").strip()
        
        if choice == "0":
            print("👋 종료합니다.")
            break
        elif choice == "1":
            asyncio.run(demo_basic_usage())
        elif choice == "2":
            asyncio.run(demo_trading_analysis())
        elif choice == "3":
            asyncio.run(demo_real_time_monitoring())
        elif choice == "4":
            asyncio.run(demo_parallel_queries())
        else:
            print("❌ 잘못된 선택입니다. 0-4 중에서 선택해주세요.")
        
        input("\n아무 키나 눌러 계속...")

if __name__ == "__main__":
    main()


# Lesson 16: MCP (Model Context Protocol) 실전 활용

## 📚 개요

이 레슨에서는 **MCP(Model Context Protocol)**를 실제 자동매매 시스템에 적용하는 방법을 학습합니다.

### 학습 목표
- ✅ MCP의 개념과 아키텍처 이해
- ✅ MCP 서버 구현 방법 학습
- ✅ MCP 클라이언트 사용법 습득
- ✅ 자동매매 시스템에 MCP 통합

## 📂 파일 구조

```
lesson-16/
├── MCP_GUIDE.md              # MCP 완벽 가이드 (이론)
├── upbit_mcp_server.py        # 업비트 MCP 서버 구현
├── mcp_client_example.py      # MCP 클라이언트 예제
├── requirements.txt           # 필요한 패키지
├── .env.example              # 환경변수 예시
└── README.md                 # 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정 (선택사항)

실제 거래 API를 사용하려면 `.env` 파일 생성:

```bash
# .env 파일
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here
```

⚠️ **주의**: API 키 없이도 가격 조회, 호가 정보 등 공개 API는 사용 가능합니다.

### 3. MCP 서버 실행

```bash
# 터미널 1: MCP 서버 실행
python upbit_mcp_server.py
```

### 4. MCP 클라이언트 실행

```bash
# 터미널 2: 클라이언트 예제 실행
python mcp_client_example.py
```

## 📖 주요 개념

### MCP란?

**Model Context Protocol (MCP)**는 AI 모델과 외부 데이터 소스/도구를 표준화된 방식으로 연결하는 프로토콜입니다.

#### 핵심 구성요소

```
┌─────────────┐
│ AI Client   │  (MCP 클라이언트)
│             │
└──────┬──────┘
       │ JSON-RPC 2.0
       │
┌──────┴──────┐
│ MCP Server  │  (도구/데이터 제공)
│             │
└─────────────┘
```

### 주요 기능

#### 1. Tools (도구)
MCP 서버가 제공하는 실행 가능한 함수

```python
# 예: 현재 가격 조회
await client.call_tool("get_current_price", {"ticker": "KRW-BTC"})
```

#### 2. Resources (리소스)
MCP 서버가 제공하는 데이터

```python
# 예: OHLCV 데이터 조회
await client.read_resource("upbit://ohlcv/KRW-BTC")
```

## 🔧 구현 예시

### MCP 서버 구현

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_price",
            description="가격 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}
                },
                "required": ["ticker"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_price":
        # 실제 로직 구현
        price = get_market_price(arguments["ticker"])
        return [TextContent(type="text", text=f"Price: {price}")]
```

### MCP 클라이언트 사용

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 서버 연결
server_params = StdioServerParameters(
    command="python",
    args=["my_mcp_server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # 도구 호출
        result = await session.call_tool("get_price", {"ticker": "KRW-BTC"})
        print(result.content[0].text)
```

## 💡 실전 활용 예제

### 1. 기본 사용 (demo_basic_usage)

```python
# 가격 조회
price = await client.get_current_price("KRW-BTC")

# 여러 코인 동시 조회
prices = await client.get_multiple_prices(["KRW-BTC", "KRW-ETH"])

# 호가 정보
orderbook = await client.get_orderbook("KRW-BTC", depth=5)
```

### 2. 거래 분석 (demo_trading_analysis)

```python
# 현재 시장 상황 파악
price = await client.get_current_price("KRW-BTC")
orderbook = await client.get_orderbook("KRW-BTC")

# 과거 데이터로 추세 분석
ohlcv_data = await client.read_resource("upbit://ohlcv/KRW-BTC")
candles = json.loads(ohlcv_data)

# 추세 계산
recent = candles[-7:]
trend = analyze_trend(recent)
```

### 3. 실시간 모니터링 (demo_real_time_monitoring)

```python
# 10초마다 가격 업데이트
while True:
    prices = await client.get_multiple_prices(tickers)
    print(prices)
    await asyncio.sleep(10)
```

### 4. 병렬 쿼리 (demo_parallel_queries)

```python
# 여러 API를 동시에 호출
tasks = [
    client.get_current_price("KRW-BTC"),
    client.get_orderbook("KRW-BTC"),
    client.get_market_list("KRW"),
]

results = await asyncio.gather(*tasks)
```

## 🎯 자동매매 시스템 통합

### 아키텍처

```
┌─────────────────────────────────────┐
│     Trading Strategy Engine         │
│  (매매 전략 실행)                    │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───┴────┐          ┌─────┴─────┐
│ Upbit  │          │ Technical │
│  MCP   │          │ Indicator │
│ Server │          │    MCP    │
└────────┘          └───────────┘
```

### 전략 구현 예시

```python
class MCPTradingStrategy:
    async def analyze_market(self, ticker):
        # 1. 현재 가격 (Upbit MCP)
        price = await upbit_client.call_tool("get_current_price", {...})
        
        # 2. 기술적 지표 (Indicator MCP)
        rsi = await indicator_client.call_tool("calculate_rsi", {...})
        
        # 3. 종합 분석
        signal = self.generate_signal(price, rsi)
        return signal
    
    async def execute_trade(self, signal):
        if signal == "BUY":
            await upbit_client.call_tool("place_order", {
                "ticker": "KRW-BTC",
                "side": "bid",
                ...
            })
```

## 📊 제공되는 MCP 도구

### 업비트 MCP 서버 (upbit_mcp_server.py)

| 도구 | 설명 | 파라미터 |
|------|------|----------|
| `get_current_price` | 현재 가격 조회 | `ticker` |
| `get_multiple_prices` | 여러 코인 가격 조회 | `tickers[]` |
| `get_orderbook` | 호가 정보 조회 | `ticker`, `depth` |
| `get_balance` | 잔고 조회 (API 키 필요) | - |
| `get_market_list` | 마켓 목록 조회 | `currency` |
| `get_ohlcv` | OHLCV 데이터 조회 | `ticker`, `interval`, `count` |

### 리소스

| URI | 설명 |
|-----|------|
| `upbit://ohlcv/KRW-BTC` | 비트코인 일봉 데이터 |
| `upbit://ohlcv/KRW-ETH` | 이더리움 일봉 데이터 |
| `upbit://markets/all` | 전체 마켓 목록 |

## 🔒 보안 고려사항

### API 키 관리

```python
# ✅ 좋은 예: 환경변수 사용
import os
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")

# ❌ 나쁜 예: 하드코딩
ACCESS_KEY = "your-key-here"  # 절대 금지!
```

### 권한 제어

```python
# MCP 서버에서 권한 확인
async def call_tool(name, arguments):
    if name == "place_order":
        # 실제 거래는 추가 인증 필요
        if not validate_permission():
            raise PermissionError("권한 없음")
    # ...
```

## 🧪 테스트

### 단위 테스트

```python
# Mock MCP 서버로 테스트
class MockUpbitServer:
    async def call_tool(self, name, args):
        return [TextContent(type="text", text="85000000")]

# 전략 테스트
strategy = TradingStrategy(client=mock_server)
signal = await strategy.analyze_market("KRW-BTC")
assert signal in ["BUY", "SELL", "HOLD"]
```

### 통합 테스트

```bash
# 실제 서버 연동 테스트
python mcp_client_example.py
# 옵션 1 선택 -> 기본 기능 테스트
```

## 📈 성능 최적화

### 1. 캐싱

```python
class CachedMCPClient:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 60
    
    async def call_tool_with_cache(self, name, args):
        cache_key = f"{name}:{str(args)}"
        
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
        
        result = await self.session.call_tool(name, args)
        self.cache[cache_key] = (result, time.time())
        return result
```

### 2. 병렬 처리

```python
# 여러 요청을 동시에 처리
tasks = [
    client.get_current_price(ticker)
    for ticker in ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
]
results = await asyncio.gather(*tasks)
```

### 3. 연결 풀

```python
# 여러 MCP 서버를 풀로 관리
class MCPConnectionPool:
    def __init__(self):
        self.connections = {}
    
    async def get_client(self, server_name):
        if server_name not in self.connections:
            self.connections[server_name] = await self.create_client(server_name)
        return self.connections[server_name]
```

## 🐛 문제 해결

### 서버 연결 실패

```bash
# 문제: "Connection refused"
# 해결: 서버가 실행 중인지 확인
python upbit_mcp_server.py

# 문제: "Module not found: mcp"
# 해결: MCP 패키지 설치
pip install mcp
```

### API 키 오류

```bash
# 문제: "API 키가 설정되지 않았습니다"
# 해결: .env 파일 생성 및 환경변수 설정
cp .env.example .env
# .env 파일에 실제 키 입력
```

### JSON 파싱 오류

```python
# 문제: JSON 파싱 실패
# 해결: 데이터 타입 확인
try:
    data = json.loads(result)
except json.JSONDecodeError:
    print(f"Invalid JSON: {result}")
```

## 📚 추가 학습 자료

### 공식 문서
- [MCP 공식 사이트](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### 예제 및 튜토리얼
- [MCP 서버 예제 모음](https://github.com/modelcontextprotocol/servers)
- [Anthropic MCP 가이드](https://docs.anthropic.com/en/docs/mcp)

### 관련 레슨
- Lesson 06: 업비트 API 통합
- Lesson 08: 자동매매 시스템 아키텍처
- Lesson 13: 모니터링 및 알림 시스템

## 🎓 다음 단계

1. **기본 MCP 서버 만들기**
   - [ ] 간단한 가격 조회 서버 구현
   - [ ] 클라이언트로 연결 테스트

2. **기능 확장**
   - [ ] 기술적 지표 MCP 서버 추가
   - [ ] 뉴스 감성 분석 MCP 서버 추가

3. **자동매매 통합**
   - [ ] 기존 전략에 MCP 적용
   - [ ] 여러 MCP 서버 조합

4. **고급 기능**
   - [ ] 캐싱 및 성능 최적화
   - [ ] 보안 강화 (인증, 권한)
   - [ ] 에러 처리 및 복구

## ⚠️ 주의사항

1. **실제 거래 주의**
   - 테스트는 반드시 모의 환경에서
   - 실제 자금 사용 시 충분한 검증 필요
   - 소액으로 시작

2. **API 제한**
   - 업비트: 초당 10회 요청 제한
   - 과도한 요청 시 IP 차단 가능

3. **보안**
   - API 키 절대 공개 금지
   - `.env` 파일을 `.gitignore`에 추가
   - 최소 권한 원칙 적용

## 📝 라이센스

이 프로젝트는 교육 목적으로 제공됩니다.

## 🤝 기여

이슈 및 개선 제안은 언제든 환영합니다!

---

**Happy Trading with MCP! 🚀📈**


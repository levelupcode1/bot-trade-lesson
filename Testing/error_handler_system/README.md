# 24시간 연속 운영 자동매매 시스템 오류 처리 및 복구 시스템

24시간 연속 운영이 가능한 자동매매 시스템의 오류 처리 및 자동 복구 시스템입니다.

## 📁 프로젝트 구조

```
error_handler_system/
├── __init__.py
├── error_handler.py          # 오류 처리 및 복구 클래스
├── service.py                # Docker 서비스 실행 파일
├── requirements.txt          # Python 의존성
├── Dockerfile               # Docker 이미지 빌드 파일
├── docker-compose.yml       # Docker Compose 설정
├── .dockerignore            # Docker 빌드 제외 파일
├── cloud_deploy/            # 클라우드 배포 스크립트
│   ├── aws_deploy.sh        # AWS ECS 배포
│   ├── azure_deploy.sh      # Azure Container Instances 배포
│   └── gcp_deploy.sh        # GCP Cloud Run 배포
└── README.md                # 이 문서
```

## 🚀 주요 기능

### 1. 오류 처리 메서드

#### `handle_auth_error()`
- API 인증 오류 처리
- API 키 재확인
- JWT 토큰 자동 재생성
- 최대 3회 재시도

#### `handle_network_error()`
- 네트워크 오류 처리
- 지수 백오프 재시도 (1초, 2초, 4초)
- 최대 3회 재시도
- 자동 복구 시도

#### `handle_data_error()`
- 데이터 오류 처리
- 데이터 검증 로직
- 이전 정상 데이터 자동 사용
- 폴백 데이터 관리

### 2. 로깅 시스템
- 오류 유형 기록
- 발생 시간 기록
- 재시도 횟수 기록
- 심각도별 로그 레벨

### 3. 알림 시스템
- 텔레그램 알림
- 이메일 알림 (심각한 오류만)
- 알림 우선순위 관리

## 🐳 Docker 배포

### 1. 로컬 빌드 및 실행

```bash
# 이미지 빌드
docker build -t error-handler-service:latest .

# 컨테이너 실행
docker run -d \
  --name error-handler \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  -v $(pwd)/logs:/app/logs \
  error-handler-service:latest
```

### 2. Docker Compose 사용

```bash
# 환경 변수 설정 (.env 파일)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key

# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs -f
```

## ☁️ 클라우드 배포

### AWS ECS 배포

```bash
# 환경 변수 설정
export AWS_REGION=ap-northeast-2
export AWS_ACCOUNT_ID=your_account_id
export ECS_CLUSTER_NAME=your_cluster_name

# 배포 실행
chmod +x cloud_deploy/aws_deploy.sh
./cloud_deploy/aws_deploy.sh
```

### Azure Container Instances 배포

```bash
# 환경 변수 설정
export AZURE_RESOURCE_GROUP=your_resource_group
export AZURE_CONTAINER_NAME=error-handler-service
export AZURE_ACR_NAME=your_acr_name

# 배포 실행
chmod +x cloud_deploy/azure_deploy.sh
./cloud_deploy/azure_deploy.sh
```

### GCP Cloud Run 배포

```bash
# 환경 변수 설정
export GCP_PROJECT_ID=your_project_id
export GCP_SERVICE_NAME=error-handler-service

# 배포 실행
chmod +x cloud_deploy/gcp_deploy.sh
./cloud_deploy/gcp_deploy.sh
```

## 📋 환경 변수

### 필수 환경 변수
- `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰
- `TELEGRAM_CHAT_ID`: 텔레그램 채팅 ID
- `UPBIT_ACCESS_KEY`: 업비트 Access Key
- `UPBIT_SECRET_KEY`: 업비트 Secret Key

### 선택 환경 변수
- `SMTP_SERVER`: SMTP 서버 주소
- `SMTP_PORT`: SMTP 포트 (기본값: 587)
- `EMAIL_USERNAME`: 이메일 주소
- `EMAIL_PASSWORD`: 이메일 비밀번호
- `EMAIL_TO`: 수신자 이메일
- `LOG_FILE`: 로그 파일 경로 (기본값: logs/error_handler.log)

## 💻 사용 예시

```python
from error_handler import ErrorHandler, ErrorType, ErrorSeverity

# 오류 처리자 초기화
error_handler = ErrorHandler(
    telegram_bot_token="your_token",
    telegram_chat_id="your_chat_id"
)

# 인증 오류 처리
try:
    # API 호출
    pass
except Exception as e:
    error_handler.handle_auth_error(
        e,
        context={'api_key': 'your_key', 'secret_key': 'your_secret'}
    )

# 네트워크 오류 처리
def api_call():
    # API 호출 로직
    pass

try:
    result = api_call()
except Exception as e:
    error_handler.handle_network_error(
        e,
        context={'retry_func': api_call, 'args': [], 'kwargs': {}}
    )

# 데이터 오류 처리
def validate_data(data):
    # 데이터 검증 로직
    return True

try:
    # 데이터 처리
    pass
except Exception as e:
    recovered_data = error_handler.handle_data_error(
        e,
        context={'data': data, 'validation_func': validate_data},
        data_key='price_data'
    )
```

## 📊 모니터링

### 오류 요약 조회

```python
summary = error_handler.get_error_summary()
print(f"총 오류: {summary['total_errors']}")
print(f"복구 성공: {summary['recovered_errors']}")
print(f"복구율: {summary['recovery_rate']:.2f}%")
```

## ⚠️ 주의사항

1. **보안**: API 키는 환경 변수로 관리하고 절대 코드에 하드코딩하지 마세요.
2. **모니터링**: 정기적으로 오류 로그를 확인하세요.
3. **알림 설정**: 중요한 오류에 대한 알림을 적절히 설정하세요.
4. **리소스 관리**: 오류 기록이 너무 많아지지 않도록 주기적으로 정리하세요.

## 📚 관련 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [AWS ECS 문서](https://docs.aws.amazon.com/ecs/)
- [Azure Container Instances 문서](https://docs.microsoft.com/azure/container-instances/)
- [GCP Cloud Run 문서](https://cloud.google.com/run/docs)

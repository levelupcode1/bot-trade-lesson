#!/bin/bash
# Google Cloud Platform Cloud Run 배포 스크립트

set -e

echo "🚀 GCP Cloud Run 배포 시작..."

# 환경 변수 확인
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "❌ GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다."
    exit 1
fi

if [ -z "$GCP_SERVICE_NAME" ]; then
    echo "❌ GCP_SERVICE_NAME 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# GCP 프로젝트 설정
echo "🔧 GCP 프로젝트 설정 중..."
gcloud config set project $GCP_PROJECT_ID

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME:latest .

# 이미지 푸시
echo "📤 이미지 푸시 중..."
docker push gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME:latest

# Cloud Run 배포
echo "🔄 Cloud Run 배포 중..."
gcloud run deploy $GCP_SERVICE_NAME \
    --image gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME:latest \
    --platform managed \
    --region asia-northeast3 \
    --allow-unauthenticated \
    --set-env-vars \
        TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN,\
        TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID,\
        UPBIT_ACCESS_KEY=$UPBIT_ACCESS_KEY,\
        UPBIT_SECRET_KEY=$UPBIT_SECRET_KEY \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1

echo "✅ 배포 완료!"

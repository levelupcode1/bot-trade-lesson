#!/bin/bash
# Azure Container Instances 배포 스크립트

set -e

echo "🚀 Azure Container Instances 배포 시작..."

# 환경 변수 확인
if [ -z "$AZURE_RESOURCE_GROUP" ]; then
    echo "❌ AZURE_RESOURCE_GROUP 환경 변수가 설정되지 않았습니다."
    exit 1
fi

if [ -z "$AZURE_CONTAINER_NAME" ]; then
    echo "❌ AZURE_CONTAINER_NAME 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# Azure 로그인 확인
echo "🔐 Azure 로그인 확인 중..."
az account show > /dev/null 2>&1 || {
    echo "❌ Azure에 로그인되지 않았습니다. 'az login'을 실행하세요."
    exit 1
}

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t error-handler-service:latest .

# ACR 로그인 (ACR 사용 시)
if [ ! -z "$AZURE_ACR_NAME" ]; then
    echo "📦 ACR 로그인 중..."
    az acr login --name $AZURE_ACR_NAME
    
    # 이미지 태깅 및 푸시
    echo "🏷️ 이미지 태깅 및 푸시 중..."
    docker tag error-handler-service:latest $AZURE_ACR_NAME.azurecr.io/error-handler-service:latest
    docker push $AZURE_ACR_NAME.azurecr.io/error-handler-service:latest
    IMAGE_NAME="$AZURE_ACR_NAME.azurecr.io/error-handler-service:latest"
else
    IMAGE_NAME="error-handler-service:latest"
fi

# Container Instance 생성/업데이트
echo "🔄 Container Instance 배포 중..."
az container create \
    --resource-group $AZURE_RESOURCE_GROUP \
    --name $AZURE_CONTAINER_NAME \
    --image $IMAGE_NAME \
    --cpu 1 \
    --memory 1 \
    --registry-login-server $AZURE_ACR_NAME.azurecr.io \
    --registry-username $AZURE_ACR_USERNAME \
    --registry-password $AZURE_ACR_PASSWORD \
    --environment-variables \
        TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN \
        TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID \
        UPBIT_ACCESS_KEY=$UPBIT_ACCESS_KEY \
        UPBIT_SECRET_KEY=$UPBIT_SECRET_KEY \
    --restart-policy Always \
    --os-type Linux

echo "✅ 배포 완료!"

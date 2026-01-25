#!/bin/bash
# AWS ECS 배포 스크립트

set -e

echo "🚀 AWS ECS 배포 시작..."

# 환경 변수 확인
if [ -z "$AWS_REGION" ]; then
    echo "❌ AWS_REGION 환경 변수가 설정되지 않았습니다."
    exit 1
fi

if [ -z "$ECS_CLUSTER_NAME" ]; then
    echo "❌ ECS_CLUSTER_NAME 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# ECR 로그인
echo "📦 ECR 로그인 중..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t error-handler-service:latest .

# 이미지 태깅
echo "🏷️ 이미지 태깅 중..."
docker tag error-handler-service:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/error-handler-service:latest

# 이미지 푸시
echo "📤 이미지 푸시 중..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/error-handler-service:latest

# ECS 서비스 업데이트
echo "🔄 ECS 서비스 업데이트 중..."
aws ecs update-service \
    --cluster $ECS_CLUSTER_NAME \
    --service error-handler-service \
    --force-new-deployment \
    --region $AWS_REGION

echo "✅ 배포 완료!"

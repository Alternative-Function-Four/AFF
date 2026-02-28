#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PREFIX="Aff"
DEFAULT_ENVIRONMENT="preview-$(whoami)"
ENVIRONMENT="${1:-$DEFAULT_ENVIRONMENT}"

if [[ $# -gt 0 ]]; then
  shift
fi

API_BASE_URL=""
AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-southeast-1}}"

usage() {
  cat <<USAGE
Usage: ./scripts/deploy.sh [environment] --api-base-url <https-url> [--region <aws-region>]

Examples:
  ./scripts/deploy.sh preview-andrew --api-base-url https://d12345.cloudfront.net
  ./scripts/deploy.sh prod --api-base-url https://api.example.com --region ap-southeast-1
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-base-url)
      API_BASE_URL="${2:-}"
      shift 2
      ;;
    --region)
      AWS_REGION="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$API_BASE_URL" ]]; then
  echo "--api-base-url is required."
  usage
  exit 1
fi

API_BASE_URL="${API_BASE_URL%/}"

if [[ ! "$API_BASE_URL" =~ ^https:// ]]; then
  echo "API base URL must start with https:// to avoid browser mixed-content blocking."
  exit 1
fi

if [[ "$API_BASE_URL" =~ ^https://(localhost|127\.0\.0\.1)(:|/|$) ]]; then
  echo "API base URL cannot point to localhost/127.0.0.1 for deployed frontend."
  exit 1
fi

echo "Validating AWS credentials..."
ACCOUNT_ID=$(aws sts get-caller-identity --region "$AWS_REGION" --query Account --output text)

echo "Using AWS account: $ACCOUNT_ID"
echo "Using AWS region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo "API base URL for frontend build: $API_BASE_URL"

echo "Installing and building CDK infra..."
cd "$ROOT_DIR/infra"
npm install --no-progress
npm run build

echo "Bootstrapping CDK (idempotent)..."
npx cdk bootstrap "aws://$ACCOUNT_ID/$AWS_REGION" --progress events

echo "Deploying backend HTTPS edge stack..."
npx cdk deploy "${APP_PREFIX}BackendEdge-${ENVIRONMENT}" \
  --context "environment=${ENVIRONMENT}" \
  --context "buildPath=../clients/app/dist" \
  --require-approval never \
  --progress events

echo "Building Expo web bundle with deploy-time API URL..."
cd "$ROOT_DIR/clients/app"
EXPO_PUBLIC_API_BASE_URL="$API_BASE_URL" npm run build

echo "Deploying frontend stack..."
cd "$ROOT_DIR/infra"
npx cdk deploy "${APP_PREFIX}Frontend-${ENVIRONMENT}" \
  --context "environment=${ENVIRONMENT}" \
  --context "buildPath=../clients/app/dist" \
  --require-approval never \
  --progress events

FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name "${APP_PREFIX}Frontend-${ENVIRONMENT}" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
  --output text)

API_EDGE_URL=$(aws cloudformation describe-stacks \
  --stack-name "${APP_PREFIX}BackendEdge-${ENVIRONMENT}" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEdgeUrl'].OutputValue" \
  --output text)

echo
echo "Deployment complete."
echo "Frontend URL: $FRONTEND_URL"
echo "Backend edge URL: $API_EDGE_URL"
echo "Frontend was built with API base URL: $API_BASE_URL"

#!/bin/bash

# Configuration
SERVICE_NAME="stock-analysis-bot"
REGION="asia-east1"
JOB_NAME="stock-bot-daily-job"
SCHEDULE="0 6 * * 1-5"
TIMEZONE="Asia/Taipei"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Starting Deployment for ${SERVICE_NAME} ===${NC}"

# 1. Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud command not found.${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 2. Source .env variables for deployment
echo "Reading .env file..."
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}Error: .env file not found.${NC}"
    exit 1
fi

# 3. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars FINMIND_API_TOKEN="$FINMIND_API_TOKEN" \
    --set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY" \
    --set-env-vars LINE_CHANNEL_ACCESS_TOKEN="$LINE_CHANNEL_ACCESS_TOKEN" \
    --set-env-vars LINE_CHANNEL_SECRET="$LINE_CHANNEL_SECRET" \
    --set-env-vars LINE_USER_ID="$LINE_USER_ID" \
    --set-env-vars GOOGLE_SHEETS_CREDENTIALS_FILE="$GOOGLE_SHEETS_CREDENTIALS_FILE" \
    --set-env-vars GOOGLE_SHEET_URL="$GOOGLE_SHEET_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

# 4. Get Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo -e "${GREEN}Service deployed at: ${SERVICE_URL}${NC}"

# 5. Set up Cloud Scheduler
echo "Creating/Updating Cloud Scheduler Job..."

# Check if job exists
if gcloud scheduler jobs describe $JOB_NAME --location $REGION &> /dev/null; then
    echo "Updating existing job..."
    gcloud scheduler jobs update http $JOB_NAME \
        --location $REGION \
        --schedule "$SCHEDULE" \
        --uri "${SERVICE_URL}/run_analysis" \
        --http-method POST \
        --time-zone "$TIMEZONE"
else
    echo "Creating new job..."
    gcloud scheduler jobs create http $JOB_NAME \
        --location $REGION \
        --schedule "$SCHEDULE" \
        --uri "${SERVICE_URL}/run_analysis" \
        --http-method POST \
        --time-zone "$TIMEZONE"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo "Webhook URL for LINE: ${SERVICE_URL}/callback"
echo "Scheduler: ${SCHEDULE} (Approx 6:00 AM Mon-Fri)"

#!/bin/bash

SERVICE_NAME="liveraid-service"
REGION="europe-west3"
PROJECT_ID="tactile-vial-468307-d3"
NETWORK="liveraid-network"
SUBNET="liveraid-network-subnet"

# gcloud deploy komutu
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --set-secrets="DB_USER=DB_USER:latest,DB_PASS=DB_PASS:latest,DB_NAME=DB_NAME:latest,CLOUD_SQL_CONNECTION_NAME=CLOUD_SQL_CONNECTION_NAME:latest,GOOGLE_AI_API_KEY=GOOGLE_AI_API_KEY:latest,FLASK_SECRET_KEY=FLASK_SECRET_KEY:latest" \
  --network=$NETWORK \
  --subnet=$SUBNET
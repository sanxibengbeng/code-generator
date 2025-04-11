#!/bin/bash
set -e

# Default deployment ID if not provided
DEPLOYMENT_ID=${1:-"default"}

echo "Deploying with deployment ID: $DEPLOYMENT_ID"

# Install dependencies
npm install

# Deploy the stack with the specified deployment ID
cdk deploy --require-approval never --context deploymentId=$DEPLOYMENT_ID

echo "Deployment completed successfully for deployment ID: $DEPLOYMENT_ID!"

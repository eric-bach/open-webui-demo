#!/usr/bin/env bash

# Script to deploy the example-apis backend infrastructure
# Usage: 
#   ./deploy.sh [env_name]
#   ENV_NAME=staging ./deploy.sh

set -e  # Exit on any error

# Set environment name from parameter or environment variable, default to 'dev'
ENV_NAME=${1:-${ENV_NAME:-dev}}

echo "🚀 Deploying open-webui backend for environment: $ENV_NAME and profile: observability2"

ENV_NAME=$ENV_NAME cdk deploy --all --profile observability2

#!/bin/bash

# AI News Agent Lambda Function Deployment Script
# This script deploys the Lambda function code to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
LAMBDA_ZIP="$DIST_DIR/ai-news-agent-lambda.zip"

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [options]"
    echo ""
    echo "Environments:"
    echo "  dev   - Development environment"
    echo "  prod  - Production environment"
    echo ""
    echo "Options:"
    echo "  -b, --build     Build package before deploying"
    echo "  -w, --wait      Wait for deployment to complete"
    echo "  -t, --test      Test function after deployment"
    echo "  -v, --verbose   Verbose output"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Deploy to dev environment"
    echo "  $0 prod --build           # Build and deploy to prod"
    echo "  $0 dev --build --test     # Build, deploy, and test"
}

# Check if correct number of arguments
if [ $# -lt 1 ]; then
    print_error "Environment argument required"
    show_usage
    exit 1
fi

ENVIRONMENT=$1
shift

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    show_usage
    exit 1
fi

# Parse command line arguments
BUILD_PACKAGE=false
WAIT_FOR_COMPLETION=false
TEST_FUNCTION=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            BUILD_PACKAGE=true
            shift
            ;;
        -w|--wait)
            WAIT_FOR_COMPLETION=true
            shift
            ;;
        -t|--test)
            TEST_FUNCTION=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set function name based on environment
FUNCTION_NAME="ai-news-agent-${ENVIRONMENT}"

print_status "Starting Lambda deployment for $ENVIRONMENT environment"

# Build package if requested
if [ "$BUILD_PACKAGE" = true ]; then
    print_status "Building Lambda package"
    if [ "$VERBOSE" = true ]; then
        "$SCRIPT_DIR/build-lambda.sh" --verbose
    else
        "$SCRIPT_DIR/build-lambda.sh"
    fi
fi

# Check if deployment package exists
if [ ! -f "$LAMBDA_ZIP" ]; then
    print_error "Lambda deployment package not found: $LAMBDA_ZIP"
    print_error "Run with --build option or build the package first using:"
    print_error "  ./scripts/build-lambda.sh"
    exit 1
fi

# Check AWS CLI is available and configured
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install and configure AWS CLI"
    exit 1
fi

# Verify AWS credentials
print_status "Verifying AWS credentials"
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS credentials not configured or invalid"
    print_error "Please configure AWS CLI using: aws configure"
    exit 1
fi

# Check if Lambda function exists
print_status "Checking if Lambda function exists: $FUNCTION_NAME"
if aws lambda get-function --function-name "$FUNCTION_NAME" > /dev/null 2>&1; then
    print_status "Lambda function exists, updating code"
    
    # Update function code
    print_status "Uploading new code to Lambda function"
    if [ "$VERBOSE" = true ]; then
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file "fileb://$LAMBDA_ZIP" \
            --output table
    else
        UPDATE_RESULT=$(aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file "fileb://$LAMBDA_ZIP" \
            --output json)
    fi
    
    print_success "Lambda function code updated successfully"
    
    # Wait for update to complete if requested
    if [ "$WAIT_FOR_COMPLETION" = true ]; then
        print_status "Waiting for function update to complete"
        aws lambda wait function-updated --function-name "$FUNCTION_NAME"
        print_success "Function update completed"
    fi
    
else
    print_error "Lambda function '$FUNCTION_NAME' not found"
    print_error "Please deploy the infrastructure first using Terraform:"
    print_error "  cd terraform && ./deploy.sh $ENVIRONMENT apply"
    exit 1
fi

# Update function configuration if needed
print_status "Updating function configuration"
aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --timeout 300 \
    --memory-size 512 \
    --runtime python3.11 \
    --handler lambda_function.lambda_handler \
    --output table > /dev/null 2>&1

print_success "Function configuration updated"

# Get function information
print_status "Getting function information"
FUNCTION_INFO=$(aws lambda get-function --function-name "$FUNCTION_NAME" --output json)
FUNCTION_ARN=$(echo "$FUNCTION_INFO" | jq -r '.Configuration.FunctionArn')
LAST_MODIFIED=$(echo "$FUNCTION_INFO" | jq -r '.Configuration.LastModified')
CODE_SIZE=$(echo "$FUNCTION_INFO" | jq -r '.Configuration.CodeSize')

print_success "Deployment completed successfully!"
echo ""
print_status "Function Details:"
echo "  Name: $FUNCTION_NAME"
echo "  ARN: $FUNCTION_ARN"
echo "  Last Modified: $LAST_MODIFIED"
echo "  Code Size: $CODE_SIZE bytes"

# Test function if requested
if [ "$TEST_FUNCTION" = true ]; then
    print_status "Testing Lambda function"
    
    # Create test event
    TEST_EVENT='{
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {}
    }'
    
    print_status "Invoking function with test event"
    INVOKE_RESULT=$(aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --payload "$TEST_EVENT" \
        --output json \
        /tmp/lambda-response.json)
    
    STATUS_CODE=$(echo "$INVOKE_RESULT" | jq -r '.StatusCode')
    
    if [ "$STATUS_CODE" = "200" ]; then
        print_success "Function invocation successful"
        if [ "$VERBOSE" = true ]; then
            print_status "Function response:"
            cat /tmp/lambda-response.json
        fi
    else
        print_error "Function invocation failed with status code: $STATUS_CODE"
        if [ -f /tmp/lambda-response.json ]; then
            print_error "Error response:"
            cat /tmp/lambda-response.json
        fi
        exit 1
    fi
    
    # Clean up
    rm -f /tmp/lambda-response.json
fi

# Show logs command
echo ""
print_status "To view function logs, run:"
echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
print_status "To invoke the function manually, run:"
echo "  aws lambda invoke --function-name $FUNCTION_NAME --payload '{}' response.json"
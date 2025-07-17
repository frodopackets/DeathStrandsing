#!/bin/bash

# AI News Agent Full Deployment Script
# This script handles complete deployment including infrastructure and Lambda code

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [options]"
    echo ""
    echo "Environments:"
    echo "  dev   - Development environment"
    echo "  prod  - Production environment"
    echo ""
    echo "Options:"
    echo "  -i, --infra-only    Deploy infrastructure only (no Lambda code)"
    echo "  -c, --code-only     Deploy Lambda code only (no infrastructure)"
    echo "  -f, --force         Force deployment without confirmation"
    echo "  -t, --test          Test deployment after completion"
    echo "  -v, --verbose       Verbose output"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Full deployment to dev"
    echo "  $0 prod --force           # Force deployment to prod"
    echo "  $0 dev --infra-only       # Deploy only infrastructure"
    echo "  $0 dev --code-only        # Deploy only Lambda code"
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
INFRA_ONLY=false
CODE_ONLY=false
FORCE_DEPLOY=false
TEST_DEPLOYMENT=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--infra-only)
            INFRA_ONLY=true
            shift
            ;;
        -c|--code-only)
            CODE_ONLY=true
            shift
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -t|--test)
            TEST_DEPLOYMENT=true
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

# Validate conflicting options
if [ "$INFRA_ONLY" = true ] && [ "$CODE_ONLY" = true ]; then
    print_error "Cannot specify both --infra-only and --code-only"
    exit 1
fi

print_status "Starting full deployment for $ENVIRONMENT environment"

# Confirmation for production
if [ "$ENVIRONMENT" = "prod" ] && [ "$FORCE_DEPLOY" = false ]; then
    print_warning "You are about to deploy to PRODUCTION environment!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_status "Deployment cancelled"
        exit 0
    fi
fi

# Step 1: Deploy Infrastructure (unless code-only)
if [ "$CODE_ONLY" = false ]; then
    print_status "Step 1: Deploying infrastructure with Terraform"
    
    cd "$PROJECT_ROOT/terraform"
    
    # Initialize Terraform
    print_status "Initializing Terraform"
    if [ "$VERBOSE" = true ]; then
        ./deploy.sh "$ENVIRONMENT" init
    else
        ./deploy.sh "$ENVIRONMENT" init > /dev/null 2>&1
    fi
    
    # Plan deployment
    print_status "Planning infrastructure deployment"
    if [ "$VERBOSE" = true ]; then
        ./deploy.sh "$ENVIRONMENT" plan
    else
        ./deploy.sh "$ENVIRONMENT" plan > /dev/null 2>&1
    fi
    
    # Apply deployment
    print_status "Applying infrastructure deployment"
    if [ "$VERBOSE" = true ]; then
        ./deploy.sh "$ENVIRONMENT" apply
    else
        # For non-verbose mode, we still need to see the apply output for confirmation
        ./deploy.sh "$ENVIRONMENT" apply
    fi
    
    print_success "Infrastructure deployment completed"
    
    # Get outputs
    print_status "Getting Terraform outputs"
    TERRAFORM_OUTPUTS=$(terraform output -json)
    LAMBDA_FUNCTION_NAME=$(echo "$TERRAFORM_OUTPUTS" | jq -r '.lambda_function_name.value')
    SNS_TOPIC_ARN=$(echo "$TERRAFORM_OUTPUTS" | jq -r '.sns_topic_arn.value')
    
    print_status "Infrastructure Details:"
    echo "  Lambda Function: $LAMBDA_FUNCTION_NAME"
    echo "  SNS Topic: $SNS_TOPIC_ARN"
    
    cd "$PROJECT_ROOT"
fi

# Step 2: Deploy Lambda Code (unless infra-only)
if [ "$INFRA_ONLY" = false ]; then
    print_status "Step 2: Building and deploying Lambda function code"
    
    # Build and deploy Lambda code
    if [ "$VERBOSE" = true ]; then
        "$SCRIPT_DIR/deploy-lambda.sh" "$ENVIRONMENT" --build --wait --verbose
    else
        "$SCRIPT_DIR/deploy-lambda.sh" "$ENVIRONMENT" --build --wait
    fi
    
    print_success "Lambda code deployment completed"
fi

# Step 3: Test Deployment (if requested)
if [ "$TEST_DEPLOYMENT" = true ]; then
    print_status "Step 3: Testing deployment"
    
    # Test Lambda function
    print_status "Testing Lambda function"
    if [ "$VERBOSE" = true ]; then
        "$SCRIPT_DIR/deploy-lambda.sh" "$ENVIRONMENT" --test --verbose
    else
        "$SCRIPT_DIR/deploy-lambda.sh" "$ENVIRONMENT" --test
    fi
    
    # Test SNS topic (if we have the ARN)
    if [ -n "$SNS_TOPIC_ARN" ]; then
        print_status "Testing SNS topic"
        TEST_MESSAGE="Test message from AI News Agent deployment script - $(date)"
        aws sns publish \
            --topic-arn "$SNS_TOPIC_ARN" \
            --message "$TEST_MESSAGE" \
            --subject "AI News Agent Deployment Test" > /dev/null 2>&1
        print_success "Test message sent to SNS topic"
    fi
    
    print_success "Deployment testing completed"
fi

print_success "Full deployment completed successfully!"

# Show summary
echo ""
print_status "Deployment Summary:"
echo "  Environment: $ENVIRONMENT"
if [ "$INFRA_ONLY" = false ] && [ "$CODE_ONLY" = false ]; then
    echo "  Type: Full deployment (infrastructure + code)"
elif [ "$INFRA_ONLY" = true ]; then
    echo "  Type: Infrastructure only"
elif [ "$CODE_ONLY" = true ]; then
    echo "  Type: Lambda code only"
fi

# Show next steps
echo ""
print_status "Next Steps:"
echo "1. Check CloudWatch logs for function execution:"
echo "   aws logs tail /aws/lambda/ai-news-agent-$ENVIRONMENT --follow"
echo ""
echo "2. Monitor SNS topic subscriptions:"
echo "   aws sns list-subscriptions-by-topic --topic-arn [SNS_TOPIC_ARN]"
echo ""
echo "3. Test the EventBridge schedule:"
echo "   aws events list-rules --name-prefix ai-news-agent-$ENVIRONMENT"
echo ""
echo "4. View Terraform outputs:"
echo "   cd terraform && terraform output"

if [ "$ENVIRONMENT" = "dev" ]; then
    echo ""
    print_status "Development Environment Notes:"
    echo "- Function runs every 2 hours for testing"
    echo "- Uses Nova Lite model for cost savings"
    echo "- Logs retained for 7 days"
    echo "- Only one email subscriber configured"
fi

if [ "$ENVIRONMENT" = "prod" ]; then
    echo ""
    print_status "Production Environment Notes:"
    echo "- Function runs daily at scheduled time"
    echo "- Uses Nova Pro model for best quality"
    echo "- Logs retained for 30 days"
    echo "- All email subscribers configured"
fi
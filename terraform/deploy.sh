#!/bin/bash

# AI News Agent Terraform Deployment Script
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh dev plan
# Example: ./deploy.sh prod apply

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [action]"
    echo ""
    echo "Environments:"
    echo "  dev   - Development environment"
    echo "  prod  - Production environment"
    echo ""
    echo "Actions:"
    echo "  init     - Initialize Terraform"
    echo "  plan     - Plan deployment"
    echo "  apply    - Apply deployment"
    echo "  destroy  - Destroy infrastructure"
    echo "  output   - Show outputs"
    echo "  validate - Validate configuration"
    echo "  fmt      - Format Terraform files"
    echo ""
    echo "Examples:"
    echo "  $0 dev init"
    echo "  $0 dev plan"
    echo "  $0 prod apply"
    echo "  $0 dev destroy"
}

# Check if correct number of arguments
if [ $# -ne 2 ]; then
    print_error "Invalid number of arguments"
    show_usage
    exit 1
fi

ENVIRONMENT=$1
ACTION=$2

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    show_usage
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(init|plan|apply|destroy|output|validate|fmt)$ ]]; then
    print_error "Invalid action: $ACTION"
    show_usage
    exit 1
fi

# Set environment-specific variables
BACKEND_CONFIG="backend-${ENVIRONMENT}.hcl"
VAR_FILE="environments/${ENVIRONMENT}.tfvars"

# Check if required files exist
if [ ! -f "$BACKEND_CONFIG" ]; then
    print_error "Backend config file not found: $BACKEND_CONFIG"
    exit 1
fi

if [ ! -f "$VAR_FILE" ]; then
    print_error "Variable file not found: $VAR_FILE"
    exit 1
fi

print_status "Starting Terraform $ACTION for $ENVIRONMENT environment"

# Execute the requested action
case $ACTION in
    "init")
        print_status "Initializing Terraform with backend config: $BACKEND_CONFIG"
        terraform init -backend-config="$BACKEND_CONFIG" -reconfigure
        print_success "Terraform initialization completed"
        ;;
    
    "plan")
        print_status "Planning deployment with variables: $VAR_FILE"
        terraform plan -var-file="$VAR_FILE" -out="${ENVIRONMENT}.tfplan"
        print_success "Terraform plan completed. Plan saved as ${ENVIRONMENT}.tfplan"
        ;;
    
    "apply")
        print_status "Applying deployment with variables: $VAR_FILE"
        if [ -f "${ENVIRONMENT}.tfplan" ]; then
            print_status "Using existing plan file: ${ENVIRONMENT}.tfplan"
            terraform apply "${ENVIRONMENT}.tfplan"
        else
            print_warning "No plan file found. Running apply with auto-approve disabled."
            terraform apply -var-file="$VAR_FILE"
        fi
        print_success "Terraform apply completed"
        ;;
    
    "destroy")
        print_warning "This will destroy all infrastructure for $ENVIRONMENT environment!"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            print_status "Destroying infrastructure with variables: $VAR_FILE"
            terraform destroy -var-file="$VAR_FILE"
            print_success "Terraform destroy completed"
        else
            print_status "Destroy operation cancelled"
        fi
        ;;
    
    "output")
        print_status "Showing Terraform outputs"
        terraform output
        ;;
    
    "validate")
        print_status "Validating Terraform configuration"
        terraform validate
        print_success "Terraform configuration is valid"
        ;;
    
    "fmt")
        print_status "Formatting Terraform files"
        terraform fmt -recursive
        print_success "Terraform files formatted"
        ;;
esac

print_success "Operation completed successfully!"
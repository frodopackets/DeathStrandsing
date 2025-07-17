#!/bin/bash

# AI News Agent Lambda Deployment Package Build Script
# This script builds a deployment package for the AWS Lambda function

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
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
LAMBDA_ZIP="$DIST_DIR/ai-news-agent-lambda.zip"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
LAMBDA_REQUIREMENTS_FILE="$PROJECT_ROOT/requirements-lambda.txt"
SRC_DIR="$PROJECT_ROOT/src"

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -c, --clean     Clean build directory before building"
    echo "  -d, --dev       Include development dependencies"
    echo "  -v, --verbose   Verbose output"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build production package"
    echo "  $0 --clean           # Clean build and create package"
    echo "  $0 --dev --verbose   # Build with dev dependencies and verbose output"
}

# Parse command line arguments
CLEAN_BUILD=false
INCLUDE_DEV=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            CLEAN_BUILD=true
            shift
            ;;
        -d|--dev)
            INCLUDE_DEV=true
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

# Function to run commands with optional verbose output
run_command() {
    if [ "$VERBOSE" = true ]; then
        "$@"
    else
        "$@" > /dev/null 2>&1
    fi
}

print_status "Starting Lambda deployment package build"

# Check if we're in WSL and have the virtual environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    print_error "Virtual environment not found at $PROJECT_ROOT/venv"
    print_error "Please create and activate the virtual environment first"
    exit 1
fi

# Clean build directory if requested
if [ "$CLEAN_BUILD" = true ]; then
    print_status "Cleaning build directory"
    rm -rf "$BUILD_DIR"
    rm -rf "$DIST_DIR"
fi

# Create build and dist directories
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

print_status "Installing Python dependencies"

# Create a temporary requirements file for production
TEMP_REQUIREMENTS="$BUILD_DIR/requirements-lambda.txt"

if [ "$INCLUDE_DEV" = true ]; then
    print_status "Including development dependencies"
    cp "$REQUIREMENTS_FILE" "$TEMP_REQUIREMENTS"
else
    print_status "Using production dependencies only"
    # Use Lambda-specific requirements file if it exists, otherwise filter main requirements
    if [ -f "$LAMBDA_REQUIREMENTS_FILE" ]; then
        cp "$LAMBDA_REQUIREMENTS_FILE" "$TEMP_REQUIREMENTS"
    else
        # Filter out development dependencies from main requirements file
        grep -v -E "^(pytest|black|flake8|mypy)" "$REQUIREMENTS_FILE" > "$TEMP_REQUIREMENTS"
    fi
fi

# Install dependencies to build directory using WSL and virtual environment
print_status "Installing dependencies to build directory"
cd "$PROJECT_ROOT"

# Use WSL with virtual environment to install dependencies
if [ "$VERBOSE" = true ]; then
    wsl bash -c "source venv/bin/activate && pip install -r $TEMP_REQUIREMENTS -t $BUILD_DIR --no-deps --upgrade"
else
    wsl bash -c "source venv/bin/activate && pip install -r $TEMP_REQUIREMENTS -t $BUILD_DIR --no-deps --upgrade" > /dev/null 2>&1
fi

print_success "Dependencies installed successfully"

# Copy source code to build directory
print_status "Copying source code"
cp -r "$SRC_DIR"/* "$BUILD_DIR/"

# Create the main Lambda handler file at the root level
print_status "Creating Lambda handler entry point"
cat > "$BUILD_DIR/lambda_function.py" << 'EOF'
"""
Main Lambda handler entry point for AI News Agent
"""
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aws_lambda.handler import lambda_handler

# Export the handler function
__all__ = ['lambda_handler']
EOF

# Create a simple test to verify the package
print_status "Creating package verification test"
cat > "$BUILD_DIR/test_package.py" << 'EOF'
"""
Simple test to verify the Lambda package is correctly structured
"""
import sys
import importlib.util

def test_imports():
    """Test that all required modules can be imported"""
    required_modules = [
        'lambda_function',
        'models.news_article',
        'models.news_summary', 
        'models.agent_config',
        'services.google_news_fetcher',
        'services.strands_ai_summarizer',
        'services.aws_sns_publisher'
    ]
    
    for module_name in required_modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                print(f"ERROR: Module {module_name} not found")
                return False
            print(f"OK: Module {module_name} found")
        except Exception as e:
            print(f"ERROR: Failed to check module {module_name}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
EOF

# Run package verification test
print_status "Verifying package structure"
cd "$BUILD_DIR"
if python3 test_package.py; then
    print_success "Package structure verification passed"
else
    print_error "Package structure verification failed"
    exit 1
fi

# Remove test file and other unnecessary files
rm -f test_package.py
find "$BUILD_DIR" -name "*.pyc" -delete
find "$BUILD_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# Create the deployment ZIP file
print_status "Creating deployment ZIP file"
cd "$BUILD_DIR"
if [ "$VERBOSE" = true ]; then
    zip -r "$LAMBDA_ZIP" . -x "*.git*" "*.DS_Store*" "*__pycache__*" "*.pyc"
else
    zip -r "$LAMBDA_ZIP" . -x "*.git*" "*.DS_Store*" "*__pycache__*" "*.pyc" > /dev/null 2>&1
fi

# Get file size
ZIP_SIZE=$(du -h "$LAMBDA_ZIP" | cut -f1)
print_success "Lambda deployment package created: $LAMBDA_ZIP ($ZIP_SIZE)"

# Verify ZIP contents
print_status "Verifying ZIP contents"
if [ "$VERBOSE" = true ]; then
    print_status "ZIP file contents:"
    unzip -l "$LAMBDA_ZIP" | head -20
    echo "..."
    echo "Total files: $(unzip -l "$LAMBDA_ZIP" | tail -1 | awk '{print $2}')"
fi

# Check if ZIP is within Lambda limits (50MB compressed, 250MB uncompressed)
ZIP_SIZE_BYTES=$(stat -f%z "$LAMBDA_ZIP" 2>/dev/null || stat -c%s "$LAMBDA_ZIP" 2>/dev/null)
MAX_SIZE_BYTES=$((50 * 1024 * 1024))  # 50MB

if [ "$ZIP_SIZE_BYTES" -gt "$MAX_SIZE_BYTES" ]; then
    print_warning "ZIP file size ($ZIP_SIZE) exceeds AWS Lambda limit (50MB)"
    print_warning "Consider optimizing dependencies or using Lambda layers"
else
    print_success "ZIP file size ($ZIP_SIZE) is within AWS Lambda limits"
fi

print_success "Lambda deployment package build completed successfully!"
print_status "Package location: $LAMBDA_ZIP"
print_status "Package size: $ZIP_SIZE"

# Provide next steps
echo ""
print_status "Next steps:"
echo "1. Upload the package to AWS Lambda using the AWS CLI:"
echo "   aws lambda update-function-code --function-name ai-news-agent-dev --zip-file fileb://$LAMBDA_ZIP"
echo ""
echo "2. Or use the deployment script:"
echo "   ./scripts/deploy-lambda.sh dev"
echo ""
echo "3. Or update via Terraform:"
echo "   cd terraform && ./deploy.sh dev apply"
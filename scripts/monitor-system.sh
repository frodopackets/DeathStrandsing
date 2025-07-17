#!/bin/bash

# AI News Agent System Monitoring Script
# This script provides comprehensive monitoring and health checks

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
    echo "  -l, --logs      Show recent logs"
    echo "  -m, --metrics   Show key metrics"
    echo "  -c, --costs     Show cost information"
    echo "  -a, --alarms    Show alarm status"
    echo "  -t, --test      Run health tests"
    echo "  -v, --verbose   Verbose output"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Basic health check"
    echo "  $0 prod --metrics         # Show metrics for prod"
    echo "  $0 dev --logs --verbose   # Show logs with verbose output"
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
SHOW_LOGS=false
SHOW_METRICS=false
SHOW_COSTS=false
SHOW_ALARMS=false
RUN_TESTS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        -m|--metrics)
            SHOW_METRICS=true
            shift
            ;;
        -c|--costs)
            SHOW_COSTS=true
            shift
            ;;
        -a|--alarms)
            SHOW_ALARMS=true
            shift
            ;;
        -t|--test)
            RUN_TESTS=true
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

# Set resource names based on environment
FUNCTION_NAME="ai-news-agent-${ENVIRONMENT}"
LOG_GROUP_NAME="/aws/lambda/${FUNCTION_NAME}"
DASHBOARD_NAME="ai-news-agent-${ENVIRONMENT}-dashboard"
COST_DASHBOARD_NAME="ai-news-agent-${ENVIRONMENT}-cost-dashboard"

print_status "AI News Agent System Monitor - $ENVIRONMENT Environment"
echo "=================================================="

# Check AWS CLI availability
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install and configure AWS CLI"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS credentials not configured or invalid"
    exit 1
fi

# Basic Health Check
print_status "Performing basic health checks..."

# Check Lambda function exists and status
print_status "Checking Lambda function: $FUNCTION_NAME"
if LAMBDA_INFO=$(aws lambda get-function --function-name "$FUNCTION_NAME" --output json 2>/dev/null); then
    FUNCTION_STATE=$(echo "$LAMBDA_INFO" | jq -r '.Configuration.State')
    LAST_UPDATE_STATUS=$(echo "$LAMBDA_INFO" | jq -r '.Configuration.LastUpdateStatus')
    RUNTIME=$(echo "$LAMBDA_INFO" | jq -r '.Configuration.Runtime')
    MEMORY_SIZE=$(echo "$LAMBDA_INFO" | jq -r '.Configuration.MemorySize')
    TIMEOUT=$(echo "$LAMBDA_INFO" | jq -r '.Configuration.Timeout')
    
    if [ "$FUNCTION_STATE" = "Active" ] && [ "$LAST_UPDATE_STATUS" = "Successful" ]; then
        print_success "Lambda function is healthy"
        if [ "$VERBOSE" = true ]; then
            echo "  State: $FUNCTION_STATE"
            echo "  Runtime: $RUNTIME"
            echo "  Memory: ${MEMORY_SIZE}MB"
            echo "  Timeout: ${TIMEOUT}s"
        fi
    else
        print_warning "Lambda function may have issues"
        echo "  State: $FUNCTION_STATE"
        echo "  Last Update Status: $LAST_UPDATE_STATUS"
    fi
else
    print_error "Lambda function not found: $FUNCTION_NAME"
fi

# Check SNS topic
print_status "Checking SNS topic..."
if SNS_TOPICS=$(aws sns list-topics --output json 2>/dev/null); then
    TOPIC_ARN=$(echo "$SNS_TOPICS" | jq -r --arg name "ai-news-agent-${ENVIRONMENT}-notifications" '.Topics[] | select(.TopicArn | contains($name)) | .TopicArn')
    if [ -n "$TOPIC_ARN" ]; then
        print_success "SNS topic found: $TOPIC_ARN"
        
        # Check subscriptions
        if SUBSCRIPTIONS=$(aws sns list-subscriptions-by-topic --topic-arn "$TOPIC_ARN" --output json 2>/dev/null); then
            SUB_COUNT=$(echo "$SUBSCRIPTIONS" | jq '.Subscriptions | length')
            CONFIRMED_COUNT=$(echo "$SUBSCRIPTIONS" | jq '[.Subscriptions[] | select(.SubscriptionArn != "PendingConfirmation")] | length')
            print_status "SNS subscriptions: $CONFIRMED_COUNT confirmed out of $SUB_COUNT total"
            
            if [ "$VERBOSE" = true ]; then
                echo "$SUBSCRIPTIONS" | jq -r '.Subscriptions[] | "  \(.Protocol): \(.Endpoint) (\(.SubscriptionArn))"'
            fi
        fi
    else
        print_error "SNS topic not found"
    fi
fi

# Check EventBridge rule
print_status "Checking EventBridge schedule..."
if RULES=$(aws events list-rules --name-prefix "ai-news-agent-${ENVIRONMENT}" --output json 2>/dev/null); then
    RULE_COUNT=$(echo "$RULES" | jq '.Rules | length')
    if [ "$RULE_COUNT" -gt 0 ]; then
        print_success "EventBridge rule(s) found: $RULE_COUNT"
        if [ "$VERBOSE" = true ]; then
            echo "$RULES" | jq -r '.Rules[] | "  \(.Name): \(.ScheduleExpression) (\(.State))"'
        fi
    else
        print_error "No EventBridge rules found"
    fi
fi

# Show recent logs if requested
if [ "$SHOW_LOGS" = true ]; then
    print_status "Fetching recent logs..."
    if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP_NAME" > /dev/null 2>&1; then
        print_status "Recent Lambda execution logs:"
        aws logs tail "$LOG_GROUP_NAME" --since 24h --format short | head -50
    else
        print_warning "Log group not found or no recent logs"
    fi
fi

# Show key metrics if requested
if [ "$SHOW_METRICS" = true ]; then
    print_status "Fetching key metrics (last 24 hours)..."
    
    # Lambda invocations
    if INVOCATIONS=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/Lambda \
        --metric-name Invocations \
        --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
        --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 3600 \
        --statistics Sum \
        --output json 2>/dev/null); then
        
        TOTAL_INVOCATIONS=$(echo "$INVOCATIONS" | jq '[.Datapoints[].Sum] | add // 0')
        print_status "Total invocations (24h): $TOTAL_INVOCATIONS"
    fi
    
    # Lambda errors
    if ERRORS=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/Lambda \
        --metric-name Errors \
        --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
        --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 3600 \
        --statistics Sum \
        --output json 2>/dev/null); then
        
        TOTAL_ERRORS=$(echo "$ERRORS" | jq '[.Datapoints[].Sum] | add // 0')
        print_status "Total errors (24h): $TOTAL_ERRORS"
        
        if [ "$TOTAL_ERRORS" -gt 0 ]; then
            print_warning "Errors detected in the last 24 hours"
        fi
    fi
    
    # Average duration
    if DURATION=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/Lambda \
        --metric-name Duration \
        --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
        --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 3600 \
        --statistics Average \
        --output json 2>/dev/null); then
        
        AVG_DURATION=$(echo "$DURATION" | jq '[.Datapoints[].Average] | add / length // 0 | floor')
        print_status "Average duration (24h): ${AVG_DURATION}ms"
    fi
fi

# Show cost information if requested
if [ "$SHOW_COSTS" = true ]; then
    print_status "Fetching cost information..."
    
    # Get current month's costs
    CURRENT_MONTH=$(date +%Y-%m-01)
    NEXT_MONTH=$(date -d "$CURRENT_MONTH +1 month" +%Y-%m-01)
    
    if COSTS=$(aws ce get-cost-and-usage \
        --time-period Start="$CURRENT_MONTH",End="$NEXT_MONTH" \
        --granularity MONTHLY \
        --metrics BlendedCost \
        --group-by Type=DIMENSION,Key=SERVICE \
        --filter file://<(echo '{
            "Tags": {
                "Key": "Project",
                "Values": ["AI News Agent"]
            }
        }') \
        --output json 2>/dev/null); then
        
        print_status "Current month costs by service:"
        echo "$COSTS" | jq -r '.ResultsByTime[0].Groups[] | "\(.Keys[0]): $\(.Metrics.BlendedCost.Amount | tonumber | . * 100 | floor / 100)"' | head -10
    else
        print_warning "Unable to fetch cost information (may require billing permissions)"
    fi
fi

# Show alarm status if requested
if [ "$SHOW_ALARMS" = true ]; then
    print_status "Checking alarm status..."
    
    if ALARMS=$(aws cloudwatch describe-alarms \
        --alarm-name-prefix "ai-news-agent-${ENVIRONMENT}" \
        --output json 2>/dev/null); then
        
        ALARM_COUNT=$(echo "$ALARMS" | jq '.MetricAlarms | length')
        if [ "$ALARM_COUNT" -gt 0 ]; then
            print_status "Found $ALARM_COUNT alarms:"
            
            # Count alarms by state
            OK_COUNT=$(echo "$ALARMS" | jq '[.MetricAlarms[] | select(.StateValue == "OK")] | length')
            ALARM_STATE_COUNT=$(echo "$ALARMS" | jq '[.MetricAlarms[] | select(.StateValue == "ALARM")] | length')
            INSUFFICIENT_COUNT=$(echo "$ALARMS" | jq '[.MetricAlarms[] | select(.StateValue == "INSUFFICIENT_DATA")] | length')
            
            echo "  OK: $OK_COUNT"
            echo "  ALARM: $ALARM_STATE_COUNT"
            echo "  INSUFFICIENT_DATA: $INSUFFICIENT_COUNT"
            
            if [ "$ALARM_STATE_COUNT" -gt 0 ]; then
                print_warning "Some alarms are in ALARM state:"
                echo "$ALARMS" | jq -r '.MetricAlarms[] | select(.StateValue == "ALARM") | "  \(.AlarmName): \(.StateReason)"'
            fi
            
            if [ "$VERBOSE" = true ]; then
                echo "$ALARMS" | jq -r '.MetricAlarms[] | "  \(.AlarmName): \(.StateValue) - \(.AlarmDescription)"'
            fi
        else
            print_warning "No alarms found"
        fi
    fi
fi

# Run health tests if requested
if [ "$RUN_TESTS" = true ]; then
    print_status "Running health tests..."
    
    # Test Lambda function invocation
    print_status "Testing Lambda function invocation..."
    TEST_EVENT='{"source": "health-check", "detail-type": "Health Check", "detail": {}}'
    
    if INVOKE_RESULT=$(aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --payload "$TEST_EVENT" \
        --output json \
        /tmp/lambda-health-response.json 2>/dev/null); then
        
        STATUS_CODE=$(echo "$INVOKE_RESULT" | jq -r '.StatusCode')
        if [ "$STATUS_CODE" = "200" ]; then
            print_success "Lambda function invocation test passed"
            if [ "$VERBOSE" = true ]; then
                echo "Response:"
                cat /tmp/lambda-health-response.json | jq .
            fi
        else
            print_error "Lambda function invocation test failed (Status: $STATUS_CODE)"
            if [ -f /tmp/lambda-health-response.json ]; then
                cat /tmp/lambda-health-response.json
            fi
        fi
        
        rm -f /tmp/lambda-health-response.json
    else
        print_error "Failed to invoke Lambda function for testing"
    fi
    
    # Test SNS topic (if we have the ARN)
    if [ -n "$TOPIC_ARN" ]; then
        print_status "Testing SNS topic..."
        TEST_MESSAGE="Health check message from monitoring script - $(date)"
        
        if aws sns publish \
            --topic-arn "$TOPIC_ARN" \
            --message "$TEST_MESSAGE" \
            --subject "AI News Agent Health Check" > /dev/null 2>&1; then
            print_success "SNS topic test message sent successfully"
        else
            print_error "Failed to send test message to SNS topic"
        fi
    fi
fi

echo ""
print_status "Monitoring complete!"

# Show dashboard links
echo ""
print_status "Useful Links:"
echo "CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$(aws configure get region)#dashboards:name=$DASHBOARD_NAME"
if [ "$SHOW_COSTS" = true ]; then
    echo "Cost Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$(aws configure get region)#dashboards:name=$COST_DASHBOARD_NAME"
fi
echo "Lambda Function: https://console.aws.amazon.com/lambda/home?region=$(aws configure get region)#/functions/$FUNCTION_NAME"
echo "CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$(aws configure get region)#logsV2:log-groups/log-group/$(echo "$LOG_GROUP_NAME" | sed 's/\//%252F/g')"
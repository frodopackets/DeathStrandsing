# AI News Agent Terraform Deployment

This directory contains the Terraform configuration for deploying the AI News Agent infrastructure on AWS.

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0 installed
3. S3 bucket and DynamoDB table for Terraform state management (see Backend Setup below)

## Backend Setup

Before deploying, you need to create the S3 bucket and DynamoDB table for Terraform state management:

### For Development Environment:
```bash
# Create S3 bucket for state
aws s3 mb s3://ai-news-agent-terraform-state-dev --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ai-news-agent-terraform-state-dev \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ai-news-agent-terraform-state-dev \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ai-news-agent-terraform-lock-dev \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

### For Production Environment:
```bash
# Create S3 bucket for state
aws s3 mb s3://ai-news-agent-terraform-state-prod --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ai-news-agent-terraform-state-prod \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ai-news-agent-terraform-state-prod \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ai-news-agent-terraform-lock-prod \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

## Deployment Commands

### Development Environment

1. **Initialize Terraform:**
   ```bash
   terraform init -backend-config=backend-dev.hcl
   ```

2. **Plan deployment:**
   ```bash
   terraform plan -var-file=environments/dev.tfvars
   ```

3. **Apply deployment:**
   ```bash
   terraform apply -var-file=environments/dev.tfvars
   ```

4. **Destroy infrastructure:**
   ```bash
   terraform destroy -var-file=environments/dev.tfvars
   ```

### Production Environment

1. **Initialize Terraform:**
   ```bash
   terraform init -backend-config=backend-prod.hcl
   ```

2. **Plan deployment:**
   ```bash
   terraform plan -var-file=environments/prod.tfvars
   ```

3. **Apply deployment:**
   ```bash
   terraform apply -var-file=environments/prod.tfvars
   ```

4. **Destroy infrastructure:**
   ```bash
   terraform destroy -var-file=environments/prod.tfvars
   ```

## Configuration

### Environment Variables

The deployment uses environment-specific variable files:

- `environments/dev.tfvars` - Development environment settings
- `environments/prod.tfvars` - Production environment settings

### Key Configuration Options

- **Lambda Memory**: Adjust `lambda_memory_size` based on performance needs
- **Schedule**: Modify `schedule_expression` to change execution frequency
- **Email Recipients**: Update `email_endpoints` to add/remove subscribers
- **AI Model**: Change `model_name` to use different Amazon Nova models
- **Monitoring**: Adjust `error_threshold` and `duration_threshold` for alerts

## Outputs

After successful deployment, Terraform will output:

- Lambda function name and ARN
- SNS topic name and ARN
- CloudWatch log group name
- KMS key ID and ARN
- EventBridge rule name

## Troubleshooting

### Common Issues

1. **Backend bucket doesn't exist**: Create the S3 bucket and DynamoDB table as described above
2. **Permission errors**: Ensure AWS credentials have sufficient permissions
3. **Resource conflicts**: Check for existing resources with the same names

### Validation

After deployment, verify:

1. Lambda function is created and configured correctly
2. SNS topic has email subscriptions
3. EventBridge rule is scheduled properly
4. CloudWatch logs are being created

## Security Considerations

- All resources use KMS encryption
- IAM roles follow least-privilege principle
- CIS compliance standards are implemented
- VPC configuration can be enabled for additional security

## Cost Optimization

- Development environment uses Nova Lite model for cost savings
- Log retention is shorter in development
- Concurrent executions are limited to control costs
- Consider adjusting schedule frequency based on needs
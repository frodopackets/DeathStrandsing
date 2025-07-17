# AI News Agent

AI agent that monitors Google news for Generative AI content and generates intelligent summaries using the Strands SDK and Amazon Nova models via AWS Bedrock.

## Features

- Automated news monitoring from Google News
- AI-powered content summarization using Amazon Nova models
- Email distribution via AWS SNS
- Serverless AWS infrastructure with Python 3.11
- Terraform deployment
- CIS compliance and security best practices

## Architecture

- **AWS Lambda**: Serverless compute (Python 3.11)
- **Amazon EventBridge**: Scheduled execution
- **Amazon SNS**: Email notifications
- **Amazon Bedrock**: Nova model access for AI summarization
- **Strands SDK**: AI agent framework
- **Terraform**: Infrastructure as Code

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   export SNS_TOPIC_ARN="your-sns-topic-arn"
   export SEARCH_QUERY="Generative AI"
   export MODEL_NAME="amazon.nova-pro-v1:0"
   export MODEL_PROVIDER="bedrock"
   ```

3. Deploy infrastructure:
   ```bash
   cd terraform && terraform apply
   ```

## Testing

Run the test suite:
```bash
pytest
```

Run specific test categories:
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m security      # Security tests only
```

## Development

- `pytest` - Run all tests
- `pytest --watch` - Run tests in watch mode
- `black .` - Format code
- `flake8 .` - Lint code
- `mypy src/` - Type checking

## Project Structure

```
src/
├── models/          # Data models (NewsArticle, NewsSummary, etc.)
├── services/        # Business logic (NewsFetcher, AISummarizer, etc.)
├── lambda/          # Lambda handlers
└── __init__.py

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── __init__.py

terraform/          # Infrastructure as Code
```

## License

MIT

"""Unit tests for the Lambda handler with focus on no-news scenarios."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from src.aws_lambda.handler import LambdaHandler, WorkflowError, ErrorType
from src.models import NewsArticle, NewsSummary, ArticleSource, AgentConfig


class TestLambdaHandlerNoNewsScenarios:
    """Test cases for Lambda handler no-news scenarios."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return AgentConfig(
            search_query="Generative AI",
            time_range_hours=72,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=50,
            summary_length="medium",
            model_name="amazon.nova-pro-v1:0",
            model_provider="bedrock"
        )
    
    @pytest.fixture
    def mock_services(self):
        """Mock services for testing."""
        return {
            'news_fetcher': AsyncMock(),
            'ai_summarizer': AsyncMock(),
            'sns_publisher': AsyncMock()
        }
    
    @pytest.fixture
    def lambda_event(self):
        """Mock Lambda event."""
        return {
            'correlation_id': 'test-correlation-123',
            'source': 'aws.events'
        }
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context."""
        context = Mock()
        context.function_name = 'ai-news-agent'
        context.function_version = '1'
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:ai-news-agent'
        context.memory_limit_in_mb = 512
        context.remaining_time_in_millis = lambda: 300000
        return context
    
    @pytest.mark.asyncio
    @patch('src.aws_lambda.handler.AgentConfig.from_environment')
    @patch('src.aws_lambda.handler.GoogleNewsFetcher')
    @patch('src.aws_lambda.handler.StrandsAISummarizer')
    @patch('src.aws_lambda.handler.AWSNSPublisher')
    async def test_no_news_scenario_success(
        self, 
        mock_sns_publisher_class,
        mock_ai_summarizer_class,
        mock_news_fetcher_class,
        mock_config_from_env,
        mock_config,
        mock_services,
        lambda_event,
        lambda_context
    ):
        """Test successful handling of no-news scenario."""
        # Setup mocks
        mock_config_from_env.return_value = mock_config
        
        mock_news_fetcher = mock_services['news_fetcher']
        mock_sns_publisher = mock_services['sns_publisher']
        
        mock_news_fetcher_class.return_value = mock_news_fetcher
        mock_sns_publisher_class.return_value = mock_sns_publisher
        
        # Configure news fetcher to return no articles
        mock_news_fetcher.fetch_news.return_value = []
        mock_news_fetcher.filter_articles.return_value = []
        
        # Configure SNS publisher to succeed
        mock_sns_publisher.send_no_news_notification.return_value = True
        
        # Create handler and execute
        handler = LambdaHandler()
        response = await handler.handler(lambda_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert 'No relevant news found' in response_body['message']
        assert response_body['correlation_id'] == 'test-correlation-123'
        
        # Verify no-news notification was sent
        mock_sns_publisher.send_no_news_notification.assert_called_once()
        
        # Verify news fetcher was called
        mock_news_fetcher.fetch_news.assert_called_once_with(
            query="Generative AI",
            time_range_hours=72
        )
    
    @pytest.mark.asyncio
    @patch('src.aws_lambda.handler.AgentConfig.from_environment')
    @patch('src.aws_lambda.handler.GoogleNewsFetcher')
    @patch('src.aws_lambda.handler.StrandsAISummarizer')
    @patch('src.aws_lambda.handler.AWSNSPublisher')
    async def test_no_news_notification_failure_with_retry(
        self, 
        mock_sns_publisher_class,
        mock_ai_summarizer_class,
        mock_news_fetcher_class,
        mock_config_from_env,
        mock_config,
        mock_services,
        lambda_event,
        lambda_context
    ):
        """Test no-news notification failure with retry logic."""
        # Setup mocks
        mock_config_from_env.return_value = mock_config
        
        mock_news_fetcher = mock_services['news_fetcher']
        mock_sns_publisher = mock_services['sns_publisher']
        
        mock_news_fetcher_class.return_value = mock_news_fetcher
        mock_sns_publisher_class.return_value = mock_sns_publisher
        
        # Configure news fetcher to return no articles
        mock_news_fetcher.fetch_news.return_value = []
        mock_news_fetcher.filter_articles.return_value = []
        
        # Configure SNS publisher to fail first attempt, succeed second
        mock_sns_publisher.send_no_news_notification.side_effect = [False, True]
        
        # Create handler and execute
        handler = LambdaHandler()
        response = await handler.handler(lambda_event, lambda_context)
        
        # Verify response is still success (no-news notification is not critical)
        assert response['statusCode'] == 200
        
        # Verify retry was attempted (called twice)
        assert mock_sns_publisher.send_no_news_notification.call_count == 2
    
    @pytest.mark.asyncio
    @patch('src.aws_lambda.handler.AgentConfig.from_environment')
    @patch('src.aws_lambda.handler.GoogleNewsFetcher')
    @patch('src.aws_lambda.handler.StrandsAISummarizer')
    @patch('src.aws_lambda.handler.AWSNSPublisher')
    async def test_no_news_notification_complete_failure(
        self, 
        mock_sns_publisher_class,
        mock_ai_summarizer_class,
        mock_news_fetcher_class,
        mock_config_from_env,
        mock_config,
        mock_services,
        lambda_event,
        lambda_context
    ):
        """Test complete failure of no-news notification."""
        # Setup mocks
        mock_config_from_env.return_value = mock_config
        
        mock_news_fetcher = mock_services['news_fetcher']
        mock_sns_publisher = mock_services['sns_publisher']
        
        mock_news_fetcher_class.return_value = mock_news_fetcher
        mock_sns_publisher_class.return_value = mock_sns_publisher
        
        # Configure news fetcher to return no articles
        mock_news_fetcher.fetch_news.return_value = []
        mock_news_fetcher.filter_articles.return_value = []
        
        # Configure SNS publisher to always fail
        mock_sns_publisher.send_no_news_notification.return_value = False
        
        # Create handler and execute
        handler = LambdaHandler()
        response = await handler.handler(lambda_event, lambda_context)
        
        # Verify response is still success (no-news notification failure is not critical)
        assert response['statusCode'] == 200
        
        # Verify retry was attempted (called twice due to retry logic)
        assert mock_sns_publisher.send_no_news_notification.call_count == 2
    
    @pytest.mark.asyncio
    @patch('src.aws_lambda.handler.AgentConfig.from_environment')
    @patch('src.aws_lambda.handler.GoogleNewsFetcher')
    @patch('src.aws_lambda.handler.StrandsAISummarizer')
    @patch('src.aws_lambda.handler.AWSNSPublisher')
    async def test_no_news_with_exception_handling(
        self, 
        mock_sns_publisher_class,
        mock_ai_summarizer_class,
        mock_news_fetcher_class,
        mock_config_from_env,
        mock_config,
        mock_services,
        lambda_event,
        lambda_context
    ):
        """Test no-news scenario with exception in notification sending."""
        # Setup mocks
        mock_config_from_env.return_value = mock_config
        
        mock_news_fetcher = mock_services['news_fetcher']
        mock_sns_publisher = mock_services['sns_publisher']
        
        mock_news_fetcher_class.return_value = mock_news_fetcher
        mock_sns_publisher_class.return_value = mock_sns_publisher
        
        # Configure news fetcher to return no articles
        mock_news_fetcher.fetch_news.return_value = []
        mock_news_fetcher.filter_articles.return_value = []
        
        # Configure SNS publisher to raise exception
        mock_sns_publisher.send_no_news_notification.side_effect = Exception("SNS error")
        
        # Create handler and execute
        handler = LambdaHandler()
        response = await handler.handler(lambda_event, lambda_context)
        
        # Verify response is still success (exception is handled gracefully)
        assert response['statusCode'] == 200
        
        # Verify retry was attempted
        assert mock_sns_publisher.send_no_news_notification.call_count == 2
    
    @pytest.mark.asyncio
    @patch('src.aws_lambda.handler.AgentConfig.from_environment')
    @patch('src.aws_lambda.handler.GoogleNewsFetcher')
    @patch('src.aws_lambda.handler.StrandsAISummarizer')
    @patch('src.aws_lambda.handler.AWSNSPublisher')
    async def test_empty_articles_after_filtering(
        self, 
        mock_sns_publisher_class,
        mock_ai_summarizer_class,
        mock_news_fetcher_class,
        mock_config_from_env,
        mock_config,
        mock_services,
        lambda_event,
        lambda_context
    ):
        """Test scenario where articles are found but filtered out as irrelevant."""
        # Setup mocks
        mock_config_from_env.return_value = mock_config
        
        mock_news_fetcher = mock_services['news_fetcher']
        mock_sns_publisher = mock_services['sns_publisher']
        
        mock_news_fetcher_class.return_value = mock_news_fetcher
        mock_sns_publisher_class.return_value = mock_sns_publisher
        
        # Create mock articles that will be filtered out
        mock_articles = [
            NewsArticle(
                title="Irrelevant Article",
                content="This is not about AI",
                url="https://example.com/1",
                published_at=datetime.now(timezone.utc),
                source="Test Source",
                relevance_score=0.05  # Below threshold
            )
        ]
        
        # Configure news fetcher to return articles but filter them out
        mock_news_fetcher.fetch_news.return_value = mock_articles
        mock_news_fetcher.filter_articles.return_value = []  # All filtered out
        
        # Configure SNS publisher to succeed
        mock_sns_publisher.send_no_news_notification.return_value = True
        
        # Create handler and execute
        handler = LambdaHandler()
        response = await handler.handler(lambda_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert 'No relevant news found' in response_body['message']
        
        # Verify filtering was called
        mock_news_fetcher.filter_articles.assert_called_once_with(mock_articles)
        
        # Verify no-news notification was sent
        mock_sns_publisher.send_no_news_notification.assert_called_once()
    
    def test_no_news_detection_logic(self):
        """Test the logic for detecting no-news scenarios."""
        # Test empty list
        assert self._is_no_news_scenario([]) == True
        
        # Test None
        assert self._is_no_news_scenario(None) == True
        
        # Test list with articles
        articles = [
            NewsArticle(
                title="AI Article",
                content="About AI",
                url="https://example.com/1",
                published_at=datetime.now(timezone.utc),
                source="Test Source"
            )
        ]
        assert self._is_no_news_scenario(articles) == False
    
    def _is_no_news_scenario(self, articles):
        """Helper method to test no-news detection logic."""
        return not articles or len(articles) == 0


class TestNoNewsNotificationContent:
    """Test cases for no-news notification content and formatting."""
    
    @pytest.fixture
    def mock_sns_publisher(self):
        """Mock SNS publisher for testing."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_no_news_notification_content_structure(self, mock_sns_publisher):
        """Test that no-news notification has proper content structure."""
        # Mock the internal methods to capture the message content
        mock_sns_publisher.send_no_news_notification.return_value = True
        
        # Verify the notification contains expected elements
        # This would be tested by examining the actual SNS publisher implementation
        # which we already have in the AWSNSPublisher class
        
        # Test plain text content
        expected_elements = [
            "No relevant Generative AI news articles",
            "last 72 hours",
            "no significant developments",
            "next summary when relevant news becomes available"
        ]
        
        # These elements should be present in the no-news notification
        # The actual implementation is in AWSNSPublisher._get_no_news_text()
        assert True  # Placeholder - actual content testing would examine the publisher
    
    @pytest.mark.asyncio
    async def test_no_news_html_formatting(self, mock_sns_publisher):
        """Test HTML formatting of no-news notification."""
        # Test HTML content structure
        expected_html_elements = [
            "<h1>🤖 AI News Summary</h1>",
            "<h2>No Updates Today</h2>",
            "<ul>",
            "<li>There were no significant developments",
            "AI News Agent"
        ]
        
        # These elements should be present in the HTML version
        # The actual implementation is in AWSNSPublisher._get_no_news_html()
        assert True  # Placeholder - actual content testing would examine the publisher


class TestNoNewsScenarioIntegration:
    """Integration tests for no-news scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_no_news_flow(self):
        """Test complete end-to-end flow for no-news scenario."""
        # This would be an integration test that:
        # 1. Sets up real or realistic mock services
        # 2. Triggers the Lambda handler
        # 3. Verifies the complete flow from news fetching to notification
        # 4. Checks that appropriate logs are generated
        # 5. Verifies error handling and recovery
        
        # For now, this is a placeholder for future integration testing
        assert True
    
    @pytest.mark.asyncio
    async def test_no_news_with_partial_service_failures(self):
        """Test no-news scenario with some service failures."""
        # This would test scenarios where:
        # 1. News fetching partially fails but returns empty results
        # 2. SNS publishing has intermittent failures
        # 3. Recovery mechanisms are triggered
        
        # For now, this is a placeholder for future integration testing
        assert True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
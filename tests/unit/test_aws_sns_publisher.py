"""Unit tests for AWS SNS Publisher."""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from botocore.exceptions import ClientError

from src.services.aws_sns_publisher import AWSNSPublisher
from src.models.news_summary import NewsSummary, ArticleSource


@pytest.fixture
def sample_summary():
    """Create a sample NewsSummary for testing."""
    sources = [
        ArticleSource(
            title="AI Breakthrough in 2024",
            url="https://example.com/ai-breakthrough",
            source="Tech News",
            published_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        ),
        ArticleSource(
            title="New Language Model Released",
            url="https://example.com/new-model",
            source="AI Weekly",
            published_at=datetime(2024, 1, 14, 15, 45, tzinfo=timezone.utc)
        )
    ]
    
    return NewsSummary(
        summary="Major developments in AI this week include new breakthroughs and model releases.",
        key_points=[
            "New AI model shows improved reasoning capabilities",
            "Industry adoption of AI tools continues to grow",
            "Regulatory discussions around AI safety intensify"
        ],
        sources=sources,
        generated_at=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        article_count=2
    )


@pytest.fixture
def sns_publisher():
    """Create an AWSNSPublisher instance for testing."""
    with patch('boto3.client'):
        publisher = AWSNSPublisher(
            topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            region_name="us-east-1"
        )
        return publisher


class TestAWSNSPublisher:
    """Test cases for AWSNSPublisher class."""
    
    def test_init(self):
        """Test SNS publisher initialization."""
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client
            
            publisher = AWSNSPublisher(
                topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                region_name="us-west-2"
            )
            
            assert publisher.topic_arn == "arn:aws:sns:us-east-1:123456789012:test-topic"
            assert publisher.region_name == "us-west-2"
            assert publisher.sns_client == mock_client
            assert publisher.max_retries == 3
            assert publisher.base_delay == 1.0
            
            mock_boto3.assert_called_once_with('sns', region_name='us-west-2')
    
    @pytest.mark.asyncio
    async def test_format_message(self, sns_publisher, sample_summary):
        """Test message formatting for email delivery."""
        formatted_message = await sns_publisher.format_message(sample_summary)
        
        # Parse the JSON message
        message_data = json.loads(formatted_message)
        
        # Check structure
        assert 'default' in message_data
        assert 'email' in message_data
        assert 'email-json' in message_data
        
        # Check default (plain text) content
        default_content = message_data['default']
        assert "AI News Summary" in default_content
        assert "Major developments in AI" in default_content
        assert "AI Breakthrough in 2024" in default_content
        
        # Check email (HTML) content
        email_content = message_data['email']
        assert "<html>" in email_content
        assert "<h1>🤖 AI News Summary</h1>" in email_content
        assert "Major developments in AI" in email_content
        assert "AI Breakthrough in 2024" in email_content
        
        # Check email-json structure
        email_json = message_data['email-json']
        assert 'html' in email_json
        assert 'text' in email_json
    
    @pytest.mark.asyncio
    async def test_format_message_error_fallback(self, sns_publisher):
        """Test message formatting fallback on error."""
        # Create a summary that might cause formatting issues
        bad_summary = Mock()
        bad_summary.id = "test-id"
        bad_summary.format_for_plain_text.return_value = "Fallback text"
        
        # Mock the _format_html_message to raise an exception
        with patch.object(sns_publisher, '_format_html_message', side_effect=Exception("Format error")):
            formatted_message = await sns_publisher.format_message(bad_summary)
            
            # Should fallback to plain text
            assert formatted_message == "Fallback text"
    
    @pytest.mark.asyncio
    async def test_publish_summary_success(self, sns_publisher, sample_summary):
        """Test successful summary publishing."""
        # Mock successful SNS publish
        mock_response = {'MessageId': 'test-message-id-123'}
        sns_publisher.sns_client.publish.return_value = mock_response
        
        result = await sns_publisher.publish_summary(sample_summary)
        
        assert result is True
        
        # Verify SNS publish was called with correct parameters
        sns_publisher.sns_client.publish.assert_called_once()
        call_args = sns_publisher.sns_client.publish.call_args
        
        assert call_args[1]['TopicArn'] == sns_publisher.topic_arn
        assert call_args[1]['Subject'] == "AI News Summary - January 15, 2024"
        assert call_args[1]['MessageStructure'] == 'json'
        
        # Check message attributes
        message_attrs = call_args[1]['MessageAttributes']
        assert message_attrs['MessageType']['StringValue'] == 'NewsSummary'
        assert message_attrs['ArticleCount']['StringValue'] == '2'
    
    @pytest.mark.asyncio
    async def test_publish_summary_with_retry(self, sns_publisher, sample_summary):
        """Test summary publishing with retry logic."""
        # Mock first call to fail, second to succeed
        mock_error = ClientError(
            error_response={'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
            operation_name='Publish'
        )
        mock_success = {'MessageId': 'test-message-id-123'}
        
        sns_publisher.sns_client.publish.side_effect = [mock_error, mock_success]
        
        # Mock sleep to avoid actual delays in tests
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await sns_publisher.publish_summary(sample_summary)
        
        assert result is True
        assert sns_publisher.sns_client.publish.call_count == 2
    
    @pytest.mark.asyncio
    async def test_publish_summary_max_retries_exceeded(self, sns_publisher, sample_summary):
        """Test summary publishing when max retries are exceeded."""
        # Mock all calls to fail
        mock_error = ClientError(
            error_response={'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
            operation_name='Publish'
        )
        sns_publisher.sns_client.publish.side_effect = mock_error
        
        # Mock sleep to avoid actual delays in tests
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await sns_publisher.publish_summary(sample_summary)
        
        assert result is False
        assert sns_publisher.sns_client.publish.call_count == 4  # Initial + 3 retries
    
    @pytest.mark.asyncio
    async def test_publish_summary_non_retryable_error(self, sns_publisher, sample_summary):
        """Test summary publishing with non-retryable error."""
        # Mock non-retryable error
        mock_error = ClientError(
            error_response={'Error': {'Code': 'InvalidParameter', 'Message': 'Invalid topic ARN'}},
            operation_name='Publish'
        )
        sns_publisher.sns_client.publish.side_effect = mock_error
        
        result = await sns_publisher.publish_summary(sample_summary)
        
        assert result is False
        assert sns_publisher.sns_client.publish.call_count == 1  # No retries for non-retryable errors
    
    @pytest.mark.asyncio
    async def test_send_no_news_notification_success(self, sns_publisher):
        """Test successful no-news notification."""
        mock_response = {'MessageId': 'test-message-id-456'}
        sns_publisher.sns_client.publish.return_value = mock_response
        
        result = await sns_publisher.send_no_news_notification()
        
        assert result is True
        
        # Verify SNS publish was called
        sns_publisher.sns_client.publish.assert_called_once()
        call_args = sns_publisher.sns_client.publish.call_args
        
        assert call_args[1]['Subject'] == "AI News Summary - No Updates Today"
        
        # Check message attributes
        message_attrs = call_args[1]['MessageAttributes']
        assert message_attrs['MessageType']['StringValue'] == 'NoNewsNotification'
    
    @pytest.mark.asyncio
    async def test_send_no_news_notification_failure(self, sns_publisher):
        """Test no-news notification failure."""
        mock_error = ClientError(
            error_response={'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            operation_name='Publish'
        )
        sns_publisher.sns_client.publish.side_effect = mock_error
        
        # Mock sleep to avoid actual delays in tests
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await sns_publisher.send_no_news_notification()
        
        assert result is False
    
    def test_calculate_retry_delay(self, sns_publisher):
        """Test retry delay calculation."""
        # Test exponential backoff
        delay_0 = sns_publisher._calculate_retry_delay(0)
        delay_1 = sns_publisher._calculate_retry_delay(1)
        delay_2 = sns_publisher._calculate_retry_delay(2)
        
        # Should increase exponentially (with some jitter)
        assert 0.9 <= delay_0 <= 1.1  # ~1.0 with jitter
        assert 1.8 <= delay_1 <= 2.2  # ~2.0 with jitter
        assert 3.6 <= delay_2 <= 4.4  # ~4.0 with jitter
        
        # Test maximum delay cap (allowing for jitter which can add up to 10% more)
        large_delay = sns_publisher._calculate_retry_delay(10)
        # With jitter, delay can be up to 10% more than max_delay
        max_allowed = sns_publisher.max_delay * 1.1
        assert large_delay <= max_allowed
    
    def test_calculate_retry_delay_no_jitter(self, sns_publisher):
        """Test retry delay calculation without jitter."""
        sns_publisher.jitter = False
        
        delay_0 = sns_publisher._calculate_retry_delay(0)
        delay_1 = sns_publisher._calculate_retry_delay(1)
        delay_2 = sns_publisher._calculate_retry_delay(2)
        
        # Should be exact values without jitter
        assert delay_0 == 1.0
        assert delay_1 == 2.0
        assert delay_2 == 4.0
    
    def test_format_html_message(self, sns_publisher, sample_summary):
        """Test HTML message formatting."""
        html_content = sns_publisher._format_html_message(sample_summary)
        
        # Check HTML structure
        assert "<html>" in html_content
        assert "</html>" in html_content
        assert "<h1>🤖 AI News Summary</h1>" in html_content
        
        # Check content
        assert "Major developments in AI" in html_content
        assert "AI Breakthrough in 2024" in html_content
        assert "New Language Model Released" in html_content
        assert "New AI model shows improved reasoning" in html_content
        
        # Check styling
        assert "<style>" in html_content
        assert "font-family: Arial" in html_content
    
    def test_get_no_news_text(self, sns_publisher):
        """Test plain text no-news notification."""
        text_content = sns_publisher._get_no_news_text()
        
        assert "AI News Summary - No Updates Today" in text_content
        assert "No relevant Generative AI news articles" in text_content
        assert "This could mean:" in text_content
        assert "AI News Agent" in text_content
    
    def test_get_no_news_html(self, sns_publisher):
        """Test HTML no-news notification."""
        html_content = sns_publisher._get_no_news_html()
        
        assert "<html>" in html_content
        assert "</html>" in html_content
        assert "<h1>🤖 AI News Summary</h1>" in html_content
        assert "No relevant Generative AI news articles" in html_content
        assert "This could mean:" in html_content
        assert "AI News Agent" in html_content
    
    @pytest.mark.asyncio
    async def test_get_subscription_status_success(self, sns_publisher):
        """Test successful subscription status retrieval."""
        mock_response = {
            'Subscriptions': [
                {
                    'SubscriptionArn': 'arn:aws:sns:us-east-1:123456789012:test-topic:12345',
                    'Protocol': 'email',
                    'Endpoint': 'test@example.com'
                },
                {
                    'SubscriptionArn': 'PendingConfirmation',
                    'Protocol': 'email',
                    'Endpoint': 'pending@example.com'
                }
            ]
        }
        sns_publisher.sns_client.list_subscriptions_by_topic.return_value = mock_response
        
        status = await sns_publisher.get_subscription_status()
        
        assert status['total_subscriptions'] == 2
        assert status['confirmed_subscriptions'] == 1
        assert status['pending_subscriptions'] == 1
        assert len(status['subscriptions']) == 2
        assert status['subscriptions'][0]['confirmed'] is True
        assert status['subscriptions'][1]['confirmed'] is False
    
    @pytest.mark.asyncio
    async def test_get_subscription_status_error(self, sns_publisher):
        """Test subscription status retrieval error."""
        mock_error = ClientError(
            error_response={'Error': {'Code': 'NotFound', 'Message': 'Topic not found'}},
            operation_name='ListSubscriptionsByTopic'
        )
        sns_publisher.sns_client.list_subscriptions_by_topic.side_effect = mock_error
        
        status = await sns_publisher.get_subscription_status()
        
        assert 'error' in status
        assert 'Topic not found' in status['error']
    
    @pytest.mark.asyncio
    async def test_track_delivery_status_success(self, sns_publisher):
        """Test successful delivery status tracking."""
        mock_response = {
            'Attributes': {
                'DeliveryStatusLogging': {
                    'email': 'true',
                    'http': 'false',
                    'sms': 'false'
                }
            }
        }
        sns_publisher.sns_client.get_topic_attributes.return_value = mock_response
        
        status = await sns_publisher.track_delivery_status('test-message-id')
        
        assert status['message_id'] == 'test-message-id'
        assert status['topic_arn'] == sns_publisher.topic_arn
        assert 'timestamp' in status
        assert status['delivery_status_logging_enabled']['email'] is True
        assert status['delivery_status_logging_enabled']['http'] is False
    
    @pytest.mark.asyncio
    async def test_track_delivery_status_error(self, sns_publisher):
        """Test delivery status tracking error."""
        mock_error = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='GetTopicAttributes'
        )
        sns_publisher.sns_client.get_topic_attributes.side_effect = mock_error
        
        status = await sns_publisher.track_delivery_status('test-message-id')
        
        assert 'error' in status
        assert status['message_id'] == 'test-message-id'
        assert 'Access denied' in status['error']
    
    @pytest.mark.asyncio
    async def test_handle_subscription_confirmation_success(self, sns_publisher):
        """Test successful subscription confirmation."""
        mock_response = {
            'SubscriptionArn': 'arn:aws:sns:us-east-1:123456789012:test-topic:confirmed'
        }
        sns_publisher.sns_client.confirm_subscription.return_value = mock_response
        
        result = await sns_publisher.handle_subscription_confirmation(
            'test-token', 
            'arn:aws:sns:us-east-1:123456789012:test-topic'
        )
        
        assert result is True
        sns_publisher.sns_client.confirm_subscription.assert_called_once_with(
            TopicArn='arn:aws:sns:us-east-1:123456789012:test-topic',
            Token='test-token'
        )
    
    @pytest.mark.asyncio
    async def test_handle_subscription_confirmation_error(self, sns_publisher):
        """Test subscription confirmation error."""
        mock_error = ClientError(
            error_response={'Error': {'Code': 'InvalidParameter', 'Message': 'Invalid token'}},
            operation_name='ConfirmSubscription'
        )
        sns_publisher.sns_client.confirm_subscription.side_effect = mock_error
        
        result = await sns_publisher.handle_subscription_confirmation(
            'invalid-token',
            'arn:aws:sns:us-east-1:123456789012:test-topic'
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_log_delivery_attempt_success(self, sns_publisher):
        """Test successful delivery attempt logging."""
        delivery_info = {
            'status': 'published',
            'attempt': 1,
            'subject': 'Test Subject'
        }
        
        # This should not raise an exception
        await sns_publisher.log_delivery_attempt('test-message-id', delivery_info)
        
        # Verify it completes without error (no assertion needed as it's a logging function)
    
    @pytest.mark.asyncio
    async def test_log_delivery_attempt_error(self, sns_publisher):
        """Test delivery attempt logging with error."""
        # Create invalid delivery info that might cause JSON serialization issues
        delivery_info = {'invalid': object()}  # object() is not JSON serializable
        
        # This should handle the error gracefully and not raise an exception
        await sns_publisher.log_delivery_attempt('test-message-id', delivery_info)
        
        # Verify it completes without raising an exception
    
    @pytest.mark.asyncio
    async def test_publish_with_delivery_tracking(self, sns_publisher, sample_summary):
        """Test publishing with delivery tracking integration."""
        # Mock successful SNS publish
        mock_response = {'MessageId': 'test-message-id-123'}
        sns_publisher.sns_client.publish.return_value = mock_response
        
        # Mock topic attributes for delivery tracking
        mock_topic_attrs = {
            'Attributes': {
                'DeliveryStatusLogging': {
                    'email': 'true'
                }
            }
        }
        sns_publisher.sns_client.get_topic_attributes.return_value = mock_topic_attrs
        
        result = await sns_publisher.publish_summary(sample_summary)
        
        assert result is True
        
        # Verify both publish and get_topic_attributes were called
        sns_publisher.sns_client.publish.assert_called_once()
        sns_publisher.sns_client.get_topic_attributes.assert_called_once_with(
            TopicArn=sns_publisher.topic_arn
        )
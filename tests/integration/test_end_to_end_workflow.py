"""Integration tests for end-to-end AI News Agent workflow."""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from src.aws_lambda.handler import LambdaHandler, WorkflowError, ErrorType
from src.models import NewsArticle, NewsSummary, ArticleSource, AgentConfig
from src.services import GoogleNewsFetcher, StrandsAISummarizer, AWSNSPublisher


@pytest.fixture
def sample_articles():
    """Create sample NewsArticle objects for integration testing."""
    now = datetime.now(timezone.utc)
    return [
        NewsArticle(
            title="OpenAI Releases Revolutionary GPT-5 Model",
            content="OpenAI has announced the release of GPT-5, featuring unprecedented reasoning capabilities and multimodal understanding. The new model demonstrates significant improvements in code generation, mathematical reasoning, and creative writing tasks.",
            url="https://example.com/openai-gpt5-release",
            published_at=now - timedelta(hours=2),
            source="TechCrunch",
            relevance_score=0.95
        ),
        NewsArticle(
            title="Google Unveils Gemini 3.0 with Advanced AI Capabilities",
            content="Google has introduced Gemini 3.0, a next-generation AI model that excels in multimodal tasks and demonstrates superior performance in scientific reasoning and code generation.",
            url="https://example.com/google-gemini-3",
            published_at=now - timedelta(hours=4),
            source="The Verge",
            relevance_score=0.88
        ),
        NewsArticle(
            title="Microsoft Integrates Advanced AI into Office Suite",
            content="Microsoft announces comprehensive AI integration across Office applications, bringing generative AI capabilities to Word, Excel, and PowerPoint with new Copilot features.",
            url="https://example.com/microsoft-office-ai",
            published_at=now - timedelta(hours=6),
            source="Microsoft News",
            relevance_score=0.82
        )
    ]


@pytest.fixture
def sample_summary(sample_articles):
    """Create a sample NewsSummary for integration testing."""
    sources = [
        ArticleSource(
            title=article.title,
            url=article.url,
            source=article.source,
            published_at=article.published_at
        ) for article in sample_articles
    ]
    
    return NewsSummary(
        summary="This week has seen major developments in generative AI with significant releases from OpenAI, Google, and Microsoft. OpenAI's GPT-5 represents a breakthrough in reasoning capabilities, while Google's Gemini 3.0 advances multimodal AI understanding. Microsoft's integration of AI into Office applications demonstrates the practical application of these technologies in everyday productivity tools.",
        key_points=[
            "OpenAI releases GPT-5 with unprecedented reasoning capabilities",
            "Google unveils Gemini 3.0 with superior multimodal performance",
            "Microsoft integrates advanced AI across Office suite applications",
            "Industry focus shifts toward practical AI implementation",
            "Significant improvements in code generation and scientific reasoning"
        ],
        sources=sources,
        generated_at=datetime.now(timezone.utc),
        article_count=len(sample_articles)
    )


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    return {
        'SEARCH_QUERY': 'Generative AI',
        'TIME_RANGE_HOURS': '72',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-ai-news-topic',
        'MAX_ARTICLES': '50',
        'SUMMARY_LENGTH': 'medium',
        'MODEL_NAME': 'amazon.nova-pro-v1:0',
        'MODEL_PROVIDER': 'bedrock'
    }


@pytest.fixture
def lambda_event():
    """Create a sample Lambda event for testing."""
    return {
        'correlation_id': 'test-integration-123',
        'source': 'aws.events',
        'detail-type': 'Scheduled Event',
        'detail': {},
        'time': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context for testing."""
    context = Mock()
    context.function_name = 'ai-news-agent-integration-test'
    context.function_version = '1'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:ai-news-agent-test'
    context.memory_limit_in_mb = 512
    context.remaining_time_in_millis = lambda: 300000  # 5 minutes
    context.aws_request_id = 'test-request-id-123'
    return context


class TestEndToEndWorkflow:
    """Integration tests for complete end-to-end workflow."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_successful_end_to_end_workflow(
        self, 
        mock_environment, 
        sample_articles, 
        sample_summary, 
        lambda_event, 
        lambda_context
    ):
        """Test complete successful workflow from news fetching to summary delivery."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Mock all external dependencies
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Configure mock behaviors
            mock_fetcher.fetch_news.return_value = sample_articles
            mock_fetcher.filter_articles.return_value = sample_articles
            mock_summarizer.generate_summary.return_value = sample_summary
            mock_publisher.publish_summary.return_value = True
            
            # Execute the workflow
            handler = LambdaHandler()
            start_time = time.time()
            response = await handler.handler(lambda_event, lambda_context)
            execution_time = time.time() - start_time
            
            # Verify response structure
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            
            # Verify response content
            assert 'AI News Agent executed successfully' in response_body['message']
            assert response_body['correlation_id'] == 'test-integration-123'
            assert response_body['article_count'] == 3
            assert response_body['summary_id'] == sample_summary.id
            assert response_body['execution_time_seconds'] > 0
            assert response_body['status'] == 'success'
            
            # Verify workflow state
            workflow_state = response_body['workflow_state']
            assert workflow_state['articles_fetched'] is True
            assert workflow_state['summary_generated'] is True
            assert workflow_state['summary_published'] is True
            assert len(workflow_state['articles']) == 3
            
            # Verify all services were called correctly
            mock_fetcher.fetch_news.assert_called_once_with(
                query='Generative AI',
                time_range_hours=72
            )
            mock_fetcher.filter_articles.assert_called_once_with(sample_articles)
            mock_summarizer.generate_summary.assert_called_once_with(sample_articles)
            mock_publisher.publish_summary.assert_called_once_with(sample_summary)
            
            # Verify execution time is reasonable (should complete within 30 seconds)
            assert execution_time < 30.0
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_no_news_workflow(
        self, 
        mock_environment, 
        lambda_event, 
        lambda_context
    ):
        """Test end-to-end workflow when no relevant news is found."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Configure no-news scenario
            mock_fetcher.fetch_news.return_value = []
            mock_fetcher.filter_articles.return_value = []
            mock_publisher.send_no_news_notification.return_value = True
            
            # Execute the workflow
            handler = LambdaHandler()
            response = await handler.handler(lambda_event, lambda_context)
            
            # Verify response
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert 'No relevant news found' in response_body['message']
            
            # Verify workflow state
            workflow_state = response_body['workflow_state']
            assert workflow_state['articles_fetched'] is True
            assert workflow_state['summary_generated'] is False
            assert workflow_state['summary_published'] is False
            assert len(workflow_state['articles']) == 0
            
            # Verify no-news notification was sent
            mock_publisher.send_no_news_notification.assert_called_once()
            
            # Verify summarizer was not called
            mock_summarizer.generate_summary.assert_not_called()
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_workflow_with_news_fetch_failure_recovery(
        self, 
        mock_environment, 
        lambda_event, 
        lambda_context
    ):
        """Test workflow recovery when news fetching fails initially but succeeds on retry."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_publisher_class.return_value = mock_publisher
            
            # Configure fetch failure then success
            mock_fetcher.fetch_news.side_effect = [
                Exception("Network timeout"),  # First attempt fails
                []  # Second attempt succeeds but returns no articles
            ]
            mock_fetcher.filter_articles.return_value = []
            mock_publisher.send_no_news_notification.return_value = True
            
            # Execute the workflow
            handler = LambdaHandler()
            response = await handler.handler(lambda_event, lambda_context)
            
            # Verify response indicates successful recovery
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert 'No relevant news found' in response_body['message']
            
            # Verify retry was attempted
            assert mock_fetcher.fetch_news.call_count == 2
            mock_publisher.send_no_news_notification.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_workflow_with_summarization_fallback(
        self, 
        mock_environment, 
        sample_articles, 
        lambda_event, 
        lambda_context
    ):
        """Test workflow with AI summarization failure and fallback."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Configure successful fetching but failed summarization
            mock_fetcher.fetch_news.return_value = sample_articles
            mock_fetcher.filter_articles.return_value = sample_articles
            mock_summarizer.generate_summary.side_effect = Exception("AI service unavailable")
            mock_publisher.publish_summary.return_value = True
            
            # Execute the workflow
            handler = LambdaHandler()
            response = await handler.handler(lambda_event, lambda_context)
            
            # Verify response indicates successful fallback
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert 'AI News Agent executed successfully' in response_body['message']
            
            # Verify workflow state shows successful completion with fallback
            workflow_state = response_body['workflow_state']
            assert workflow_state['articles_fetched'] is True
            assert workflow_state['summary_generated'] is True
            assert workflow_state['summary_published'] is True
            
            # Verify fallback summary was published
            mock_publisher.publish_summary.assert_called_once()
            published_summary = mock_publisher.publish_summary.call_args[0][0]
            assert "Recent Generative AI developments" in published_summary.summary
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_workflow_with_publishing_failure_and_fallback(
        self, 
        mock_environment, 
        sample_articles, 
        sample_summary, 
        lambda_event, 
        lambda_context
    ):
        """Test workflow with publishing failure and fallback attempts."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Configure successful workflow until publishing
            mock_fetcher.fetch_news.return_value = sample_articles
            mock_fetcher.filter_articles.return_value = sample_articles
            mock_summarizer.generate_summary.return_value = sample_summary
            
            # Configure publishing to fail initially then succeed on fallback
            mock_publisher.publish_summary.side_effect = [False, True]  # Fail then succeed
            
            # Execute the workflow
            handler = LambdaHandler()
            response = await handler.handler(lambda_event, lambda_context)
            
            # Verify response indicates successful completion
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert 'AI News Agent executed successfully' in response_body['message']
            
            # Verify publishing was attempted multiple times (original + fallback)
            assert mock_publisher.publish_summary.call_count == 2
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_workflow_performance_under_load(
        self, 
        mock_environment, 
        lambda_event, 
        lambda_context
    ):
        """Test workflow performance with large number of articles."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create a large set of articles to test performance
        large_article_set = []
        now = datetime.now(timezone.utc)
        
        for i in range(50):  # Create 50 articles
            article = NewsArticle(
                title=f"AI Development News Article {i+1}",
                content=f"This is article {i+1} about generative AI developments. " * 10,  # Longer content
                url=f"https://example.com/article-{i+1}",
                published_at=now - timedelta(hours=i),
                source=f"News Source {i % 5 + 1}",
                relevance_score=0.7 + (i % 3) * 0.1
            )
            large_article_set.append(article)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Configure mocks with large dataset
            mock_fetcher.fetch_news.return_value = large_article_set
            mock_fetcher.filter_articles.return_value = large_article_set
            
            # Create a summary for the large dataset
            large_summary = NewsSummary(
                summary="Comprehensive summary of 50 AI-related articles covering recent developments.",
                key_points=[f"Key point {i+1}" for i in range(10)],
                sources=[ArticleSource(
                    title=article.title,
                    url=article.url,
                    source=article.source,
                    published_at=article.published_at
                ) for article in large_article_set[:10]],  # Limit sources for performance
                generated_at=datetime.now(timezone.utc),
                article_count=50
            )
            
            mock_summarizer.generate_summary.return_value = large_summary
            mock_publisher.publish_summary.return_value = True
            
            # Execute the workflow and measure performance
            handler = LambdaHandler()
            start_time = time.time()
            response = await handler.handler(lambda_event, lambda_context)
            execution_time = time.time() - start_time
            
            # Verify successful completion
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert response_body['article_count'] == 50
            
            # Verify performance is acceptable (should complete within 60 seconds even with large dataset)
            assert execution_time < 60.0
            
            # Log performance metrics for monitoring
            print(f"Performance test completed in {execution_time:.2f} seconds with 50 articles")


class TestWorkflowErrorHandling:
    """Integration tests for error handling and recovery scenarios."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_complete_service_failure_handling(
        self, 
        mock_environment, 
        lambda_event, 
        lambda_context
    ):
        """Test handling when all services fail."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure all services to fail
            mock_fetcher_class.side_effect = Exception("News service unavailable")
            mock_summarizer_class.side_effect = Exception("AI service unavailable")
            mock_publisher_class.side_effect = Exception("SNS service unavailable")
            
            # Execute the workflow
            handler = LambdaHandler()
            response = await handler.handler(lambda_event, lambda_context)
            
            # Verify error response
            assert response['statusCode'] in [500, 206]  # Error or partial success
            response_body = json.loads(response['body'])
            
            # Verify error information is included
            assert 'error' in response_body or 'errors' in response_body.get('workflow_state', {})
            assert response_body['correlation_id'] == 'test-integration-123'
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_timeout_handling(
        self, 
        mock_environment, 
        lambda_event, 
        lambda_context
    ):
        """Test handling of service timeouts."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Mock context with very short remaining time
        lambda_context.remaining_time_in_millis = lambda: 1000  # 1 second remaining
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Configure slow responses to simulate timeout scenarios
            async def slow_fetch(*args, **kwargs):
                await asyncio.sleep(2)  # Longer than remaining time
                return []
            
            mock_fetcher.fetch_news.side_effect = slow_fetch
            
            # Execute the workflow
            handler = LambdaHandler()
            start_time = time.time()
            response = await handler.handler(lambda_event, lambda_context)
            execution_time = time.time() - start_time
            
            # Verify the workflow handles timeout gracefully
            # (Implementation may vary based on timeout handling strategy)
            assert response['statusCode'] in [200, 206, 500]
            assert execution_time < 10.0  # Should not hang indefinitely


class TestWorkflowIntegrationWithMockServices:
    """Integration tests using more realistic mock services."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_realistic_news_fetching_simulation(
        self, 
        mock_environment, 
        lambda_event, 
        lambda_context
    ):
        """Test with realistic news fetching simulation including API delays."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mock instances with realistic delays
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            # Simulate realistic API delays
            async def realistic_fetch(*args, **kwargs):
                await asyncio.sleep(0.5)  # Simulate API call delay
                return [
                    NewsArticle(
                        title="Real-time AI News Update",
                        content="Breaking news about AI developments",
                        url="https://example.com/breaking-ai-news",
                        published_at=datetime.now(timezone.utc),
                        source="AI News Network",
                        relevance_score=0.9
                    )
                ]
            
            async def realistic_summarize(*args, **kwargs):
                await asyncio.sleep(1.0)  # Simulate AI processing delay
                return NewsSummary(
                    summary="AI continues to advance rapidly with new developments.",
                    key_points=["Major AI breakthrough announced"],
                    sources=[ArticleSource(
                        title="Real-time AI News Update",
                        url="https://example.com/breaking-ai-news",
                        source="AI News Network",
                        published_at=datetime.now(timezone.utc)
                    )],
                    generated_at=datetime.now(timezone.utc),
                    article_count=1
                )
            
            async def realistic_publish(*args, **kwargs):
                await asyncio.sleep(0.3)  # Simulate SNS publishing delay
                return True
            
            mock_fetcher.fetch_news.side_effect = realistic_fetch
            mock_fetcher.filter_articles.return_value = await realistic_fetch()
            mock_summarizer.generate_summary.side_effect = realistic_summarize
            mock_publisher.publish_summary.side_effect = realistic_publish
            
            # Execute the workflow
            handler = LambdaHandler()
            start_time = time.time()
            response = await handler.handler(lambda_event, lambda_context)
            execution_time = time.time() - start_time
            
            # Verify successful completion with realistic timing
            assert response['statusCode'] == 200
            assert execution_time >= 1.8  # Should take at least sum of delays
            assert execution_time < 10.0  # But not too long
            
            response_body = json.loads(response['body'])
            assert response_body['article_count'] == 1
            assert 'AI News Agent executed successfully' in response_body['message']


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
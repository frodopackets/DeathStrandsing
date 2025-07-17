"""Performance and memory usage integration tests for AI News Agent."""

import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from typing import List

from src.aws_lambda.handler import LambdaHandler
from src.models import NewsArticle, NewsSummary, ArticleSource


class PerformanceMonitor:
    """Helper class to monitor performance metrics during tests."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process(os.getpid())
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def get_metrics(self):
        """Get current performance metrics."""
        if self.start_time is None:
            return None
        
        current_time = time.time()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'execution_time': current_time - self.start_time,
            'memory_usage_mb': current_memory,
            'memory_increase_mb': current_memory - self.start_memory,
            'cpu_percent': self.process.cpu_percent()
        }


@pytest.fixture
def performance_monitor():
    """Create a performance monitor for tests."""
    return PerformanceMonitor()


@pytest.fixture
def mock_environment():
    """Mock environment variables for performance testing."""
    return {
        'SEARCH_QUERY': 'Generative AI',
        'TIME_RANGE_HOURS': '72',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:perf-test-topic',
        'MAX_ARTICLES': '100',  # Higher limit for performance testing
        'SUMMARY_LENGTH': 'medium',
        'MODEL_NAME': 'amazon.nova-pro-v1:0',
        'MODEL_PROVIDER': 'bedrock'
    }


def create_large_article_dataset(count: int) -> List[NewsArticle]:
    """Create a large dataset of articles for performance testing."""
    articles = []
    now = datetime.now(timezone.utc)
    
    for i in range(count):
        # Create articles with varying content sizes
        content_multiplier = (i % 5) + 1  # 1-5x content size
        content = f"This is article {i+1} about generative AI and machine learning developments. " * (content_multiplier * 20)
        
        article = NewsArticle(
            title=f"AI Development Article {i+1}: Advanced Machine Learning Techniques",
            content=content,
            url=f"https://example.com/ai-article-{i+1}",
            published_at=now - timedelta(hours=i % 72),  # Spread across 72 hours
            source=f"AI News Source {i % 10 + 1}",
            relevance_score=0.5 + (i % 5) * 0.1  # Varying relevance scores
        )
        articles.append(article)
    
    return articles


class TestLambdaPerformance:
    """Performance tests for Lambda function execution."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_lambda_execution_time_with_small_dataset(
        self, 
        mock_environment, 
        performance_monitor
    ):
        """Test Lambda execution time with small dataset (10 articles)."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create small dataset
        small_articles = create_large_article_dataset(10)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mocks
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            mock_fetcher.fetch_news.return_value = small_articles
            mock_fetcher.filter_articles.return_value = small_articles
            
            # Create summary
            summary = NewsSummary(
                summary="Summary of 10 AI articles",
                key_points=[f"Key point {i+1}" for i in range(5)],
                sources=[ArticleSource(
                    title=article.title,
                    url=article.url,
                    source=article.source,
                    published_at=article.published_at
                ) for article in small_articles[:5]],
                generated_at=datetime.now(timezone.utc),
                article_count=10
            )
            
            mock_summarizer.generate_summary.return_value = summary
            mock_publisher.publish_summary.return_value = True
            
            # Start monitoring
            performance_monitor.start_monitoring()
            
            # Execute Lambda
            handler = LambdaHandler()
            event = {'correlation_id': 'perf-test-small'}
            context = Mock()
            context.remaining_time_in_millis = lambda: 300000
            
            response = await handler.handler(event, context)
            
            # Get performance metrics
            metrics = performance_monitor.get_metrics()
            
            # Verify performance requirements
            assert response['statusCode'] == 200
            assert metrics['execution_time'] < 5.0  # Should complete within 5 seconds
            assert metrics['memory_increase_mb'] < 50  # Should not use more than 50MB additional memory
            
            print(f"Small dataset performance: {metrics['execution_time']:.2f}s, "
                  f"{metrics['memory_increase_mb']:.1f}MB memory increase")
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_lambda_execution_time_with_medium_dataset(
        self, 
        mock_environment, 
        performance_monitor
    ):
        """Test Lambda execution time with medium dataset (50 articles)."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create medium dataset
        medium_articles = create_large_article_dataset(50)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mocks
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            mock_fetcher.fetch_news.return_value = medium_articles
            mock_fetcher.filter_articles.return_value = medium_articles
            
            # Create summary
            summary = NewsSummary(
                summary="Summary of 50 AI articles with comprehensive analysis",
                key_points=[f"Key point {i+1}" for i in range(8)],
                sources=[ArticleSource(
                    title=article.title,
                    url=article.url,
                    source=article.source,
                    published_at=article.published_at
                ) for article in medium_articles[:10]],
                generated_at=datetime.now(timezone.utc),
                article_count=50
            )
            
            mock_summarizer.generate_summary.return_value = summary
            mock_publisher.publish_summary.return_value = True
            
            # Start monitoring
            performance_monitor.start_monitoring()
            
            # Execute Lambda
            handler = LambdaHandler()
            event = {'correlation_id': 'perf-test-medium'}
            context = Mock()
            context.remaining_time_in_millis = lambda: 300000
            
            response = await handler.handler(event, context)
            
            # Get performance metrics
            metrics = performance_monitor.get_metrics()
            
            # Verify performance requirements
            assert response['statusCode'] == 200
            assert metrics['execution_time'] < 15.0  # Should complete within 15 seconds
            assert metrics['memory_increase_mb'] < 100  # Should not use more than 100MB additional memory
            
            print(f"Medium dataset performance: {metrics['execution_time']:.2f}s, "
                  f"{metrics['memory_increase_mb']:.1f}MB memory increase")
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_lambda_execution_time_with_large_dataset(
        self, 
        mock_environment, 
        performance_monitor
    ):
        """Test Lambda execution time with large dataset (100 articles)."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create large dataset
        large_articles = create_large_article_dataset(100)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mocks
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            mock_fetcher.fetch_news.return_value = large_articles
            mock_fetcher.filter_articles.return_value = large_articles
            
            # Create summary
            summary = NewsSummary(
                summary="Comprehensive summary of 100 AI articles covering recent developments across multiple domains",
                key_points=[f"Key point {i+1}" for i in range(10)],
                sources=[ArticleSource(
                    title=article.title,
                    url=article.url,
                    source=article.source,
                    published_at=article.published_at
                ) for article in large_articles[:15]],
                generated_at=datetime.now(timezone.utc),
                article_count=100
            )
            
            mock_summarizer.generate_summary.return_value = summary
            mock_publisher.publish_summary.return_value = True
            
            # Start monitoring
            performance_monitor.start_monitoring()
            
            # Execute Lambda
            handler = LambdaHandler()
            event = {'correlation_id': 'perf-test-large'}
            context = Mock()
            context.remaining_time_in_millis = lambda: 300000
            
            response = await handler.handler(event, context)
            
            # Get performance metrics
            metrics = performance_monitor.get_metrics()
            
            # Verify performance requirements
            assert response['statusCode'] == 200
            assert metrics['execution_time'] < 30.0  # Should complete within 30 seconds
            assert metrics['memory_increase_mb'] < 200  # Should not use more than 200MB additional memory
            
            print(f"Large dataset performance: {metrics['execution_time']:.2f}s, "
                  f"{metrics['memory_increase_mb']:.1f}MB memory increase")


class TestMemoryUsage:
    """Memory usage tests for different scenarios."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_memory_usage_with_concurrent_operations(
        self, 
        mock_environment, 
        performance_monitor
    ):
        """Test memory usage when multiple operations run concurrently."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create dataset
        articles = create_large_article_dataset(30)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mocks with delays to simulate concurrent processing
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            async def delayed_fetch(*args, **kwargs):
                await asyncio.sleep(0.1)
                return articles
            
            async def delayed_summarize(*args, **kwargs):
                await asyncio.sleep(0.2)
                return NewsSummary(
                    summary="Concurrent processing test summary",
                    key_points=["Concurrent point 1", "Concurrent point 2"],
                    sources=[ArticleSource(
                        title=article.title,
                        url=article.url,
                        source=article.source,
                        published_at=article.published_at
                    ) for article in articles[:5]],
                    generated_at=datetime.now(timezone.utc),
                    article_count=30
                )
            
            async def delayed_publish(*args, **kwargs):
                await asyncio.sleep(0.1)
                return True
            
            mock_fetcher.fetch_news.side_effect = delayed_fetch
            mock_fetcher.filter_articles.side_effect = delayed_fetch
            mock_summarizer.generate_summary.side_effect = delayed_summarize
            mock_publisher.publish_summary.side_effect = delayed_publish
            
            # Start monitoring
            performance_monitor.start_monitoring()
            
            # Execute multiple concurrent Lambda invocations
            handler = LambdaHandler()
            
            tasks = []
            for i in range(3):  # 3 concurrent executions
                event = {'correlation_id': f'concurrent-test-{i}'}
                context = Mock()
                context.remaining_time_in_millis = lambda: 300000
                
                task = asyncio.create_task(handler.handler(event, context))
                tasks.append(task)
            
            # Wait for all tasks to complete
            responses = await asyncio.gather(*tasks)
            
            # Get performance metrics
            metrics = performance_monitor.get_metrics()
            
            # Verify all executions succeeded
            for response in responses:
                assert response['statusCode'] == 200
            
            # Verify memory usage is reasonable for concurrent operations
            assert metrics['memory_increase_mb'] < 300  # Should not exceed 300MB for 3 concurrent operations
            
            print(f"Concurrent operations memory usage: {metrics['memory_increase_mb']:.1f}MB")
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_memory_cleanup_after_execution(
        self, 
        mock_environment, 
        performance_monitor
    ):
        """Test that memory is properly cleaned up after execution."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create dataset
        articles = create_large_article_dataset(50)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mocks
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            mock_fetcher.fetch_news.return_value = articles
            mock_fetcher.filter_articles.return_value = articles
            mock_summarizer.generate_summary.return_value = NewsSummary(
                summary="Memory cleanup test summary",
                key_points=["Memory point 1", "Memory point 2"],
                sources=[ArticleSource(
                    title=article.title,
                    url=article.url,
                    source=article.source,
                    published_at=article.published_at
                ) for article in articles[:5]],
                generated_at=datetime.now(timezone.utc),
                article_count=50
            )
            mock_publisher.publish_summary.return_value = True
            
            # Measure baseline memory
            baseline_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            
            # Execute Lambda multiple times
            handler = LambdaHandler()
            
            for i in range(5):  # 5 sequential executions
                event = {'correlation_id': f'cleanup-test-{i}'}
                context = Mock()
                context.remaining_time_in_millis = lambda: 300000
                
                response = await handler.handler(event, context)
                assert response['statusCode'] == 200
                
                # Force garbage collection
                import gc
                gc.collect()
            
            # Measure final memory
            final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            memory_increase = final_memory - baseline_memory
            
            # Verify memory increase is reasonable (should not grow significantly with each execution)
            assert memory_increase < 100  # Should not increase by more than 100MB after 5 executions
            
            print(f"Memory increase after 5 executions: {memory_increase:.1f}MB")


class TestLambdaTimeoutHandling:
    """Tests for Lambda timeout scenarios."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ')
    async def test_execution_within_lambda_timeout_limits(
        self, 
        mock_environment
    ):
        """Test that execution completes within typical Lambda timeout limits."""
        # Set up environment
        import os
        os.environ.update(mock_environment)
        
        # Create realistic dataset
        articles = create_large_article_dataset(25)
        
        with patch('src.services.GoogleNewsFetcher') as mock_fetcher_class, \
             patch('src.services.StrandsAISummarizer') as mock_summarizer_class, \
             patch('src.services.AWSNSPublisher') as mock_publisher_class:
            
            # Configure mocks with realistic delays
            mock_fetcher = AsyncMock()
            mock_summarizer = AsyncMock()
            mock_publisher = AsyncMock()
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_summarizer_class.return_value = mock_summarizer
            mock_publisher_class.return_value = mock_publisher
            
            async def realistic_fetch(*args, **kwargs):
                await asyncio.sleep(1.0)  # 1 second for news fetching
                return articles
            
            async def realistic_summarize(*args, **kwargs):
                await asyncio.sleep(2.0)  # 2 seconds for AI summarization
                return NewsSummary(
                    summary="Realistic timeout test summary",
                    key_points=["Timeout point 1", "Timeout point 2"],
                    sources=[ArticleSource(
                        title=article.title,
                        url=article.url,
                        source=article.source,
                        published_at=article.published_at
                    ) for article in articles[:5]],
                    generated_at=datetime.now(timezone.utc),
                    article_count=25
                )
            
            async def realistic_publish(*args, **kwargs):
                await asyncio.sleep(0.5)  # 0.5 seconds for SNS publishing
                return True
            
            mock_fetcher.fetch_news.side_effect = realistic_fetch
            mock_fetcher.filter_articles.return_value = articles
            mock_summarizer.generate_summary.side_effect = realistic_summarize
            mock_publisher.publish_summary.side_effect = realistic_publish
            
            # Execute with timeout monitoring
            handler = LambdaHandler()
            event = {'correlation_id': 'timeout-test'}
            context = Mock()
            
            # Simulate 5-minute Lambda timeout
            start_time = time.time()
            context.remaining_time_in_millis = lambda: max(0, int((start_time + 300 - time.time()) * 1000))
            
            start_execution = time.time()
            response = await handler.handler(event, context)
            execution_time = time.time() - start_execution
            
            # Verify successful completion within timeout
            assert response['statusCode'] == 200
            assert execution_time < 300  # Should complete within 5 minutes
            assert execution_time > 3.0   # Should take at least 3 seconds (sum of delays)
            
            print(f"Execution completed in {execution_time:.2f} seconds (within Lambda timeout)")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s"])
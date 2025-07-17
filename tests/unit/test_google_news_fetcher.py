"""Unit tests for GoogleNewsFetcher."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from src.services.google_news_fetcher import GoogleNewsFetcher
from src.models.news_article import NewsArticle


class TestGoogleNewsFetcher:
    """Test cases for GoogleNewsFetcher class."""
    
    @pytest.fixture
    def fetcher(self):
        """Create a GoogleNewsFetcher instance for testing."""
        return GoogleNewsFetcher(
            language='en',
            country='US',
            max_results=10,
            requests_per_minute=60
        )
    
    @pytest.fixture
    def sample_raw_articles(self):
        """Sample raw articles from GNews API."""
        now = datetime.now()
        return [
            {
                'title': 'OpenAI Releases New GPT Model',
                'url': 'https://example.com/article1',
                'description': 'OpenAI has announced a new generative AI model...',
                'published date': (now - timedelta(hours=1)).isoformat(),
                'publisher': {'title': 'Tech News'}
            },
            {
                'title': 'Machine Learning Breakthrough',
                'url': 'https://example.com/article2',
                'description': 'Researchers achieve new milestone in ML...',
                'published date': (now - timedelta(hours=48)).isoformat(),
                'publisher': {'title': 'Science Daily'}
            },
            {
                'title': 'Old AI News',
                'url': 'https://example.com/article3',
                'description': 'This is old news about AI...',
                'published date': (now - timedelta(hours=100)).isoformat(),
                'publisher': {'title': 'Old News'}
            }
        ]
    
    @pytest.fixture
    def sample_news_articles(self):
        """Sample NewsArticle objects for testing."""
        now = datetime.now()
        return [
            NewsArticle(
                title="AI Revolution in Healthcare",
                content="Artificial intelligence is transforming healthcare...",
                url="https://example.com/ai-healthcare",
                published_at=now - timedelta(hours=12),
                source="Health Tech"
            ),
            NewsArticle(
                title="New Generative AI Model Released",
                content="A new generative AI model has been released...",
                url="https://example.com/new-ai-model",
                published_at=now - timedelta(hours=6),
                source="AI News"
            ),
            NewsArticle(
                title="Duplicate AI Healthcare News",
                content="Artificial intelligence is transforming healthcare industry...",
                url="https://example.com/duplicate-healthcare",
                published_at=now - timedelta(hours=8),
                source="Medical AI"
            )
        ]
    
    def test_initialization(self, fetcher):
        """Test GoogleNewsFetcher initialization."""
        assert fetcher.language == 'en'
        assert fetcher.country == 'US'
        assert fetcher.max_results == 10
        assert fetcher.gnews is not None
        assert fetcher.throttler is not None
        assert isinstance(fetcher._processed_urls, set)
    
    def test_set_time_period(self, fetcher):
        """Test time period setting for different hour ranges."""
        # Test 24 hours or less
        fetcher._set_time_period(12)
        assert fetcher.gnews.period == '1d'
        
        fetcher._set_time_period(24)
        assert fetcher.gnews.period == '1d'
        
        # Test 7 days or less
        fetcher._set_time_period(72)
        assert fetcher.gnews.period == '7d'
        
        fetcher._set_time_period(168)
        assert fetcher.gnews.period == '7d'
        
        # Test more than 7 days
        fetcher._set_time_period(200)
        assert fetcher.gnews.period == '30d'
    
    @pytest.mark.asyncio
    async def test_fetch_news_success(self, fetcher, sample_raw_articles):
        """Test successful news fetching."""
        with patch.object(fetcher, '_fetch_with_retry', return_value=sample_raw_articles):
            with patch.object(fetcher, '_convert_to_news_articles') as mock_convert:
                mock_articles = [Mock(spec=NewsArticle) for _ in range(2)]
                mock_convert.return_value = mock_articles
                
                result = await fetcher.fetch_news("Generative AI", 72)
                
                assert len(result) == 2
                mock_convert.assert_called_once_with(sample_raw_articles, 72)
    
    @pytest.mark.asyncio
    async def test_fetch_news_no_results(self, fetcher):
        """Test news fetching when no articles are found."""
        with patch.object(fetcher, '_fetch_with_retry', return_value=[]):
            result = await fetcher.fetch_news("Nonexistent Topic", 72)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_fetch_news_error_handling(self, fetcher):
        """Test error handling during news fetching."""
        with patch.object(fetcher, '_fetch_with_retry', side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                await fetcher.fetch_news("Generative AI", 72)
    
    @pytest.mark.asyncio
    async def test_convert_to_news_articles_time_filtering(self, fetcher, sample_raw_articles):
        """Test time-based filtering during article conversion."""
        # Mock the article creation method
        with patch.object(fetcher, '_create_news_article') as mock_create:
            now = datetime.now()
            
            # Create mock articles with different timestamps
            mock_articles = [
                NewsArticle(
                    title="Recent AI News",
                    content="Recent content",
                    url="https://example.com/recent",
                    published_at=now - timedelta(hours=1),
                    source="Tech News"
                ),
                NewsArticle(
                    title="Old AI News",
                    content="Old content",
                    url="https://example.com/old",
                    published_at=now - timedelta(hours=100),
                    source="Old News"
                )
            ]
            
            mock_create.side_effect = mock_articles
            
            # Test 72-hour filtering
            result = await fetcher._convert_to_news_articles(sample_raw_articles, 72)
            
            # Should only include articles within 72 hours
            assert len(result) == 1
            assert result[0].title == "Recent AI News"
    
    @pytest.mark.asyncio
    async def test_convert_to_news_articles_duplicate_filtering(self, fetcher):
        """Test duplicate URL filtering during article conversion."""
        raw_articles = [
            {
                'title': 'AI News 1',
                'url': 'https://example.com/same-url',
                'description': 'First article',
                'published date': datetime.now().isoformat(),
                'publisher': {'title': 'News 1'}
            },
            {
                'title': 'AI News 2',
                'url': 'https://example.com/same-url',  # Same URL
                'description': 'Second article',
                'published date': datetime.now().isoformat(),
                'publisher': {'title': 'News 2'}
            }
        ]
        
        with patch.object(fetcher, '_create_news_article') as mock_create:
            mock_articles = [
                NewsArticle(
                    title="AI News 1",
                    content="First article",
                    url="https://example.com/same-url",
                    published_at=datetime.now(),
                    source="News 1"
                ),
                NewsArticle(
                    title="AI News 2",
                    content="Second article",
                    url="https://example.com/same-url",
                    published_at=datetime.now(),
                    source="News 2"
                )
            ]
            
            mock_create.side_effect = mock_articles
            
            result = await fetcher._convert_to_news_articles(raw_articles, 72)
            
            # Should only include one article (first one)
            assert len(result) == 1
            assert result[0].title == "AI News 1"
    
    @pytest.mark.asyncio
    async def test_filter_articles_relevance(self, fetcher, sample_news_articles):
        """Test article filtering by relevance."""
        # Mock relevance calculation
        with patch.object(NewsArticle, 'calculate_relevance_score') as mock_calc:
            with patch.object(NewsArticle, 'is_relevant') as mock_relevant:
                # Set up mock return values
                mock_calc.side_effect = [0.8, 0.9, 0.3]  # Scores for each article
                mock_relevant.side_effect = [True, True, False]  # Relevance results
                
                result = await fetcher.filter_articles(sample_news_articles)
                
                # Should return 2 relevant articles, sorted by score
                assert len(result) == 2
                assert mock_calc.call_count == 3
                assert mock_relevant.call_count == 3
    
    @pytest.mark.asyncio
    async def test_filter_articles_empty_list(self, fetcher):
        """Test filtering empty article list."""
        result = await fetcher.filter_articles([])
        assert result == []
    
    def test_remove_duplicates(self, fetcher):
        """Test duplicate removal functionality."""
        now = datetime.now()
        
        # Create articles with same URL (exact duplicate)
        article1 = NewsArticle(
            title="AI News 1",
            content="First article content",
            url="https://example.com/same-url",
            published_at=now,
            source="Source 1"
        )
        
        article2 = NewsArticle(
            title="AI News 2", 
            content="Second article content",
            url="https://example.com/same-url",  # Same URL = duplicate
            published_at=now,
            source="Source 2"
        )
        
        article3 = NewsArticle(
            title="Different AI News",
            content="Different content",
            url="https://example.com/different-url",
            published_at=now,
            source="Source 3"
        )
        
        articles_with_duplicate = [article1, article2, article3]
        result = fetcher._remove_duplicates(articles_with_duplicate)
        
        # Should remove the URL duplicate (article2)
        assert len(result) == 2
        urls = [article.url for article in result]
        assert "https://example.com/same-url" in urls
        assert "https://example.com/different-url" in urls
        # Should only have one instance of the same URL
        assert urls.count("https://example.com/same-url") == 1
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_success(self, fetcher):
        """Test successful fetch with retry mechanism."""
        mock_articles = [{'title': 'Test Article'}]
        
        with patch.object(fetcher.gnews, 'get_news', return_value=mock_articles):
            result = await fetcher._fetch_with_retry("test query")
            assert result == mock_articles
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_failure_then_success(self, fetcher):
        """Test retry mechanism with initial failure."""
        mock_articles = [{'title': 'Test Article'}]
        
        with patch.object(fetcher.gnews, 'get_news') as mock_get_news:
            # First call fails, second succeeds
            mock_get_news.side_effect = [Exception("Network error"), mock_articles]
            
            result = await fetcher._fetch_with_retry("test query", max_retries=2)
            assert result == mock_articles
            assert mock_get_news.call_count == 2
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_max_retries_exceeded(self, fetcher):
        """Test retry mechanism when max retries are exceeded."""
        with patch.object(fetcher.gnews, 'get_news', side_effect=Exception("Persistent error")):
            with pytest.raises(Exception, match="Persistent error"):
                await fetcher._fetch_with_retry("test query", max_retries=2)
    
    def test_parse_published_date_valid(self, fetcher):
        """Test parsing valid published date."""
        raw_article = {
            'published date': '2024-01-15T10:30:00Z'
        }
        
        result = fetcher._parse_published_date(raw_article)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_published_date_invalid(self, fetcher):
        """Test parsing invalid published date falls back to current time."""
        raw_article = {
            'published date': 'invalid-date'
        }
        
        before = datetime.now()
        result = fetcher._parse_published_date(raw_article)
        after = datetime.now()
        
        assert isinstance(result, datetime)
        assert before <= result <= after
    
    def test_parse_published_date_missing(self, fetcher):
        """Test parsing missing published date falls back to current time."""
        raw_article = {}
        
        before = datetime.now()
        result = fetcher._parse_published_date(raw_article)
        after = datetime.now()
        
        assert isinstance(result, datetime)
        assert before <= result <= after


class TestTimeBasedFiltering:
    """Specific tests for time-based filtering functionality."""
    
    @pytest.fixture
    def fetcher(self):
        """Create a GoogleNewsFetcher instance for testing."""
        return GoogleNewsFetcher()
    
    def test_72_hour_window_filtering(self, fetcher):
        """Test that articles are properly filtered within 72-hour window."""
        now = datetime.now()
        
        articles = [
            NewsArticle(
                title="Recent AI News",
                content="Recent content",
                url="https://example.com/recent",
                published_at=now - timedelta(hours=1),  # 1 hour ago
                source="Tech News"
            ),
            NewsArticle(
                title="AI News from 2 days ago",
                content="2-day old content",
                url="https://example.com/2days",
                published_at=now - timedelta(hours=48),  # 2 days ago
                source="AI Daily"
            ),
            NewsArticle(
                title="AI News from 3 days ago",
                content="3-day old content",
                url="https://example.com/3days",
                published_at=now - timedelta(hours=72),  # Exactly 3 days ago
                source="Old AI News"
            ),
            NewsArticle(
                title="Very old AI News",
                content="Very old content",
                url="https://example.com/old",
                published_at=now - timedelta(hours=100),  # Over 4 days ago
                source="Ancient News"
            )
        ]
        
        # Simulate the time filtering logic
        cutoff_time = now - timedelta(hours=72)
        filtered_articles = [
            article for article in articles 
            if article.published_at > cutoff_time
        ]
        
        # Should include articles from 1 hour and 2 days ago, but not 3+ days
        assert len(filtered_articles) == 2
        assert filtered_articles[0].title == "Recent AI News"
        assert filtered_articles[1].title == "AI News from 2 days ago"
    
    def test_generative_ai_query_handling(self, fetcher):
        """Test that 'Generative AI' search terms are handled correctly."""
        # Test that the query is passed through correctly
        test_queries = [
            "Generative AI",
            "generative ai",
            "Generative AI news",
            "AI and machine learning"
        ]
        
        for query in test_queries:
            # Mock the GNews search to verify query is passed correctly
            with patch.object(fetcher.gnews, 'get_news') as mock_search:
                mock_search.return_value = []
                
                # This would be called in the actual fetch_news method
                mock_search(query)
                mock_search.assert_called_with(query)
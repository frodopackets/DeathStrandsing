"""Unit tests for NewsArticle model."""

import pytest
from datetime import datetime, timezone
from src.models.news_article import NewsArticle


class TestNewsArticle:
    """Test cases for NewsArticle model."""
    
    def test_valid_article_creation(self):
        """Test creating a valid NewsArticle."""
        article = NewsArticle(
            title="AI Breakthrough in 2024",
            content="This is a test article about artificial intelligence developments.",
            url="https://example.com/ai-news",
            published_at=datetime.now(timezone.utc),
            source="Tech News"
        )
        
        assert article.title == "AI Breakthrough in 2024"
        assert article.content == "This is a test article about artificial intelligence developments."
        assert article.url == "https://example.com/ai-news"
        assert article.source == "Tech News"
        assert article.id is not None
        assert article.relevance_score is None
    
    def test_article_id_generation(self):
        """Test that unique IDs are generated when not provided."""
        article1 = NewsArticle(
            title="Test Article 1",
            content="Content 1",
            url="https://example.com/1",
            published_at=datetime.now(timezone.utc),
            source="Source 1"
        )
        
        article2 = NewsArticle(
            title="Test Article 2",
            content="Content 2",
            url="https://example.com/2",
            published_at=datetime.now(timezone.utc),
            source="Source 2"
        )
        
        assert article1.id != article2.id
        assert len(article1.id) > 0
        assert len(article2.id) > 0
    
    def test_custom_id_preserved(self):
        """Test that custom IDs are preserved."""
        custom_id = "custom-123"
        article = NewsArticle(
            title="Test Article",
            content="Test content",
            url="https://example.com/test",
            published_at=datetime.now(timezone.utc),
            source="Test Source",
            id=custom_id
        )
        
        assert article.id == custom_id
    
    def test_empty_title_validation(self):
        """Test validation fails for empty title."""
        with pytest.raises(ValueError, match="Article title cannot be empty"):
            NewsArticle(
                title="",
                content="Test content",
                url="https://example.com/test",
                published_at=datetime.now(timezone.utc),
                source="Test Source"
            )
    
    def test_empty_content_validation(self):
        """Test validation fails for empty content."""
        with pytest.raises(ValueError, match="Article content cannot be empty"):
            NewsArticle(
                title="Test Title",
                content="",
                url="https://example.com/test",
                published_at=datetime.now(timezone.utc),
                source="Test Source"
            )
    
    def test_empty_url_validation(self):
        """Test validation fails for empty URL."""
        with pytest.raises(ValueError, match="Article URL cannot be empty"):
            NewsArticle(
                title="Test Title",
                content="Test content",
                url="",
                published_at=datetime.now(timezone.utc),
                source="Test Source"
            )
    
    def test_invalid_url_validation(self):
        """Test validation fails for invalid URL format."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            NewsArticle(
                title="Test Title",
                content="Test content",
                url="not-a-valid-url",
                published_at=datetime.now(timezone.utc),
                source="Test Source"
            )
    
    def test_empty_source_validation(self):
        """Test validation fails for empty source."""
        with pytest.raises(ValueError, match="Article source cannot be empty"):
            NewsArticle(
                title="Test Title",
                content="Test content",
                url="https://example.com/test",
                published_at=datetime.now(timezone.utc),
                source=""
            )
    
    def test_invalid_published_date_validation(self):
        """Test validation fails for invalid published date."""
        with pytest.raises(ValueError, match="Published date must be a datetime object"):
            NewsArticle(
                title="Test Title",
                content="Test content",
                url="https://example.com/test",
                published_at="not-a-datetime",
                source="Test Source"
            )
    
    def test_invalid_relevance_score_type(self):
        """Test validation fails for invalid relevance score type."""
        with pytest.raises(ValueError, match="Relevance score must be a number"):
            NewsArticle(
                title="Test Title",
                content="Test content",
                url="https://example.com/test",
                published_at=datetime.now(timezone.utc),
                source="Test Source",
                relevance_score="not-a-number"
            )
    
    def test_relevance_score_out_of_range(self):
        """Test validation fails for relevance score out of range."""
        with pytest.raises(ValueError, match="Relevance score must be between 0.0 and 1.0"):
            NewsArticle(
                title="Test Title",
                content="Test content",
                url="https://example.com/test",
                published_at=datetime.now(timezone.utc),
                source="Test Source",
                relevance_score=1.5
            )
    
    def test_valid_relevance_score(self):
        """Test valid relevance score is accepted."""
        article = NewsArticle(
            title="Test Title",
            content="Test content",
            url="https://example.com/test",
            published_at=datetime.now(timezone.utc),
            source="Test Source",
            relevance_score=0.8
        )
        
        assert article.relevance_score == 0.8
    
    def test_calculate_relevance_score_high(self):
        """Test relevance score calculation for AI-related content."""
        article = NewsArticle(
            title="ChatGPT and Artificial Intelligence Revolution",
            content="This article discusses machine learning, neural networks, and generative AI developments.",
            url="https://example.com/ai-news",
            published_at=datetime.now(timezone.utc),
            source="AI Weekly"
        )
        
        score = article.calculate_relevance_score()
        assert score > 0.1  # Should have decent relevance
        assert article.relevance_score == score
    
    def test_calculate_relevance_score_low(self):
        """Test relevance score calculation for non-AI content."""
        article = NewsArticle(
            title="Weather Update for Tomorrow",
            content="It will be sunny with a chance of rain in the afternoon.",
            url="https://example.com/weather",
            published_at=datetime.now(timezone.utc),
            source="Weather Channel"
        )
        
        score = article.calculate_relevance_score()
        assert score < 0.1  # Should have low relevance
        assert article.relevance_score == score
    
    def test_is_relevant_with_threshold(self):
        """Test relevance checking with custom threshold."""
        ai_article = NewsArticle(
            title="OpenAI GPT-4 Release",
            content="New large language model with improved capabilities.",
            url="https://example.com/gpt4",
            published_at=datetime.now(timezone.utc),
            source="Tech News"
        )
        
        weather_article = NewsArticle(
            title="Weather Forecast",
            content="Sunny skies expected.",
            url="https://example.com/weather",
            published_at=datetime.now(timezone.utc),
            source="Weather"
        )
        
        assert ai_article.is_relevant(threshold=0.1)
        assert not weather_article.is_relevant(threshold=0.1)
    
    def test_duplicate_detection_same_url(self):
        """Test duplicate detection for same URL."""
        article1 = NewsArticle(
            title="AI News",
            content="Content about AI",
            url="https://example.com/ai-news",
            published_at=datetime.now(timezone.utc),
            source="Tech News"
        )
        
        article2 = NewsArticle(
            title="Different Title",
            content="Different content",
            url="https://example.com/ai-news",  # Same URL
            published_at=datetime.now(timezone.utc),
            source="Other Source"
        )
        
        assert article1.is_duplicate(article2)
        assert article2.is_duplicate(article1)
    
    def test_duplicate_detection_similar_title(self):
        """Test duplicate detection for similar titles."""
        article1 = NewsArticle(
            title="OpenAI Releases New ChatGPT Model",
            content="Content about the release",
            url="https://example.com/news1",
            published_at=datetime.now(timezone.utc),
            source="Tech News"
        )
        
        article2 = NewsArticle(
            title="OpenAI Releases New ChatGPT Model Today",
            content="Different content about the same release",
            url="https://example.com/news2",
            published_at=datetime.now(timezone.utc),
            source="AI Weekly"
        )
        
        assert article1.is_duplicate(article2)
    
    def test_not_duplicate_different_content(self):
        """Test that different articles are not marked as duplicates."""
        article1 = NewsArticle(
            title="AI Breakthrough in Healthcare",
            content="Medical AI applications",
            url="https://example.com/healthcare-ai",
            published_at=datetime.now(timezone.utc),
            source="Medical News"
        )
        
        article2 = NewsArticle(
            title="New Smartphone Release",
            content="Latest mobile technology",
            url="https://example.com/smartphone",
            published_at=datetime.now(timezone.utc),
            source="Tech Review"
        )
        
        assert not article1.is_duplicate(article2)
        assert not article2.is_duplicate(article1)
    
    def test_custom_keywords_relevance(self):
        """Test relevance calculation with custom keywords."""
        article = NewsArticle(
            title="Quantum Computing Breakthrough",
            content="Scientists achieve quantum supremacy with new algorithms.",
            url="https://example.com/quantum",
            published_at=datetime.now(timezone.utc),
            source="Science Daily"
        )
        
        # Should have low relevance with default AI keywords
        default_score = article.calculate_relevance_score()
        
        # Should have high relevance with quantum keywords
        quantum_keywords = ["quantum", "computing", "algorithms", "supremacy"]
        quantum_score = article.calculate_relevance_score(quantum_keywords)
        
        assert quantum_score > default_score
        assert quantum_score > 0.5
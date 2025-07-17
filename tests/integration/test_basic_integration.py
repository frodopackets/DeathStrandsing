"""Basic integration tests for AI News Agent components."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from src.models import NewsArticle, NewsSummary, ArticleSource, AgentConfig


class TestBasicIntegration:
    """Basic integration tests to verify component interaction."""
    
    @pytest.mark.asyncio
    async def test_news_article_creation_and_validation(self):
        """Test NewsArticle creation and validation integration."""
        # Test valid article creation
        article = NewsArticle(
            title="Test AI Article",
            content="This is a test article about artificial intelligence.",
            url="https://example.com/test-article",
            published_at=datetime.now(timezone.utc),
            source="Test Source"
        )
        
        assert article.title == "Test AI Article"
        assert article.id is not None
        assert article.relevance_score is None
        
        # Test relevance calculation
        score = article.calculate_relevance_score()
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert article.relevance_score == score
        
        # Test relevance check
        is_relevant = article.is_relevant(threshold=0.1)
        assert isinstance(is_relevant, bool)
    
    @pytest.mark.asyncio
    async def test_news_summary_creation_and_formatting(self):
        """Test NewsSummary creation and formatting integration."""
        # Create sample sources
        sources = [
            ArticleSource(
                title="AI Article 1",
                url="https://example.com/article1",
                source="Source 1",
                published_at=datetime.now(timezone.utc)
            ),
            ArticleSource(
                title="AI Article 2", 
                url="https://example.com/article2",
                source="Source 2",
                published_at=datetime.now(timezone.utc)
            )
        ]
        
        # Create summary
        summary = NewsSummary(
            summary="Test summary of AI developments",
            key_points=["Point 1", "Point 2"],
            sources=sources,
            generated_at=datetime.now(timezone.utc),
            article_count=2
        )
        
        assert summary.id is not None
        assert len(summary.sources) == 2
        assert summary.article_count == 2
        
        # Test formatting
        email_format = summary.format_for_email()
        plain_format = summary.format_for_plain_text()
        
        assert "AI News Summary" in email_format
        assert "AI News Summary" in plain_format
        assert "Test summary of AI developments" in email_format
        assert "Test summary of AI developments" in plain_format
        
        # Test source methods
        unique_sources = summary.get_unique_sources()
        assert len(unique_sources) == 2
        assert "Source 1" in unique_sources
        assert "Source 2" in unique_sources
    
    @pytest.mark.asyncio
    async def test_agent_config_integration(self):
        """Test AgentConfig integration with environment variables."""
        # Test config creation with valid parameters
        config = AgentConfig(
            search_query="Test AI Query",
            time_range_hours=48,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=25,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        
        assert config.search_query == "Test AI Query"
        assert config.time_range_hours == 48
        assert config.max_articles == 25
        assert config.summary_length == "short"
        
        # Test config to dict conversion
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict['search_query'] == "Test AI Query"
        assert config_dict['time_range_hours'] == 48
    
    @pytest.mark.asyncio
    async def test_component_interaction_flow(self):
        """Test basic interaction flow between components."""
        # Create test articles
        articles = [
            NewsArticle(
                title="AI Development News",
                content="Latest developments in artificial intelligence and machine learning.",
                url="https://example.com/ai-dev",
                published_at=datetime.now(timezone.utc),
                source="AI News"
            ),
            NewsArticle(
                title="Machine Learning Breakthrough",
                content="New breakthrough in machine learning algorithms.",
                url="https://example.com/ml-breakthrough",
                published_at=datetime.now(timezone.utc),
                source="ML Weekly"
            )
        ]
        
        # Calculate relevance scores
        for article in articles:
            article.calculate_relevance_score()
        
        # Filter relevant articles
        relevant_articles = [article for article in articles if article.is_relevant(threshold=0.1)]
        
        # Create summary from articles
        sources = [
            ArticleSource(
                title=article.title,
                url=article.url,
                source=article.source,
                published_at=article.published_at
            ) for article in relevant_articles
        ]
        
        summary = NewsSummary(
            summary="Integration test summary of AI and ML developments",
            key_points=[
                "AI development continues to advance",
                "Machine learning shows breakthrough results"
            ],
            sources=sources,
            generated_at=datetime.now(timezone.utc),
            article_count=len(relevant_articles)
        )
        
        # Verify the flow worked correctly
        assert len(relevant_articles) <= len(articles)
        assert summary.article_count == len(relevant_articles)
        assert len(summary.sources) == len(relevant_articles)
        
        # Test summary formatting
        formatted_summary = summary.format_for_plain_text()
        assert "Integration test summary" in formatted_summary
        assert "AI development continues" in formatted_summary


if __name__ == "__main__":
    # Run basic integration tests
    pytest.main([__file__, "-v"])
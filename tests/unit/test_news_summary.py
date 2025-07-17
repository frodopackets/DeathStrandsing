"""Unit tests for NewsSummary model."""

import pytest
from datetime import datetime, timezone
from src.models.news_summary import NewsSummary, ArticleSource


class TestArticleSource:
    """Test cases for ArticleSource dataclass."""
    
    def test_article_source_creation(self):
        """Test creating an ArticleSource instance."""
        published_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        source = ArticleSource(
            title="Test Article",
            url="https://example.com/article",
            source="Example News",
            published_at=published_at
        )
        
        assert source.title == "Test Article"
        assert source.url == "https://example.com/article"
        assert source.source == "Example News"
        assert source.published_at == published_at


class TestNewsSummary:
    """Test cases for NewsSummary dataclass."""
    
    @pytest.fixture
    def sample_sources(self):
        """Create sample ArticleSource instances for testing."""
        return [
            ArticleSource(
                title="AI Breakthrough in 2024",
                url="https://example.com/ai-breakthrough",
                source="Tech News",
                published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            ),
            ArticleSource(
                title="Machine Learning Advances",
                url="https://example.com/ml-advances",
                source="AI Weekly",
                published_at=datetime(2024, 1, 14, 15, 45, 0, tzinfo=timezone.utc)
            ),
            ArticleSource(
                title="Generative AI in Business",
                url="https://example.com/gen-ai-business",
                source="Business Tech",
                published_at=datetime(2024, 1, 16, 8, 20, 0, tzinfo=timezone.utc)
            )
        ]
    
    @pytest.fixture
    def sample_summary(self, sample_sources):
        """Create a sample NewsSummary instance for testing."""
        return NewsSummary(
            summary="Recent developments in AI show significant progress in generative models and business applications.",
            key_points=[
                "New AI models demonstrate improved reasoning capabilities",
                "Business adoption of generative AI continues to grow",
                "Regulatory frameworks are being developed for AI governance"
            ],
            sources=sample_sources,
            generated_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=timezone.utc),
            article_count=3
        )
    
    def test_news_summary_creation(self, sample_summary):
        """Test creating a NewsSummary instance."""
        assert sample_summary.summary.startswith("Recent developments")
        assert len(sample_summary.key_points) == 3
        assert len(sample_summary.sources) == 3
        assert sample_summary.article_count == 3
        assert sample_summary.id is not None
    
    def test_news_summary_auto_id_generation(self, sample_sources):
        """Test that ID is automatically generated when not provided."""
        summary1 = NewsSummary(
            summary="Test summary",
            key_points=["Point 1"],
            sources=sample_sources,
            generated_at=datetime.now(timezone.utc),
            article_count=1
        )
        
        summary2 = NewsSummary(
            summary="Test summary",
            key_points=["Point 1"],
            sources=sample_sources,
            generated_at=datetime.now(timezone.utc),
            article_count=1
        )
        
        assert summary1.id is not None
        assert summary2.id is not None
        assert summary1.id != summary2.id
    
    def test_news_summary_custom_id(self, sample_sources):
        """Test creating NewsSummary with custom ID."""
        custom_id = "custom-summary-id"
        summary = NewsSummary(
            summary="Test summary",
            key_points=["Point 1"],
            sources=sample_sources,
            generated_at=datetime.now(timezone.utc),
            article_count=1,
            id=custom_id
        )
        
        assert summary.id == custom_id
    
    def test_format_for_email(self, sample_summary):
        """Test email formatting with markdown."""
        formatted = sample_summary.format_for_email()
        
        # Check header
        assert "# AI News Summary - January 16, 2024" in formatted
        assert "**Generated at:** 2024-01-16 12:00:00 UTC" in formatted
        assert "**Articles analyzed:** 3" in formatted
        
        # Check summary section
        assert "## Summary" in formatted
        assert "Recent developments in AI" in formatted
        
        # Check key points section
        assert "## Key Points" in formatted
        assert "1. New AI models demonstrate" in formatted
        assert "2. Business adoption of generative AI" in formatted
        assert "3. Regulatory frameworks are being" in formatted
        
        # Check sources section
        assert "## Sources" in formatted
        assert "**AI Breakthrough in 2024** - Tech News (2024-01-15)" in formatted
        assert "https://example.com/ai-breakthrough" in formatted
    
    def test_format_for_plain_text(self, sample_summary):
        """Test plain text formatting without markdown."""
        formatted = sample_summary.format_for_plain_text()
        
        # Check header
        assert "AI News Summary - January 16, 2024" in formatted
        assert "Generated at: 2024-01-16 12:00:00 UTC" in formatted
        assert "Articles analyzed: 3" in formatted
        
        # Check sections
        assert "SUMMARY" in formatted
        assert "KEY POINTS" in formatted
        assert "SOURCES" in formatted
        
        # Check no markdown formatting
        assert "**" not in formatted
        assert "##" not in formatted
        
        # Check content
        assert "Recent developments in AI" in formatted
        assert "1. New AI models demonstrate" in formatted
        assert "AI Breakthrough in 2024 - Tech News (2024-01-15)" in formatted
    
    def test_get_sources_by_date(self, sample_summary):
        """Test sorting sources by publication date."""
        sorted_sources = sample_summary.get_sources_by_date()
        
        # Should be sorted newest first
        assert len(sorted_sources) == 3
        assert sorted_sources[0].title == "Generative AI in Business"  # 2024-01-16
        assert sorted_sources[1].title == "AI Breakthrough in 2024"    # 2024-01-15
        assert sorted_sources[2].title == "Machine Learning Advances"  # 2024-01-14
    
    def test_get_unique_sources(self, sample_summary):
        """Test getting unique source names."""
        unique_sources = sample_summary.get_unique_sources()
        
        assert len(unique_sources) == 3
        assert "Tech News" in unique_sources
        assert "AI Weekly" in unique_sources
        assert "Business Tech" in unique_sources
    
    def test_get_unique_sources_with_duplicates(self):
        """Test getting unique source names when there are duplicates."""
        sources = [
            ArticleSource(
                title="Article 1",
                url="https://example.com/1",
                source="Tech News",
                published_at=datetime.now(timezone.utc)
            ),
            ArticleSource(
                title="Article 2",
                url="https://example.com/2",
                source="Tech News",
                published_at=datetime.now(timezone.utc)
            ),
            ArticleSource(
                title="Article 3",
                url="https://example.com/3",
                source="AI Weekly",
                published_at=datetime.now(timezone.utc)
            )
        ]
        
        summary = NewsSummary(
            summary="Test summary",
            key_points=["Point 1"],
            sources=sources,
            generated_at=datetime.now(timezone.utc),
            article_count=3
        )
        
        unique_sources = summary.get_unique_sources()
        assert len(unique_sources) == 2
        assert "Tech News" in unique_sources
        assert "AI Weekly" in unique_sources
    
    def test_empty_key_points_formatting(self, sample_sources):
        """Test formatting when there are no key points."""
        summary = NewsSummary(
            summary="Test summary without key points",
            key_points=[],
            sources=sample_sources,
            generated_at=datetime.now(timezone.utc),
            article_count=1
        )
        
        email_format = summary.format_for_email()
        plain_format = summary.format_for_plain_text()
        
        # Key points section should not appear when empty
        assert "## Key Points" not in email_format
        assert "KEY POINTS" not in plain_format
    
    def test_empty_sources_formatting(self):
        """Test formatting when there are no sources."""
        summary = NewsSummary(
            summary="Test summary without sources",
            key_points=["Point 1"],
            sources=[],
            generated_at=datetime.now(timezone.utc),
            article_count=0
        )
        
        email_format = summary.format_for_email()
        plain_format = summary.format_for_plain_text()
        
        # Sources section should not appear when empty
        assert "## Sources" not in email_format
        assert "SOURCES" not in plain_format
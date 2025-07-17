"""Unit tests for StrandsAISummarizer class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import List

from src.models import NewsArticle, NewsSummary, AgentConfig
from src.services.strands_ai_summarizer import StrandsAISummarizer


@pytest.fixture
def sample_config():
    """Create a sample AgentConfig for testing."""
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
def sample_articles():
    """Create sample NewsArticle objects for testing."""
    return [
        NewsArticle(
            title="OpenAI Releases GPT-5 with Enhanced Capabilities",
            content="OpenAI has announced the release of GPT-5, featuring improved reasoning and multimodal capabilities...",
            url="https://example.com/gpt5-release",
            published_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            source="TechCrunch",
            relevance_score=0.9
        ),
        NewsArticle(
            title="Google Announces Gemini 2.0 AI Model",
            content="Google has unveiled Gemini 2.0, a new large language model that promises better performance...",
            url="https://example.com/gemini-2",
            published_at=datetime(2024, 1, 14, 15, 30, 0, tzinfo=timezone.utc),
            source="The Verge",
            relevance_score=0.8
        )
    ]


@pytest.fixture
def mock_strands_agent():
    """Create a mock Strands agent."""
    agent = Mock()
    agent.generate = AsyncMock()
    return agent


class TestStrandsAISummarizer:
    """Test cases for StrandsAISummarizer class."""
    
    @patch('src.services.strands_ai_summarizer.Agent')
    def test_initialization_success(self, mock_agent_class, sample_config):
        """Test successful initialization of StrandsAISummarizer."""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance
        
        summarizer = StrandsAISummarizer(sample_config)
        
        assert summarizer.config == sample_config
        assert summarizer.agent == mock_agent_instance
        mock_agent_class.assert_called_once()
    
    @patch('src.services.strands_ai_summarizer.Agent')
    def test_initialization_failure(self, mock_agent_class, sample_config):
        """Test initialization failure handling."""
        mock_agent_class.side_effect = Exception("Agent initialization failed")
        
        with pytest.raises(Exception, match="Agent initialization failed"):
            StrandsAISummarizer(sample_config)
    
    def test_get_max_tokens_for_length(self, sample_config):
        """Test max tokens calculation for different summary lengths."""
        with patch('src.services.strands_ai_summarizer.Agent'):
            summarizer = StrandsAISummarizer(sample_config)
            
            # Test different length settings
            assert summarizer._get_max_tokens_for_length() == 600  # medium (default)
            
            sample_config.summary_length = "short"
            summarizer.config = sample_config
            assert summarizer._get_max_tokens_for_length() == 300
            
            sample_config.summary_length = "long"
            summarizer.config = sample_config
            assert summarizer._get_max_tokens_for_length() == 1000
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, mock_agent_class, sample_config, sample_articles):
        """Test successful summary generation."""
        # Setup mock agent
        mock_agent_instance = Mock()
        mock_response = Mock()
        mock_response.content = "This is a comprehensive summary of recent AI developments..."
        mock_agent_instance.invoke_async = AsyncMock(return_value=mock_response)
        mock_agent_class.return_value = mock_agent_instance
        
        summarizer = StrandsAISummarizer(sample_config)
        
        # Mock key points extraction
        with patch.object(summarizer, 'extract_key_points', return_value=["Key point 1", "Key point 2"]):
            result = await summarizer.generate_summary(sample_articles)
        
        assert isinstance(result, NewsSummary)
        assert result.summary == "This is a comprehensive summary of recent AI developments..."
        assert len(result.key_points) == 2
        assert result.article_count == 2
        assert len(result.sources) == 2
        assert isinstance(result.generated_at, datetime)
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_generate_summary_empty_articles(self, mock_agent_class, sample_config):
        """Test summary generation with empty article list."""
        mock_agent_class.return_value = Mock()
        summarizer = StrandsAISummarizer(sample_config)
        
        with pytest.raises(ValueError, match="Cannot generate summary from empty article list"):
            await summarizer.generate_summary([])
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_generate_summary_with_fallback(self, mock_agent_class, sample_config, sample_articles):
        """Test summary generation with fallback when Strands fails."""
        # Setup mock agent that fails
        mock_agent_instance = Mock()
        mock_agent_instance.invoke_async = AsyncMock(side_effect=Exception("API Error"))
        mock_agent_class.return_value = mock_agent_instance
        
        summarizer = StrandsAISummarizer(sample_config)
        
        result = await summarizer.generate_summary(sample_articles)
        
        assert isinstance(result, NewsSummary)
        assert "Recent Generative AI developments include:" in result.summary
        assert result.article_count == 2
        assert len(result.sources) == 2
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_extract_key_points_success(self, mock_agent_class, sample_config, sample_articles):
        """Test successful key points extraction."""
        # Setup mock agent
        mock_agent_instance = Mock()
        mock_response = Mock()
        mock_response.content = """• OpenAI releases GPT-5 with enhanced reasoning (Article 1)
• Google announces Gemini 2.0 improvements (Article 2)
• New AI safety measures implemented"""
        mock_agent_instance.invoke_async = AsyncMock(return_value=mock_response)
        mock_agent_class.return_value = mock_agent_instance
        
        summarizer = StrandsAISummarizer(sample_config)
        
        result = await summarizer.extract_key_points(sample_articles)
        
        assert len(result) == 3
        assert "OpenAI releases GPT-5 with enhanced reasoning (Article 1)" in result
        assert "Google announces Gemini 2.0 improvements (Article 2)" in result
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_extract_key_points_empty_articles(self, mock_agent_class, sample_config):
        """Test key points extraction with empty article list."""
        mock_agent_class.return_value = Mock()
        summarizer = StrandsAISummarizer(sample_config)
        
        result = await summarizer.extract_key_points([])
        
        assert result == []
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_extract_key_points_with_fallback(self, mock_agent_class, sample_config, sample_articles):
        """Test key points extraction with fallback when Strands fails."""
        # Setup mock agent that fails
        mock_agent_instance = Mock()
        mock_agent_instance.invoke_async = AsyncMock(side_effect=Exception("API Error"))
        mock_agent_class.return_value = mock_agent_instance
        
        summarizer = StrandsAISummarizer(sample_config)
        
        result = await summarizer.extract_key_points(sample_articles)
        
        assert len(result) == 2
        assert "OpenAI Releases GPT-5 with Enhanced Capabilities - TechCrunch" in result
        assert "Google Announces Gemini 2.0 AI Model - The Verge" in result
    
    def test_parse_key_points_response(self, sample_config):
        """Test parsing of key points from agent response."""
        with patch('src.services.strands_ai_summarizer.Agent'):
            summarizer = StrandsAISummarizer(sample_config)
            
            response_content = """• First key point here
• Second key point here
- Third key point with dash
* Fourth key point with asterisk
1. Fifth key point numbered
2. Sixth key point numbered"""
            
            result = summarizer._parse_key_points_response(response_content)
            
            assert len(result) == 6
            assert "First key point here" in result
            assert "Second key point here" in result
            assert "Third key point with dash" in result
            assert "Fourth key point with asterisk" in result
            assert "Fifth key point numbered" in result
            assert "Sixth key point numbered" in result
    
    def test_prepare_articles_for_summarization(self, sample_config, sample_articles):
        """Test preparation of articles for summarization."""
        with patch('src.services.strands_ai_summarizer.Agent'):
            summarizer = StrandsAISummarizer(sample_config)
            
            result = summarizer._prepare_articles_for_summarization(sample_articles)
            
            assert len(result) == 2
            assert "Title: OpenAI Releases GPT-5 with Enhanced Capabilities" in result[0]
            assert "Source: TechCrunch" in result[0]
            assert "Title: Google Announces Gemini 2.0 AI Model" in result[1]
            assert "Source: The Verge" in result[1]
    
    def test_create_article_sources(self, sample_config, sample_articles):
        """Test creation of ArticleSource objects."""
        with patch('src.services.strands_ai_summarizer.Agent'):
            summarizer = StrandsAISummarizer(sample_config)
            
            result = summarizer._create_article_sources(sample_articles)
            
            assert len(result) == 2
            assert result[0].title == "OpenAI Releases GPT-5 with Enhanced Capabilities"
            assert result[0].source == "TechCrunch"
            assert result[1].title == "Google Announces Gemini 2.0 AI Model"
            assert result[1].source == "The Verge"
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, mock_agent_class, sample_config):
        """Test successful execution with retry logic."""
        mock_agent_class.return_value = Mock()
        summarizer = StrandsAISummarizer(sample_config)
        
        mock_func = AsyncMock(return_value="success")
        
        result = await summarizer._execute_with_retry(mock_func, test_param="value")
        
        assert result == "success"
        mock_func.assert_called_once_with(test_param="value")
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_execute_with_retry_rate_limit(self, mock_agent_class, sample_config):
        """Test retry logic with rate limit errors."""
        mock_agent_class.return_value = Mock()
        summarizer = StrandsAISummarizer(sample_config)
        
        mock_func = AsyncMock()
        mock_func.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Rate limit exceeded"),
            "success"
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await summarizer._execute_with_retry(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @patch('src.services.strands_ai_summarizer.Agent')
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, mock_agent_class, sample_config):
        """Test retry logic when max retries are exceeded."""
        mock_agent_class.return_value = Mock()
        summarizer = StrandsAISummarizer(sample_config)
        
        mock_func = AsyncMock(side_effect=Exception("Rate limit exceeded"))
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(Exception, match="Failed after 3 attempts"):
                await summarizer._execute_with_retry(mock_func, max_retries=3)
    
    def test_create_summarization_prompt(self, sample_config):
        """Test creation of summarization prompt."""
        with patch('src.services.strands_ai_summarizer.Agent'):
            summarizer = StrandsAISummarizer(sample_config)
            
            article_texts = ["Article 1 content", "Article 2 content"]
            
            result = summarizer._create_summarization_prompt(article_texts)
            
            assert "AI news analyst" in result
            assert "Generative AI developments" in result
            assert "Article 1 content" in result
            assert "Article 2 content" in result
            assert "comprehensive summary (4-5 paragraphs)" in result  # medium length
    
    def test_create_key_points_prompt(self, sample_config, sample_articles):
        """Test creation of key points extraction prompt."""
        with patch('src.services.strands_ai_summarizer.Agent'):
            summarizer = StrandsAISummarizer(sample_config)
            
            article_texts = summarizer._prepare_articles_for_summarization(sample_articles)
            
            result = summarizer._create_key_points_prompt(article_texts, sample_articles)
            
            assert "AI news analyst" in result
            assert "key points" in result
            assert "Article 1 (TechCrunch)" in result
            assert "Article 2 (The Verge)" in result
            assert "5-8 key points maximum" in result
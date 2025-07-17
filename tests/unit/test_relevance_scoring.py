"""Unit tests for relevance scoring functionality."""

import pytest
from datetime import datetime
from src.models.news_article import NewsArticle


class TestRelevanceScoring:
    """Test cases for article relevance scoring."""
    
    def test_high_relevance_generative_ai_article(self):
        """Test that articles about generative AI get high relevance scores."""
        article = NewsArticle(
            title="OpenAI Releases New Generative AI Model GPT-5",
            content="OpenAI has announced the release of GPT-5, a new generative AI model that represents a significant advancement in large language model technology. The new model shows improved performance in natural language processing tasks and demonstrates enhanced capabilities in artificial intelligence applications.",
            url="https://example.com/gpt5-release",
            published_at=datetime.now(),
            source="AI News"
        )
        
        score = article.calculate_relevance_score()
        
        # Should get high score due to multiple AI-related keywords
        assert score > 0.3
        assert article.is_relevant(threshold=0.1)
        assert article.relevance_score == score
    
    def test_medium_relevance_ai_article(self):
        """Test that articles with some AI content get medium relevance scores."""
        article = NewsArticle(
            title="Tech Company Adopts Machine Learning for Business Operations",
            content="A major technology company has announced the adoption of machine learning algorithms to improve their business operations. The implementation focuses on data analysis and process optimization using artificial intelligence techniques.",
            url="https://example.com/ml-adoption",
            published_at=datetime.now(),
            source="Tech Business"
        )
        
        score = article.calculate_relevance_score()
        
        # Should get medium score due to some AI keywords
        assert 0.1 <= score <= 0.4
        assert article.is_relevant(threshold=0.1)
    
    def test_low_relevance_non_ai_article(self):
        """Test that non-AI articles get low relevance scores."""
        article = NewsArticle(
            title="New Restaurant Opens Downtown",
            content="A new Italian restaurant has opened in the downtown area, featuring traditional recipes and modern dining experience. The restaurant offers a variety of pasta dishes and wine selections.",
            url="https://example.com/restaurant-news",
            published_at=datetime.now(),
            source="Local News"
        )
        
        score = article.calculate_relevance_score()
        
        # Should get very low or zero score
        assert score < 0.1
        assert not article.is_relevant(threshold=0.1)
    
    def test_title_boost_scoring(self):
        """Test that AI keywords in title get higher scores."""
        article_with_ai_title = NewsArticle(
            title="ChatGPT and Generative AI Transform Education",
            content="Educational institutions are exploring new teaching methods.",
            url="https://example.com/ai-education",
            published_at=datetime.now(),
            source="Education News"
        )
        
        article_without_ai_title = NewsArticle(
            title="Educational Institutions Explore New Teaching Methods",
            content="Schools are looking at ChatGPT and generative AI for educational purposes.",
            url="https://example.com/education-methods",
            published_at=datetime.now(),
            source="Education News"
        )
        
        score_with_title = article_with_ai_title.calculate_relevance_score()
        score_without_title = article_without_ai_title.calculate_relevance_score()
        
        # Article with AI keywords in title should score higher
        assert score_with_title > score_without_title
    
    def test_custom_keywords_scoring(self):
        """Test relevance scoring with custom keywords."""
        article = NewsArticle(
            title="Quantum Computing Breakthrough",
            content="Scientists achieve new milestone in quantum computing research with advanced algorithms and computational methods.",
            url="https://example.com/quantum-computing",
            published_at=datetime.now(),
            source="Science News"
        )
        
        # Test with default AI keywords (should be low)
        default_score = article.calculate_relevance_score()
        
        # Test with custom quantum-related keywords (should be higher)
        quantum_keywords = ['quantum', 'computing', 'algorithms', 'computational']
        custom_score = article.calculate_relevance_score(keywords=quantum_keywords)
        
        assert custom_score > default_score
        assert custom_score > 0.2
    
    def test_relevance_threshold_filtering(self):
        """Test relevance threshold filtering."""
        high_relevance_article = NewsArticle(
            title="OpenAI GPT-4 and Claude AI Models Compared",
            content="A comprehensive comparison of generative AI models including GPT-4, Claude, and other large language models shows significant differences in artificial intelligence capabilities.",
            url="https://example.com/ai-comparison",
            published_at=datetime.now(),
            source="AI Research"
        )
        
        low_relevance_article = NewsArticle(
            title="Weather Update for Tomorrow",
            content="Tomorrow's weather forecast shows sunny skies with mild temperatures.",
            url="https://example.com/weather",
            published_at=datetime.now(),
            source="Weather News"
        )
        
        high_relevance_article.calculate_relevance_score()
        low_relevance_article.calculate_relevance_score()
        
        # Test different thresholds
        assert high_relevance_article.is_relevant(threshold=0.1)
        assert high_relevance_article.is_relevant(threshold=0.2)
        
        assert not low_relevance_article.is_relevant(threshold=0.1)
        assert not low_relevance_article.is_relevant(threshold=0.05)
    
    def test_generative_ai_specific_keywords(self):
        """Test that generative AI specific keywords are properly weighted."""
        generative_ai_keywords = [
            'generative ai', 'chatgpt', 'gpt', 'llm', 'large language model',
            'openai', 'anthropic', 'claude', 'gemini', 'bard', 'copilot'
        ]
        
        for keyword in generative_ai_keywords:
            article = NewsArticle(
                title=f"News about {keyword}",
                content=f"This article discusses {keyword} and its impact on technology.",
                url=f"https://example.com/{keyword.replace(' ', '-')}",
                published_at=datetime.now(),
                source="Tech News"
            )
            
            score = article.calculate_relevance_score()
            
            # Each generative AI keyword should result in relevant content
            assert score > 0.05, f"Keyword '{keyword}' should result in relevant score"
            assert article.is_relevant(threshold=0.05)
    
    def test_case_insensitive_scoring(self):
        """Test that relevance scoring is case insensitive."""
        article_lowercase = NewsArticle(
            title="artificial intelligence and machine learning",
            content="generative ai and chatgpt are transforming industries",
            url="https://example.com/lowercase",
            published_at=datetime.now(),
            source="Tech News"
        )
        
        article_uppercase = NewsArticle(
            title="ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING",
            content="GENERATIVE AI AND CHATGPT ARE TRANSFORMING INDUSTRIES",
            url="https://example.com/uppercase",
            published_at=datetime.now(),
            source="Tech News"
        )
        
        article_mixed = NewsArticle(
            title="Artificial Intelligence and Machine Learning",
            content="Generative AI and ChatGPT are Transforming Industries",
            url="https://example.com/mixed",
            published_at=datetime.now(),
            source="Tech News"
        )
        
        score_lower = article_lowercase.calculate_relevance_score()
        score_upper = article_uppercase.calculate_relevance_score()
        score_mixed = article_mixed.calculate_relevance_score()
        
        # All should have similar scores (case insensitive)
        assert abs(score_lower - score_upper) < 0.01
        assert abs(score_lower - score_mixed) < 0.01
        assert abs(score_upper - score_mixed) < 0.01
    
    def test_score_capping_at_one(self):
        """Test that relevance scores are capped at 1.0."""
        # Create article with many AI keywords
        article = NewsArticle(
            title="Artificial Intelligence Machine Learning Generative AI ChatGPT GPT LLM",
            content="This article contains artificial intelligence, machine learning, generative ai, chatgpt, gpt, llm, large language model, neural network, deep learning, transformer, openai, anthropic, claude, gemini, bard, copilot and many other AI-related terms.",
            url="https://example.com/ai-heavy",
            published_at=datetime.now(),
            source="AI News"
        )
        
        score = article.calculate_relevance_score()
        
        # Score should be capped at 1.0
        assert score <= 1.0
        assert article.is_relevant(threshold=0.1)
    
    def test_empty_content_handling(self):
        """Test handling of articles with minimal content."""
        try:
            article = NewsArticle(
                title="AI",
                content="AI",
                url="https://example.com/minimal",
                published_at=datetime.now(),
                source="News"
            )
            
            score = article.calculate_relevance_score()
            
            # Should handle minimal content gracefully
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
            
        except ValueError:
            # If validation prevents minimal content, that's also acceptable
            pass
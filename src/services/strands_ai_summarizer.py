"""Strands SDK-based AI summarizer implementation for the AI News Agent."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio

from strands import Agent
from strands.models import BedrockModel

from ..models import NewsArticle, NewsSummary, ArticleSource, AgentConfig
from .ai_summarizer import AISummarizer


logger = logging.getLogger(__name__)


class StrandsAISummarizer(AISummarizer):
    """Strands SDK-based implementation of AI summarization."""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Strands AI Summarizer.
        
        Args:
            config: AgentConfig containing model and summarization settings
        """
        self.config = config
        self.agent: Optional[Agent] = None
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize the Strands agent with configuration."""
        try:
            # Create model based on provider
            model = self._create_model()
            
            # Create agent with model
            self.agent = Agent(
                model=model,
                system_prompt="You are an AI news analyst specializing in Generative AI developments."
            )
            logger.info(f"Initialized Strands agent with model: {self.config.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands agent: {e}")
            raise Exception(f"Agent initialization failed: {e}")
    
    def _create_model(self):
        """Create Strands model from agent config."""
        if self.config.model_provider == 'bedrock':
            return BedrockModel(
                model_id=self.config.model_name,
                region_name='us-east-1'  # Default region for Bedrock
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.config.model_provider}")
    
    def _get_max_tokens_for_length(self) -> int:
        """Get max tokens based on summary length setting."""
        length_mapping = {
            'short': 300,
            'medium': 600,
            'long': 1000
        }
        return length_mapping.get(self.config.summary_length, 600)
    
    async def generate_summary(self, articles: List[NewsArticle]) -> NewsSummary:
        """
        Generate a comprehensive summary from news articles using Strands SDK.
        
        Args:
            articles: List of NewsArticle objects to summarize
            
        Returns:
            NewsSummary object containing the generated summary
            
        Raises:
            StrandsError: If summarization fails
        """
        if not articles:
            raise ValueError("Cannot generate summary from empty article list")
        
        if not self.agent:
            raise Exception("Strands agent not initialized")
        
        try:
            logger.info(f"Generating summary for {len(articles)} articles")
            
            # Prepare articles for summarization
            article_texts = self._prepare_articles_for_summarization(articles)
            
            # Generate summary using Strands agent
            summary_text = await self._generate_summary_text(article_texts)
            
            # Extract key points
            key_points = await self.extract_key_points(articles)
            
            # Create article sources
            sources = self._create_article_sources(articles)
            
            # Create and return NewsSummary
            news_summary = NewsSummary(
                summary=summary_text,
                key_points=key_points,
                sources=sources,
                generated_at=datetime.now(timezone.utc),
                article_count=len(articles)
            )
            
            logger.info(f"Successfully generated summary with {len(key_points)} key points")
            return news_summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # Try fallback approach
            return await self._fallback_summary_generation(articles)
    
    async def _generate_summary_text(self, article_texts: List[str]) -> str:
        """Generate summary text using Strands agent."""
        try:
            # Create prompt for summarization
            prompt = self._create_summarization_prompt(article_texts)
            
            # Generate summary with retry logic
            response = await self._execute_with_retry(
                self.agent.invoke_async,
                prompt=prompt,
                max_retries=3
            )
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Summary text generation failed: {e}")
            raise Exception(f"Failed to generate summary text: {e}")
    
    def _create_summarization_prompt(self, article_texts: List[str]) -> str:
        """Create a prompt for summarizing news articles."""
        length_instructions = {
            'short': "Keep the summary concise (2-3 paragraphs).",
            'medium': "Provide a comprehensive summary (4-5 paragraphs).",
            'long': "Create a detailed summary (6-8 paragraphs)."
        }
        
        length_instruction = length_instructions.get(self.config.summary_length, 
                                                   length_instructions['medium'])
        
        combined_articles = "\n\n---\n\n".join(article_texts)
        
        prompt = f"""You are an AI news analyst specializing in Generative AI developments. 
Please analyze the following news articles and create a coherent summary focusing on the most important developments in Generative AI.

{length_instruction}

Focus on:
- Major announcements and product launches
- Technical breakthroughs and research developments
- Industry trends and market movements
- Regulatory and policy changes
- Notable partnerships and acquisitions

Articles to summarize:

{combined_articles}

Please provide a well-structured summary that synthesizes the key information from these articles into a coherent narrative about recent Generative AI developments."""
        
        return prompt
    
    async def extract_key_points(self, articles: List[NewsArticle]) -> List[str]:
        """
        Extract key points from articles using Strands agent.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            List of key points as strings
        """
        if not articles:
            return []
        
        if not self.agent:
            raise Exception("Strands agent not initialized")
        
        try:
            logger.info(f"Extracting key points from {len(articles)} articles")
            
            # Prepare articles for key point extraction
            article_texts = self._prepare_articles_for_summarization(articles)
            
            # Create prompt for key point extraction
            prompt = self._create_key_points_prompt(article_texts, articles)
            
            # Extract key points with retry logic
            response = await self._execute_with_retry(
                self.agent.invoke_async,
                prompt=prompt,
                max_retries=3
            )
            
            # Parse key points from response
            key_points = self._parse_key_points_response(response.content)
            
            logger.info(f"Successfully extracted {len(key_points)} key points")
            return key_points
            
        except Exception as e:
            logger.error(f"Key points extraction failed: {e}")
            # Return fallback key points
            return self._generate_fallback_key_points(articles)
    
    def _create_key_points_prompt(self, article_texts: List[str], articles: List[NewsArticle]) -> str:
        """Create a prompt for extracting key points with source attribution."""
        combined_articles = ""
        for i, (text, article) in enumerate(zip(article_texts, articles), 1):
            combined_articles += f"Article {i} ({article.source}):\n{text}\n\n---\n\n"
        
        prompt = f"""You are an AI news analyst. Please extract the most important key points from the following Generative AI news articles.

For each key point:
1. Make it concise but informative (1-2 sentences)
2. Focus on actionable insights or significant developments
3. Include the source article number in parentheses at the end

Extract 5-8 key points maximum. Format each point as a bullet point.

Articles:

{combined_articles}

Please provide the key points in this format:
• [Key point text] (Article X)
• [Key point text] (Article Y)
"""
        
        return prompt
    
    def _parse_key_points_response(self, response_content: str) -> List[str]:
        """Parse key points from the agent response."""
        lines = response_content.strip().split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                key_point = line[1:].strip()
                if key_point:
                    key_points.append(key_point)
            elif line and line[0].isdigit() and '.' in line:
                # Handle numbered lists like "1. Key point"
                key_point = line.split('.', 1)[1].strip()
                if key_point:
                    key_points.append(key_point)
        
        return key_points[:8]  # Limit to 8 key points maximum
    
    def _prepare_articles_for_summarization(self, articles: List[NewsArticle]) -> List[str]:
        """Prepare article texts for summarization."""
        article_texts = []
        
        for article in articles:
            # Create a formatted text for each article
            article_text = f"Title: {article.title}\n"
            article_text += f"Source: {article.source}\n"
            article_text += f"Published: {article.published_at.strftime('%Y-%m-%d')}\n"
            article_text += f"Content: {article.content[:2000]}..."  # Limit content length
            
            article_texts.append(article_text)
        
        return article_texts
    
    def _create_article_sources(self, articles: List[NewsArticle]) -> List[ArticleSource]:
        """Create ArticleSource objects from NewsArticle objects."""
        sources = []
        
        for article in articles:
            source = ArticleSource(
                title=article.title,
                url=article.url,
                source=article.source,
                published_at=article.published_at
            )
            sources.append(source)
        
        return sources
    
    async def _execute_with_retry(self, func, max_retries: int = 3, **kwargs) -> Any:
        """Execute a function with retry logic for handling transient errors."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func(**kwargs)
                
            except Exception as e:
                # Check if it's a rate limit or model error by message
                error_msg = str(e).lower()
                if 'rate limit' in error_msg or 'throttl' in error_msg:
                    logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                    last_exception = e
                elif 'model' in error_msg or 'bedrock' in error_msg:
                    logger.error(f"Model error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                    last_exception = e
                else:
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    last_exception = e
                    break
        
        raise Exception(f"Failed after {max_retries} attempts: {last_exception}")
    
    async def _fallback_summary_generation(self, articles: List[NewsArticle]) -> NewsSummary:
        """Generate a fallback summary when Strands SDK fails."""
        logger.warning("Using fallback summary generation")
        
        # Create a simple summary from article titles and basic content
        summary_parts = []
        key_points = []
        
        for i, article in enumerate(articles[:5], 1):  # Limit to first 5 articles
            summary_parts.append(f"{article.title} ({article.source})")
            key_points.append(f"{article.title[:100]}... ({article.source})")
        
        fallback_summary = "Recent Generative AI developments include: " + "; ".join(summary_parts)
        
        sources = self._create_article_sources(articles)
        
        return NewsSummary(
            summary=fallback_summary,
            key_points=key_points,
            sources=sources,
            generated_at=datetime.now(timezone.utc),
            article_count=len(articles)
        )
    
    def _generate_fallback_key_points(self, articles: List[NewsArticle]) -> List[str]:
        """Generate fallback key points when extraction fails."""
        key_points = []
        
        for article in articles[:5]:  # Limit to first 5 articles
            key_point = f"{article.title} - {article.source}"
            key_points.append(key_point)
        
        return key_points
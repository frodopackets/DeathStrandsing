"""Google News API client implementation for the AI News Agent."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Set
from asyncio_throttle import Throttler
import aiohttp
from gnews import GNews

from ..models import NewsArticle
from .news_fetcher import NewsFetcher


logger = logging.getLogger(__name__)


class GoogleNewsFetcher(NewsFetcher):
    """Google News API client with rate limiting and error handling."""
    
    def __init__(
        self,
        language: str = 'en',
        country: str = 'US',
        max_results: int = 50,
        requests_per_minute: int = 30
    ):
        """
        Initialize Google News fetcher.
        
        Args:
            language: Language code for news articles
            country: Country code for news articles
            max_results: Maximum number of articles to fetch
            requests_per_minute: Rate limit for API calls
        """
        self.language = language
        self.country = country
        self.max_results = max_results
        
        # Initialize GNews client
        self.gnews = GNews(
            language=language,
            country=country,
            max_results=max_results
        )
        
        # Rate limiting
        self.throttler = Throttler(rate_limit=requests_per_minute, period=60)
        
        # Track processed URLs to avoid duplicates
        self._processed_urls: Set[str] = set()
        
        logger.info(f"Initialized GoogleNewsFetcher with language={language}, country={country}")
    
    async def fetch_news(self, query: str, time_range_hours: int) -> List[NewsArticle]:
        """
        Fetch news articles from Google News.
        
        Args:
            query: Search query string
            time_range_hours: Number of hours to look back for articles
            
        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching news for query: '{query}' within {time_range_hours} hours")
        
        try:
            # Apply rate limiting
            async with self.throttler:
                # Set time period for GNews
                self._set_time_period(time_range_hours)
                
                # Fetch articles
                raw_articles = await self._fetch_with_retry(query)
                
                if not raw_articles:
                    logger.warning(f"No articles found for query: '{query}'")
                    return []
                
                # Convert to NewsArticle objects
                articles = await self._convert_to_news_articles(raw_articles, time_range_hours)
                
                logger.info(f"Successfully fetched {len(articles)} articles")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            raise
    
    async def filter_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Filter articles for relevance and remove duplicates.
        
        Args:
            articles: List of articles to filter
            
        Returns:
            Filtered list of articles
        """
        logger.info(f"Filtering {len(articles)} articles")
        
        if not articles:
            return []
        
        # Remove duplicates
        unique_articles = self._remove_duplicates(articles)
        logger.info(f"After duplicate removal: {len(unique_articles)} articles")
        
        # Calculate relevance scores
        relevant_articles = []
        for article in unique_articles:
            try:
                score = article.calculate_relevance_score()
                if article.is_relevant(threshold=0.1):
                    relevant_articles.append(article)
                    logger.debug(f"Article '{article.title[:50]}...' scored {score:.2f}")
                else:
                    logger.debug(f"Article '{article.title[:50]}...' filtered out (score: {score:.2f})")
            except Exception as e:
                logger.warning(f"Error calculating relevance for article: {str(e)}")
                continue
        
        # Sort by relevance score (highest first)
        relevant_articles.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        
        logger.info(f"After relevance filtering: {len(relevant_articles)} articles")
        return relevant_articles
    
    def _set_time_period(self, hours: int) -> None:
        """Set the time period for GNews based on hours."""
        if hours <= 24:
            self.gnews.period = '1d'
        elif hours <= 168:  # 7 days
            self.gnews.period = '7d'
        else:
            self.gnews.period = '30d'
    
    async def _fetch_with_retry(self, query: str, max_retries: int = 3) -> List[dict]:
        """
        Fetch articles with retry logic.
        
        Args:
            query: Search query
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of raw article dictionaries
        """
        for attempt in range(max_retries):
            try:
                # Run GNews search in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                articles = await loop.run_in_executor(
                    None, 
                    lambda: self.gnews.get_news(query)
                )
                
                if articles:
                    return articles
                    
                logger.warning(f"No articles returned for query '{query}' on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    async def _convert_to_news_articles(
        self, 
        raw_articles: List[dict], 
        time_range_hours: int
    ) -> List[NewsArticle]:
        """
        Convert raw article data to NewsArticle objects.
        
        Args:
            raw_articles: Raw article dictionaries from GNews
            time_range_hours: Time range for filtering
            
        Returns:
            List of NewsArticle objects
        """
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        
        for raw_article in raw_articles:
            try:
                # Extract article details
                article = await self._create_news_article(raw_article)
                
                if not article:
                    continue
                
                # Filter by time range
                if article.published_at <= cutoff_time:
                    logger.debug(f"Article '{article.title[:50]}...' is outside time range")
                    continue
                
                # Check for duplicates
                if article.url in self._processed_urls:
                    logger.debug(f"Duplicate URL found: {article.url}")
                    continue
                
                self._processed_urls.add(article.url)
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Error processing article: {str(e)}")
                continue
        
        return articles
    
    async def _create_news_article(self, raw_article: dict) -> Optional[NewsArticle]:
        """
        Create NewsArticle from raw article data.
        
        Args:
            raw_article: Raw article dictionary
            
        Returns:
            NewsArticle object or None if creation fails
        """
        try:
            # Extract basic information
            title = raw_article.get('title', '').strip()
            url = raw_article.get('url', '').strip()
            
            if not title or not url:
                logger.warning("Article missing title or URL")
                return None
            
            # Get full article content
            content = await self._get_article_content(raw_article)
            
            # Parse publication date
            published_at = self._parse_published_date(raw_article)
            
            # Extract source
            source = raw_article.get('publisher', {}).get('title', 'Unknown')
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                published_at=published_at,
                source=source
            )
            
        except Exception as e:
            logger.error(f"Error creating NewsArticle: {str(e)}")
            return None
    
    async def _get_article_content(self, raw_article: dict) -> str:
        """
        Get full article content.
        
        Args:
            raw_article: Raw article dictionary
            
        Returns:
            Article content string
        """
        # Try to get full article content
        try:
            loop = asyncio.get_event_loop()
            full_article = await loop.run_in_executor(
                None,
                lambda: self.gnews.get_full_article(raw_article.get('url', ''))
            )
            
            if full_article and hasattr(full_article, 'text'):
                return full_article.text.strip()
                
        except Exception as e:
            logger.debug(f"Could not fetch full article content: {str(e)}")
        
        # Fallback to description/summary
        return raw_article.get('description', '').strip() or "Content not available"
    
    def _parse_published_date(self, raw_article: dict) -> datetime:
        """
        Parse publication date from raw article.
        
        Args:
            raw_article: Raw article dictionary
            
        Returns:
            Parsed datetime object
        """
        try:
            # GNews typically provides published date as string
            published_str = raw_article.get('published date', '')
            
            if published_str:
                # Try to parse the date string
                from dateutil import parser
                return parser.parse(published_str)
                
        except Exception as e:
            logger.debug(f"Could not parse published date: {str(e)}")
        
        # Fallback to current time
        return datetime.now()
    
    def _remove_duplicates(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Remove duplicate articles from the list.
        
        Args:
            articles: List of articles to deduplicate
            
        Returns:
            List of unique articles
        """
        unique_articles = []
        seen_urls = set()
        
        for article in articles:
            # Check URL duplicates
            if article.url in seen_urls:
                continue
            
            # Check content similarity duplicates
            is_duplicate = False
            for existing_article in unique_articles:
                if article.is_duplicate(existing_article):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_urls.add(article.url)
        
        return unique_articles
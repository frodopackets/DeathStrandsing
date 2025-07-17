"""News fetcher interface for the AI News Agent."""

from abc import ABC, abstractmethod
from typing import List
from datetime import datetime

from ..models import NewsArticle


class NewsFetcher(ABC):
    """Abstract base class for news fetching implementations."""
    
    @abstractmethod
    async def fetch_news(self, query: str, time_range_hours: int) -> List[NewsArticle]:
        """
        Fetch news articles from a news source.
        
        Args:
            query: Search query string
            time_range_hours: Number of hours to look back for articles
            
        Returns:
            List of NewsArticle objects
        """
        pass
    
    @abstractmethod
    async def filter_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Filter articles for relevance and remove duplicates.
        
        Args:
            articles: List of articles to filter
            
        Returns:
            Filtered list of articles
        """
        pass
"""AI summarizer interface for the AI News Agent."""

from abc import ABC, abstractmethod
from typing import List

from ..models import NewsArticle, NewsSummary


class AISummarizer(ABC):
    """Abstract base class for AI summarization implementations."""
    
    @abstractmethod
    async def generate_summary(self, articles: List[NewsArticle]) -> NewsSummary:
        """
        Generate a summary from a list of news articles.
        
        Args:
            articles: List of NewsArticle objects to summarize
            
        Returns:
            NewsSummary object containing the generated summary
        """
        pass
    
    @abstractmethod
    async def extract_key_points(self, articles: List[NewsArticle]) -> List[str]:
        """
        Extract key points from articles.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            List of key points as strings
        """
        pass
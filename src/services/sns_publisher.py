"""SNS publisher interface for the AI News Agent."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import NewsSummary


class SNSPublisher(ABC):
    """Abstract base class for SNS publishing implementations."""
    
    @abstractmethod
    async def publish_summary(self, summary: NewsSummary) -> bool:
        """
        Publish a news summary to SNS topic.
        
        Args:
            summary: NewsSummary object to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def format_message(self, summary: NewsSummary) -> str:
        """
        Format a summary for email delivery.
        
        Args:
            summary: NewsSummary object to format
            
        Returns:
            Formatted message string
        """
        pass
    
    @abstractmethod
    async def send_no_news_notification(self) -> bool:
        """
        Send notification when no relevant news is found.
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
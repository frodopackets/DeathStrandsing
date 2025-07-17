"""NewsSummary data model for the AI News Agent."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class ArticleSource:
    """Represents a source article used in the summary."""
    
    title: str
    url: str
    source: str
    published_at: datetime


@dataclass
class NewsSummary:
    """Represents an AI-generated summary of news articles."""
    
    summary: str
    key_points: List[str]
    sources: List[ArticleSource]
    generated_at: datetime
    article_count: int
    id: Optional[str] = None
    
    def __post_init__(self):
        """Generate unique ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def format_for_email(self) -> str:
        """Format the summary for email delivery with sources and dates."""
        formatted_summary = f"# AI News Summary - {self.generated_at.strftime('%B %d, %Y')}\n\n"
        formatted_summary += f"**Generated at:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        formatted_summary += f"**Articles analyzed:** {self.article_count}\n\n"
        
        formatted_summary += "## Summary\n\n"
        formatted_summary += f"{self.summary}\n\n"
        
        if self.key_points:
            formatted_summary += "## Key Points\n\n"
            for i, point in enumerate(self.key_points, 1):
                formatted_summary += f"{i}. {point}\n"
            formatted_summary += "\n"
        
        if self.sources:
            formatted_summary += "## Sources\n\n"
            for i, source in enumerate(self.sources, 1):
                formatted_date = source.published_at.strftime('%Y-%m-%d')
                formatted_summary += f"{i}. **{source.title}** - {source.source} ({formatted_date})\n"
                formatted_summary += f"   {source.url}\n\n"
        
        return formatted_summary
    
    def format_for_plain_text(self) -> str:
        """Format the summary as plain text without markdown."""
        formatted_summary = f"AI News Summary - {self.generated_at.strftime('%B %d, %Y')}\n"
        formatted_summary += "=" * 50 + "\n\n"
        formatted_summary += f"Generated at: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        formatted_summary += f"Articles analyzed: {self.article_count}\n\n"
        
        formatted_summary += "SUMMARY\n"
        formatted_summary += "-" * 20 + "\n"
        formatted_summary += f"{self.summary}\n\n"
        
        if self.key_points:
            formatted_summary += "KEY POINTS\n"
            formatted_summary += "-" * 20 + "\n"
            for i, point in enumerate(self.key_points, 1):
                formatted_summary += f"{i}. {point}\n"
            formatted_summary += "\n"
        
        if self.sources:
            formatted_summary += "SOURCES\n"
            formatted_summary += "-" * 20 + "\n"
            for i, source in enumerate(self.sources, 1):
                formatted_date = source.published_at.strftime('%Y-%m-%d')
                formatted_summary += f"{i}. {source.title} - {source.source} ({formatted_date})\n"
                formatted_summary += f"   {source.url}\n\n"
        
        return formatted_summary
    
    def get_sources_by_date(self) -> List[ArticleSource]:
        """Return sources sorted by publication date (newest first)."""
        return sorted(self.sources, key=lambda x: x.published_at, reverse=True)
    
    def get_unique_sources(self) -> List[str]:
        """Return list of unique source names."""
        return list(set(source.source for source in self.sources))
"""NewsArticle data model for the AI News Agent."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid
import re
from urllib.parse import urlparse


@dataclass
class NewsArticle:
    """Represents a news article retrieved from Google News API."""
    
    title: str
    content: str
    url: str
    published_at: datetime
    source: str
    id: Optional[str] = None
    relevance_score: Optional[float] = None
    
    def __post_init__(self):
        """Generate unique ID if not provided and validate data."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        self.validate()
    
    def validate(self) -> None:
        """Validate article data integrity."""
        if not self.title or not self.title.strip():
            raise ValueError("Article title cannot be empty")
        
        if not self.content or not self.content.strip():
            raise ValueError("Article content cannot be empty")
        
        if not self.url or not self.url.strip():
            raise ValueError("Article URL cannot be empty")
        
        if not self._is_valid_url(self.url):
            raise ValueError(f"Invalid URL format: {self.url}")
        
        if not self.source or not self.source.strip():
            raise ValueError("Article source cannot be empty")
        
        if not isinstance(self.published_at, datetime):
            raise ValueError("Published date must be a datetime object")
        
        if self.relevance_score is not None:
            if not isinstance(self.relevance_score, (int, float)):
                raise ValueError("Relevance score must be a number")
            if not 0.0 <= self.relevance_score <= 1.0:
                raise ValueError("Relevance score must be between 0.0 and 1.0")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has valid format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def calculate_relevance_score(self, keywords: list[str] = None) -> float:
        """Calculate relevance score based on AI-related keywords."""
        if keywords is None:
            keywords = [
                'artificial intelligence', 'ai', 'machine learning', 'ml',
                'generative ai', 'chatgpt', 'gpt', 'llm', 'large language model',
                'neural network', 'deep learning', 'transformer', 'openai',
                'anthropic', 'claude', 'gemini', 'bard', 'copilot'
            ]
        
        # Combine title and content for scoring
        text = f"{self.title} {self.content}".lower()
        
        # Count keyword matches
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword.lower() in text:
                matches += 1
        
        # Calculate base score from keyword density
        base_score = matches / total_keywords if total_keywords > 0 else 0.0
        
        # Boost score for title matches (more important)
        title_matches = sum(1 for keyword in keywords if keyword.lower() in self.title.lower())
        title_boost = (title_matches / total_keywords) * 0.3 if total_keywords > 0 else 0.0
        
        # Calculate final score (capped at 1.0)
        final_score = min(base_score + title_boost, 1.0)
        
        # Update the relevance score
        self.relevance_score = final_score
        
        return final_score
    
    def is_relevant(self, threshold: float = 0.1) -> bool:
        """Check if article is relevant based on threshold."""
        if self.relevance_score is None:
            self.calculate_relevance_score()
        return self.relevance_score >= threshold
    
    def is_duplicate(self, other: 'NewsArticle') -> bool:
        """Check if this article is a duplicate of another."""
        if not isinstance(other, NewsArticle):
            return False
        
        # Check URL match (exact duplicate)
        if self.url == other.url:
            return True
        
        # Check title similarity (fuzzy duplicate)
        title_similarity = self._calculate_similarity(self.title, other.title)
        if title_similarity > 0.8:
            return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        # Simple word-based similarity
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
"""AgentConfig data model for the AI News Agent."""

from typing import Literal, Optional
import os
from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict


class AgentConfig(BaseModel):
    """Configuration settings for the AI News Agent with validation."""
    
    search_query: str = Field(
        min_length=1,
        max_length=200,
        description="Search query for news articles"
    )
    time_range_hours: int = Field(
        ge=1,
        le=168,  # Max 1 week
        description="Time range in hours for news search"
    )
    sns_topic_arn: str = Field(
        min_length=1,
        description="AWS SNS topic ARN for notifications"
    )
    max_articles: int = Field(
        ge=1,
        le=100,
        description="Maximum number of articles to process"
    )
    summary_length: Literal['short', 'medium', 'long'] = Field(
        description="Length of the generated summary"
    )
    model_name: str = Field(
        min_length=1,
        description="AI model name for summarization"
    )
    model_provider: str = Field(
        min_length=1,
        description="AI model provider (e.g., bedrock, openai)"
    )
    
    @field_validator('sns_topic_arn')
    @classmethod
    def validate_sns_topic_arn(cls, v):
        """Validate SNS topic ARN format."""
        if not v.startswith('arn:aws:sns:'):
            raise ValueError('SNS topic ARN must start with "arn:aws:sns:"')
        return v
    
    @field_validator('model_provider')
    @classmethod
    def validate_model_provider(cls, v):
        """Validate model provider is supported."""
        supported_providers = ['bedrock', 'openai', 'anthropic']
        if v.lower() not in supported_providers:
            raise ValueError(f'Model provider must be one of: {supported_providers}')
        return v.lower()
    
    @field_validator('search_query')
    @classmethod
    def validate_search_query(cls, v):
        """Validate search query is not empty or just whitespace."""
        if not v.strip():
            raise ValueError('Search query cannot be empty or just whitespace')
        return v.strip()
    
    @classmethod
    def from_environment(cls) -> 'AgentConfig':
        """Create configuration from environment variables with validation."""
        try:
            config_data = {
                'search_query': os.getenv('SEARCH_QUERY', 'Generative AI'),
                'time_range_hours': int(os.getenv('TIME_RANGE_HOURS', '72')),
                'sns_topic_arn': os.getenv('SNS_TOPIC_ARN', ''),
                'max_articles': int(os.getenv('MAX_ARTICLES', '50')),
                'summary_length': os.getenv('SUMMARY_LENGTH', 'medium'),
                'model_name': os.getenv('MODEL_NAME', 'amazon.nova-pro-v1:0'),
                'model_provider': os.getenv('MODEL_PROVIDER', 'bedrock')
            }
            
            return cls(**config_data)
            
        except ValueError as e:
            raise ConfigurationError(f"Invalid environment variable value: {e}")
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
    
    def validate_required_env_vars(self) -> None:
        """Validate that required environment variables are set."""
        required_vars = ['SNS_TOPIC_ARN']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ConfigurationError(
                f"Required environment variables not set: {', '.join(missing_vars)}"
            )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'  # Don't allow extra fields
    )


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass
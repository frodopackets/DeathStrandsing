"""Unit tests for AgentConfig model."""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError
from src.models.agent_config import AgentConfig, ConfigurationError


class TestAgentConfig:
    """Test cases for AgentConfig model."""
    
    def test_agent_config_creation_valid(self):
        """Test creating AgentConfig with valid parameters."""
        config = AgentConfig(
            search_query="Generative AI",
            time_range_hours=72,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=50,
            summary_length="medium",
            model_name="amazon.nova-pro-v1:0",
            model_provider="bedrock"
        )
        
        assert config.search_query == "Generative AI"
        assert config.time_range_hours == 72
        assert config.sns_topic_arn == "arn:aws:sns:us-east-1:123456789012:test-topic"
        assert config.max_articles == 50
        assert config.summary_length == "medium"
        assert config.model_name == "amazon.nova-pro-v1:0"
        assert config.model_provider == "bedrock"
    
    def test_search_query_validation(self):
        """Test search query validation."""
        # Valid search query
        config = AgentConfig(
            search_query="AI News",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        assert config.search_query == "AI News"
        
        # Empty search query should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
        
        # Whitespace-only search query should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="   ",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
        
        # Too long search query should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="x" * 201,  # 201 characters
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
    
    def test_time_range_hours_validation(self):
        """Test time range hours validation."""
        # Valid time range
        config = AgentConfig(
            search_query="AI",
            time_range_hours=48,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        assert config.time_range_hours == 48
        
        # Zero hours should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=0,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
        
        # Negative hours should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=-1,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
        
        # Too many hours should fail (more than 1 week)
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=169,  # More than 168 hours (1 week)
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
    
    def test_sns_topic_arn_validation(self):
        """Test SNS topic ARN validation."""
        # Valid SNS ARN
        config = AgentConfig(
            search_query="AI",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-west-2:123456789012:my-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        assert config.sns_topic_arn == "arn:aws:sns:us-west-2:123456789012:my-topic"
        
        # Invalid SNS ARN format should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="invalid-arn-format",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
        
        # Empty SNS ARN should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
    
    def test_max_articles_validation(self):
        """Test max articles validation."""
        # Valid max articles
        config = AgentConfig(
            search_query="AI",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=25,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        assert config.max_articles == 25
        
        # Zero articles should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=0,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
        
        # Too many articles should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=101,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock"
            )
    
    def test_summary_length_validation(self):
        """Test summary length validation."""
        # Valid summary lengths
        for length in ['short', 'medium', 'long']:
            config = AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length=length,
                model_name="test-model",
                model_provider="bedrock"
            )
            assert config.summary_length == length
        
        # Invalid summary length should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="invalid",
                model_name="test-model",
                model_provider="bedrock"
            )
    
    def test_model_provider_validation(self):
        """Test model provider validation."""
        # Valid model providers
        for provider in ['bedrock', 'openai', 'anthropic']:
            config = AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider=provider
            )
            assert config.model_provider == provider
        
        # Case insensitive validation
        config = AgentConfig(
            search_query="AI",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="BEDROCK"
        )
        assert config.model_provider == "bedrock"
        
        # Invalid model provider should fail
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="invalid-provider"
            )
    
    @patch.dict(os.environ, {
        'SEARCH_QUERY': 'Machine Learning',
        'TIME_RANGE_HOURS': '48',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:ml-topic',
        'MAX_ARTICLES': '30',
        'SUMMARY_LENGTH': 'long',
        'MODEL_NAME': 'amazon.nova-lite-v1:0',
        'MODEL_PROVIDER': 'bedrock'
    })
    def test_from_environment_valid(self):
        """Test creating config from valid environment variables."""
        config = AgentConfig.from_environment()
        
        assert config.search_query == "Machine Learning"
        assert config.time_range_hours == 48
        assert config.sns_topic_arn == "arn:aws:sns:us-east-1:123456789012:ml-topic"
        assert config.max_articles == 30
        assert config.summary_length == "long"
        assert config.model_name == "amazon.nova-lite-v1:0"
        assert config.model_provider == "bedrock"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_defaults(self):
        """Test creating config with default values when env vars not set."""
        # This should fail because SNS_TOPIC_ARN is required but empty by default
        with pytest.raises(ConfigurationError):
            AgentConfig.from_environment()
    
    @patch.dict(os.environ, {
        'SEARCH_QUERY': 'AI',
        'TIME_RANGE_HOURS': 'invalid',  # Invalid integer
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-topic',
        'MAX_ARTICLES': '10',
        'SUMMARY_LENGTH': 'short',
        'MODEL_NAME': 'test-model',
        'MODEL_PROVIDER': 'bedrock'
    })
    def test_from_environment_invalid_type(self):
        """Test error handling for invalid environment variable types."""
        with pytest.raises(ConfigurationError):
            AgentConfig.from_environment()
    
    @patch.dict(os.environ, {
        'SEARCH_QUERY': 'AI',
        'TIME_RANGE_HOURS': '24',
        'SNS_TOPIC_ARN': 'invalid-arn',  # Invalid ARN format
        'MAX_ARTICLES': '10',
        'SUMMARY_LENGTH': 'short',
        'MODEL_NAME': 'test-model',
        'MODEL_PROVIDER': 'bedrock'
    })
    def test_from_environment_validation_error(self):
        """Test error handling for validation errors."""
        with pytest.raises(ConfigurationError):
            AgentConfig.from_environment()
    
    def test_validate_required_env_vars(self):
        """Test validation of required environment variables."""
        config = AgentConfig(
            search_query="AI",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        
        # Should pass when SNS_TOPIC_ARN is set
        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-topic'}):
            config.validate_required_env_vars()  # Should not raise
        
        # Should fail when SNS_TOPIC_ARN is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError):
                config.validate_required_env_vars()
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = AgentConfig(
            search_query="AI",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['search_query'] == "AI"
        assert config_dict['time_range_hours'] == 24
        assert config_dict['sns_topic_arn'] == "arn:aws:sns:us-east-1:123456789012:test-topic"
        assert config_dict['max_articles'] == 10
        assert config_dict['summary_length'] == "short"
        assert config_dict['model_name'] == "test-model"
        assert config_dict['model_provider'] == "bedrock"
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            AgentConfig(
                search_query="AI",
                time_range_hours=24,
                sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
                max_articles=10,
                summary_length="short",
                model_name="test-model",
                model_provider="bedrock",
                extra_field="not allowed"  # This should cause validation error
            )
    
    def test_assignment_validation(self):
        """Test that assignment validation works."""
        config = AgentConfig(
            search_query="AI",
            time_range_hours=24,
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            max_articles=10,
            summary_length="short",
            model_name="test-model",
            model_provider="bedrock"
        )
        
        # Valid assignment should work
        config.search_query = "Machine Learning"
        assert config.search_query == "Machine Learning"
        
        # Invalid assignment should fail
        with pytest.raises(ValidationError):
            config.time_range_hours = -1


class TestConfigurationError:
    """Test cases for ConfigurationError exception."""
    
    def test_configuration_error_creation(self):
        """Test creating ConfigurationError."""
        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
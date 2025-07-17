"""Main Lambda handler for the AI News Agent."""

import asyncio
import json
import logging
import time
import uuid
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

from ..models import AgentConfig, NewsArticle, NewsSummary, ArticleSource
from ..services import GoogleNewsFetcher, StrandsAISummarizer, AWSNSPublisher

# Configure structured logging with correlation IDs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Enumeration of error types for categorized handling."""
    NEWS_FETCH_ERROR = "news_fetch_error"
    SUMMARIZATION_ERROR = "summarization_error"
    PUBLISHING_ERROR = "publishing_error"
    CONFIGURATION_ERROR = "configuration_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class WorkflowError(Exception):
    """Custom exception for workflow errors with categorization."""
    
    def __init__(self, message: str, error_type: ErrorType, recoverable: bool = True, original_error: Exception = None):
        super().__init__(message)
        self.error_type = error_type
        self.recoverable = recoverable
        self.original_error = original_error
        self.timestamp = datetime.now(timezone.utc)


class LambdaHandler:
    """Main orchestrator for the AI News Agent Lambda function with comprehensive error handling."""
    
    def __init__(self):
        """Initialize the Lambda handler with configuration and services."""
        try:
            self.config = AgentConfig.from_environment()
            self.execution_id = str(uuid.uuid4())
            
            # Initialize services with error handling
            self.news_fetcher = None
            self.ai_summarizer = None
            self.sns_publisher = None
            
            self._initialize_services()
            
            logger.info(f"Lambda handler initialized with execution ID: {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Lambda handler: {str(e)}")
            raise WorkflowError(
                f"Handler initialization failed: {str(e)}",
                ErrorType.CONFIGURATION_ERROR,
                recoverable=False,
                original_error=e
            )
    
    def _initialize_services(self):
        """Initialize all services with individual error handling."""
        try:
            self.news_fetcher = GoogleNewsFetcher(
                max_results=self.config.max_articles,
                requests_per_minute=30
            )
            logger.info("News fetcher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize news fetcher: {str(e)}")
            raise WorkflowError(
                f"News fetcher initialization failed: {str(e)}",
                ErrorType.CONFIGURATION_ERROR,
                recoverable=False,
                original_error=e
            )
        
        try:
            self.ai_summarizer = StrandsAISummarizer(self.config)
            logger.info("AI summarizer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI summarizer: {str(e)}")
            raise WorkflowError(
                f"AI summarizer initialization failed: {str(e)}",
                ErrorType.CONFIGURATION_ERROR,
                recoverable=False,
                original_error=e
            )
        
        try:
            self.sns_publisher = AWSNSPublisher(
                topic_arn=self.config.sns_topic_arn,
                region_name='us-east-1'
            )
            logger.info("SNS publisher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SNS publisher: {str(e)}")
            raise WorkflowError(
                f"SNS publisher initialization failed: {str(e)}",
                ErrorType.CONFIGURATION_ERROR,
                recoverable=False,
                original_error=e
            )
    
    async def handler(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Main Lambda handler function with comprehensive error handling and recovery.
        
        Args:
            event: Lambda event data
            context: Lambda context object
            
        Returns:
            Response dictionary with status and results
        """
        start_time = time.time()
        correlation_id = event.get('correlation_id', self.execution_id)
        
        # Set correlation ID in logging context
        logger = logging.LoggerAdapter(logging.getLogger(__name__), {'correlation_id': correlation_id})
        
        logger.info("Lambda execution started")
        
        workflow_state = {
            'articles_fetched': False,
            'summary_generated': False,
            'summary_published': False,
            'articles': [],
            'summary': None,
            'errors': []
        }
        
        try:
            # Step 1: Fetch news articles with error handling
            logger.info("Step 1: Fetching news articles")
            articles = await self._fetch_news_articles_with_recovery(correlation_id)
            workflow_state['articles'] = articles
            workflow_state['articles_fetched'] = True
            
            if not articles:
                logger.info("No relevant articles found - handling no-news scenario")
                await self._handle_no_news_scenario_with_recovery(correlation_id)
                return self._create_success_response(
                    message="No relevant news found - notification sent",
                    correlation_id=correlation_id,
                    execution_time=time.time() - start_time,
                    workflow_state=workflow_state
                )
            
            logger.info(f"Found {len(articles)} relevant articles")
            
            # Step 2: Generate AI summary with error handling
            logger.info("Step 2: Generating AI summary")
            summary = await self._generate_summary_with_recovery(articles, correlation_id)
            workflow_state['summary'] = summary
            workflow_state['summary_generated'] = True
            
            # Step 3: Publish summary to SNS with error handling
            logger.info("Step 3: Publishing summary to SNS")
            publish_success = await self._publish_summary_with_recovery(summary, correlation_id)
            workflow_state['summary_published'] = publish_success
            
            if not publish_success:
                # Try fallback publishing methods
                logger.warning("Primary publishing failed, attempting recovery")
                fallback_success = await self._attempt_fallback_publishing(summary, correlation_id)
                workflow_state['summary_published'] = fallback_success
                
                if not fallback_success:
                    return self._create_partial_success_response(
                        message="Summary generated but publishing failed",
                        correlation_id=correlation_id,
                        execution_time=time.time() - start_time,
                        workflow_state=workflow_state
                    )
            
            # Complete success
            execution_time = time.time() - start_time
            logger.info(f"Lambda execution completed successfully in {execution_time:.2f} seconds")
            
            return self._create_success_response(
                message="AI News Agent executed successfully",
                correlation_id=correlation_id,
                execution_time=execution_time,
                summary_id=summary.id,
                article_count=len(articles),
                workflow_state=workflow_state
            )
            
        except WorkflowError as we:
            return await self._handle_workflow_error(we, correlation_id, start_time, workflow_state)
            
        except Exception as e:
            return await self._handle_unexpected_error(e, correlation_id, start_time, workflow_state)
    
    async def _fetch_news_articles_with_recovery(self, correlation_id: str) -> List[NewsArticle]:
        """
        Fetch news articles with error handling and recovery.
        
        Args:
            correlation_id: Correlation ID for logging
            
        Returns:
            List of NewsArticle objects
            
        Raises:
            WorkflowError: If fetching fails after all recovery attempts
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"News fetch attempt {attempt + 1}/{max_retries}")
                
                # Fetch articles from Google News
                raw_articles = await self.news_fetcher.fetch_news(
                    query=self.config.search_query,
                    time_range_hours=self.config.time_range_hours
                )
                
                if not raw_articles:
                    logger.warning("No articles returned from news fetcher")
                    return []
                
                # Filter articles for relevance
                filtered_articles = await self.news_fetcher.filter_articles(raw_articles)
                
                # Limit to max articles
                if len(filtered_articles) > self.config.max_articles:
                    filtered_articles = filtered_articles[:self.config.max_articles]
                    logger.info(f"Limited articles to {self.config.max_articles}")
                
                logger.info(f"Successfully fetched {len(filtered_articles)} articles")
                return filtered_articles
                
            except Exception as e:
                logger.warning(f"News fetch attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries - 1:
                    # Final attempt failed
                    raise WorkflowError(
                        f"News fetching failed after {max_retries} attempts: {str(e)}",
                        ErrorType.NEWS_FETCH_ERROR,
                        recoverable=False,
                        original_error=e
                    )
                
                # Wait before retry with exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        return []
    
    async def _generate_summary_with_recovery(self, articles: List[NewsArticle], correlation_id: str) -> NewsSummary:
        """
        Generate AI summary with error handling and fallback.
        
        Args:
            articles: List of NewsArticle objects
            correlation_id: Correlation ID for logging
            
        Returns:
            NewsSummary object
            
        Raises:
            WorkflowError: If summary generation fails after all recovery attempts
        """
        try:
            # Primary attempt with Strands AI
            logger.info("Attempting primary AI summarization with Strands SDK")
            summary = await self.ai_summarizer.generate_summary(articles)
            logger.info(f"Generated summary with {len(summary.key_points)} key points")
            return summary
            
        except Exception as e:
            logger.warning(f"Primary AI summarization failed: {str(e)}")
            
            # Attempt fallback summarization
            try:
                logger.info("Attempting fallback summarization")
                summary = await self._generate_fallback_summary(articles)
                logger.info("Fallback summarization successful")
                return summary
                
            except Exception as fallback_error:
                logger.error(f"Fallback summarization also failed: {str(fallback_error)}")
                raise WorkflowError(
                    f"Summary generation failed: Primary error: {str(e)}, Fallback error: {str(fallback_error)}",
                    ErrorType.SUMMARIZATION_ERROR,
                    recoverable=False,
                    original_error=e
                )
    
    async def _publish_summary_with_recovery(self, summary: NewsSummary, correlation_id: str) -> bool:
        """
        Publish summary with error handling and retry logic.
        
        Args:
            summary: NewsSummary object to publish
            correlation_id: Correlation ID for logging
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            success = await self.sns_publisher.publish_summary(summary)
            if success:
                logger.info(f"Successfully published summary {summary.id}")
                return True
            else:
                logger.warning(f"Failed to publish summary {summary.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing summary: {str(e)}")
            return False
    
    async def _handle_no_news_scenario_with_recovery(self, correlation_id: str) -> None:
        """
        Handle no-news scenario with comprehensive error handling and recovery.
        
        Args:
            correlation_id: Correlation ID for logging
        """
        logger.info("Handling no-news scenario")
        
        # Log the no-news event for monitoring
        await self._log_no_news_event(correlation_id)
        
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"No-news notification attempt {attempt + 1}/{max_retries}")
                success = await self.sns_publisher.send_no_news_notification()
                
                if success:
                    logger.info("Successfully sent no-news notification")
                    await self._log_notification_success(correlation_id, "no_news")
                    return
                else:
                    logger.warning(f"No-news notification attempt {attempt + 1} failed")
                    
            except Exception as e:
                logger.warning(f"No-news notification attempt {attempt + 1} error: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
        
        logger.error("Failed to send no-news notification after all attempts")
        await self._log_notification_failure(correlation_id, "no_news")
    
    async def _log_no_news_event(self, correlation_id: str) -> None:
        """
        Log no-news event for monitoring and analytics.
        
        Args:
            correlation_id: Correlation ID for logging
        """
        try:
            event_data = {
                'event_type': 'no_news_detected',
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'search_query': self.config.search_query,
                'time_range_hours': self.config.time_range_hours,
                'execution_id': self.execution_id
            }
            
            logger.info(f"No-news event logged: {json.dumps(event_data)}")
            
        except Exception as e:
            logger.warning(f"Failed to log no-news event: {str(e)}")
    
    async def _log_notification_success(self, correlation_id: str, notification_type: str) -> None:
        """
        Log successful notification delivery.
        
        Args:
            correlation_id: Correlation ID for logging
            notification_type: Type of notification (e.g., 'no_news', 'summary')
        """
        try:
            success_data = {
                'event_type': 'notification_success',
                'notification_type': notification_type,
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'execution_id': self.execution_id
            }
            
            logger.info(f"Notification success logged: {json.dumps(success_data)}")
            
        except Exception as e:
            logger.warning(f"Failed to log notification success: {str(e)}")
    
    async def _log_notification_failure(self, correlation_id: str, notification_type: str) -> None:
        """
        Log failed notification delivery.
        
        Args:
            correlation_id: Correlation ID for logging
            notification_type: Type of notification (e.g., 'no_news', 'summary')
        """
        try:
            failure_data = {
                'event_type': 'notification_failure',
                'notification_type': notification_type,
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'execution_id': self.execution_id
            }
            
            logger.error(f"Notification failure logged: {json.dumps(failure_data)}")
            
        except Exception as e:
            logger.warning(f"Failed to log notification failure: {str(e)}")
    
    def _is_no_news_scenario(self, articles: List[NewsArticle]) -> bool:
        """
        Determine if this is a no-news scenario.
        
        Args:
            articles: List of articles to evaluate
            
        Returns:
            True if no relevant news was found, False otherwise
        """
        if not articles:
            return True
        
        if len(articles) == 0:
            return True
        
        # Additional logic could be added here to detect low-quality scenarios
        # For example, if all articles have very low relevance scores
        relevant_articles = [
            article for article in articles 
            if article.relevance_score and article.relevance_score > 0.1
        ]
        
        if len(relevant_articles) == 0:
            logger.info("All articles filtered out due to low relevance scores")
            return True
        
        return False
    
    async def _should_send_no_news_notification(self, correlation_id: str) -> bool:
        """
        Determine if a no-news notification should be sent based on various factors.
        
        Args:
            correlation_id: Correlation ID for logging
            
        Returns:
            True if notification should be sent, False otherwise
        """
        try:
            # Check if we've sent a no-news notification recently
            # This could be enhanced with a database or cache check
            
            # For now, always send notification
            # In production, you might want to implement logic to avoid
            # sending too many no-news notifications in a short period
            
            logger.info("Determining if no-news notification should be sent")
            return True
            
        except Exception as e:
            logger.warning(f"Error determining notification necessity: {str(e)}")
            # Default to sending notification if we can't determine otherwise
            return True
    
    async def _attempt_fallback_publishing(self, summary: NewsSummary, correlation_id: str) -> bool:
        """
        Attempt fallback publishing methods.
        
        Args:
            summary: NewsSummary object to publish
            correlation_id: Correlation ID for logging
            
        Returns:
            True if any fallback method succeeded, False otherwise
        """
        logger.info("Attempting fallback publishing methods")
        
        # Fallback 1: Retry with simplified message
        try:
            logger.info("Fallback 1: Simplified message format")
            simplified_summary = self._create_simplified_summary(summary)
            success = await self.sns_publisher.publish_summary(simplified_summary)
            if success:
                logger.info("Fallback publishing with simplified message succeeded")
                return True
        except Exception as e:
            logger.warning(f"Fallback 1 failed: {str(e)}")
        
        # Fallback 2: Plain text notification
        try:
            logger.info("Fallback 2: Plain text notification")
            plain_text = summary.format_for_plain_text()
            # Create a minimal summary for plain text publishing
            minimal_summary = NewsSummary(
                summary=plain_text[:500] + "..." if len(plain_text) > 500 else plain_text,
                key_points=summary.key_points[:3],  # Limit key points
                sources=summary.sources[:5],  # Limit sources
                generated_at=summary.generated_at,
                article_count=summary.article_count
            )
            success = await self.sns_publisher.publish_summary(minimal_summary)
            if success:
                logger.info("Fallback publishing with plain text succeeded")
                return True
        except Exception as e:
            logger.warning(f"Fallback 2 failed: {str(e)}")
        
        logger.error("All fallback publishing methods failed")
        return False
    
    async def _generate_fallback_summary(self, articles: List[NewsArticle]) -> NewsSummary:
        """
        Generate a fallback summary when AI summarization fails.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            NewsSummary object with basic summarization
        """
        logger.info("Generating fallback summary")
        
        # Create basic summary from article titles and sources
        summary_parts = []
        key_points = []
        sources = []
        
        for i, article in enumerate(articles[:10], 1):  # Limit to first 10 articles
            summary_parts.append(f"{article.title} ({article.source})")
            key_points.append(f"{article.title[:100]}{'...' if len(article.title) > 100 else ''}")
            
            source = ArticleSource(
                title=article.title,
                url=article.url,
                source=article.source,
                published_at=article.published_at
            )
            sources.append(source)
        
        fallback_summary_text = (
            f"Recent Generative AI developments from {len(articles)} sources include: " +
            "; ".join(summary_parts[:5]) +  # Limit summary length
            (f" and {len(articles) - 5} more articles." if len(articles) > 5 else "")
        )
        
        return NewsSummary(
            summary=fallback_summary_text,
            key_points=key_points[:8],  # Limit key points
            sources=sources,
            generated_at=datetime.now(timezone.utc),
            article_count=len(articles)
        )
    
    def _create_simplified_summary(self, summary: NewsSummary) -> NewsSummary:
        """
        Create a simplified version of the summary for fallback publishing.
        
        Args:
            summary: Original NewsSummary object
            
        Returns:
            Simplified NewsSummary object
        """
        # Truncate summary text
        simplified_text = summary.summary[:1000] + "..." if len(summary.summary) > 1000 else summary.summary
        
        # Limit key points
        limited_key_points = summary.key_points[:5]
        
        # Limit sources
        limited_sources = summary.sources[:10]
        
        return NewsSummary(
            summary=simplified_text,
            key_points=limited_key_points,
            sources=limited_sources,
            generated_at=summary.generated_at,
            article_count=summary.article_count,
            id=summary.id
        )
    
    async def _handle_workflow_error(
        self, 
        error: WorkflowError, 
        correlation_id: str, 
        start_time: float, 
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle categorized workflow errors with appropriate responses.
        
        Args:
            error: WorkflowError instance
            correlation_id: Correlation ID for logging
            start_time: Execution start time
            workflow_state: Current workflow state
            
        Returns:
            Error response dictionary
        """
        execution_time = time.time() - start_time
        workflow_state['errors'].append({
            'type': error.error_type.value,
            'message': str(error),
            'recoverable': error.recoverable,
            'timestamp': error.timestamp.isoformat()
        })
        
        logger.error(f"Workflow error ({error.error_type.value}): {str(error)}")
        
        # Log full traceback for debugging
        if error.original_error:
            logger.error(f"Original error: {str(error.original_error)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Determine response based on error type and recoverability
        if error.error_type == ErrorType.NEWS_FETCH_ERROR and not error.recoverable:
            # Send no-news notification as fallback
            try:
                await self._handle_no_news_scenario_with_recovery(correlation_id)
                return self._create_partial_success_response(
                    message="News fetching failed, sent no-news notification",
                    correlation_id=correlation_id,
                    execution_time=execution_time,
                    workflow_state=workflow_state
                )
            except Exception:
                pass
        
        return self._create_error_response(
            error_message=str(error),
            correlation_id=correlation_id,
            execution_time=execution_time,
            error_type=error.error_type.value,
            workflow_state=workflow_state
        )
    
    async def _handle_unexpected_error(
        self, 
        error: Exception, 
        correlation_id: str, 
        start_time: float, 
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle unexpected errors with full logging and graceful degradation.
        
        Args:
            error: Exception instance
            correlation_id: Correlation ID for logging
            start_time: Execution start time
            workflow_state: Current workflow state
            
        Returns:
            Error response dictionary
        """
        execution_time = time.time() - start_time
        
        # Log full error details
        logger.error(f"Unexpected error after {execution_time:.2f} seconds: {str(error)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        workflow_state['errors'].append({
            'type': ErrorType.UNKNOWN_ERROR.value,
            'message': str(error),
            'recoverable': False,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return self._create_error_response(
            error_message=f"Unexpected error: {str(error)}",
            correlation_id=correlation_id,
            execution_time=execution_time,
            error_type=ErrorType.UNKNOWN_ERROR.value,
            workflow_state=workflow_state
        )
    
    def _create_partial_success_response(
        self, 
        message: str, 
        correlation_id: str,
        execution_time: float,
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a partial success response dictionary."""
        return {
            'statusCode': 206,  # Partial Content
            'body': json.dumps({
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'correlation_id': correlation_id,
                'execution_time_seconds': round(execution_time, 2),
                'workflow_state': workflow_state,
                'status': 'partial_success'
            })
        }
    
    async def _fetch_news_articles(self) -> list[NewsArticle]:
        """
        Fetch and filter news articles.
        
        Returns:
            List of relevant NewsArticle objects
        """
        try:
            # Fetch articles from Google News
            raw_articles = await self.news_fetcher.fetch_news(
                query=self.config.search_query,
                time_range_hours=self.config.time_range_hours
            )
            
            if not raw_articles:
                logger.warning("No articles returned from news fetcher")
                return []
            
            # Filter articles for relevance
            filtered_articles = await self.news_fetcher.filter_articles(raw_articles)
            
            # Limit to max articles
            if len(filtered_articles) > self.config.max_articles:
                filtered_articles = filtered_articles[:self.config.max_articles]
                logger.info(f"Limited articles to {self.config.max_articles}")
            
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error fetching news articles: {str(e)}")
            raise Exception(f"News fetching failed: {str(e)}")
    
    async def _generate_summary(self, articles: list[NewsArticle]) -> NewsSummary:
        """
        Generate AI summary from articles.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            NewsSummary object
        """
        try:
            summary = await self.ai_summarizer.generate_summary(articles)
            logger.info(f"Generated summary with {len(summary.key_points)} key points")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise Exception(f"Summary generation failed: {str(e)}")
    
    async def _publish_summary(self, summary: NewsSummary) -> bool:
        """
        Publish summary to SNS.
        
        Args:
            summary: NewsSummary object to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            success = await self.sns_publisher.publish_summary(summary)
            if success:
                logger.info(f"Successfully published summary {summary.id}")
            else:
                logger.error(f"Failed to publish summary {summary.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing summary: {str(e)}")
            return False
    
    async def _handle_no_news_scenario(self) -> None:
        """Handle scenario when no relevant news is found."""
        try:
            success = await self.sns_publisher.send_no_news_notification()
            if success:
                logger.info("Successfully sent no-news notification")
            else:
                logger.error("Failed to send no-news notification")
                
        except Exception as e:
            logger.error(f"Error handling no-news scenario: {str(e)}")
            # Don't raise exception here as this is not critical
    
    def _create_success_response(
        self, 
        message: str, 
        correlation_id: str,
        execution_time: float,
        summary_id: Optional[str] = None,
        article_count: Optional[int] = None,
        workflow_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a success response dictionary."""
        response_body = {
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'correlation_id': correlation_id,
            'execution_time_seconds': round(execution_time, 2),
            'config': {
                'search_query': self.config.search_query,
                'time_range_hours': self.config.time_range_hours,
                'max_articles': self.config.max_articles,
                'summary_length': self.config.summary_length
            }
        }
        
        if summary_id:
            response_body['summary_id'] = summary_id
        if article_count is not None:
            response_body['article_count'] = article_count
        if workflow_state:
            response_body['workflow_state'] = workflow_state
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }
    
    def _create_error_response(
        self, 
        error_message: str, 
        correlation_id: str,
        execution_time: float,
        error_type: Optional[str] = None,
        workflow_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an error response dictionary."""
        response_body = {
            'error': 'Internal server error',
            'message': error_message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'correlation_id': correlation_id,
            'execution_time_seconds': round(execution_time, 2)
        }
        
        if error_type:
            response_body['error_type'] = error_type
        if workflow_state:
            response_body['workflow_state'] = workflow_state
        
        return {
            'statusCode': 500,
            'body': json.dumps(response_body)
        }


# Lambda entry point
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point."""
    import asyncio
    handler_instance = LambdaHandler()
    return asyncio.run(handler_instance.handler(event, context))
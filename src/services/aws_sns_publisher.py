"""AWS SNS publisher implementation for the AI News Agent."""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import time
import random
from datetime import datetime, timezone

from .sns_publisher import SNSPublisher
from ..models import NewsSummary


logger = logging.getLogger(__name__)


class AWSNSPublisher(SNSPublisher):
    """AWS SNS implementation of the SNS publisher."""
    
    def __init__(self, topic_arn: str, region_name: str = 'us-east-1'):
        """
        Initialize AWS SNS publisher.
        
        Args:
            topic_arn: ARN of the SNS topic to publish to
            region_name: AWS region name (default: us-east-1)
        """
        self.topic_arn = topic_arn
        self.region_name = region_name
        self.sns_client = boto3.client('sns', region_name=region_name)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 60.0  # Maximum delay in seconds
        self.backoff_multiplier = 2.0
        self.jitter = True
    
    async def publish_summary(self, summary: NewsSummary) -> bool:
        """
        Publish a news summary to SNS topic with retry logic.
        
        Args:
            summary: NewsSummary object to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Format message for email delivery
            message_body = await self.format_message(summary)
            
            # Create message attributes for filtering
            message_attributes = {
                'MessageType': {
                    'DataType': 'String',
                    'StringValue': 'NewsSummary'
                },
                'ArticleCount': {
                    'DataType': 'Number',
                    'StringValue': str(summary.article_count)
                },
                'GeneratedAt': {
                    'DataType': 'String',
                    'StringValue': summary.generated_at.isoformat()
                }
            }
            
            # Attempt to publish with retry logic
            return await self._publish_with_retry(
                message=message_body,
                subject=f"AI News Summary - {summary.generated_at.strftime('%B %d, %Y')}",
                message_attributes=message_attributes
            )
            
        except Exception as e:
            logger.error(f"Failed to publish summary {summary.id}: {str(e)}")
            return False
    
    async def format_message(self, summary: NewsSummary) -> str:
        """
        Format a summary for email delivery.
        
        Args:
            summary: NewsSummary object to format
            
        Returns:
            Formatted message string with both HTML and plain text
        """
        try:
            # Create structured message with both HTML and plain text versions
            html_content = self._format_html_message(summary)
            text_content = summary.format_for_plain_text()
            
            # Create JSON message for SNS with multiple formats
            message_data = {
                'default': text_content,
                'email': html_content,
                'email-json': {
                    'html': html_content,
                    'text': text_content
                }
            }
            
            return json.dumps(message_data)
            
        except Exception as e:
            logger.error(f"Failed to format message for summary {summary.id}: {str(e)}")
            # Fallback to plain text
            return summary.format_for_plain_text()
    
    async def send_no_news_notification(self) -> bool:
        """
        Send notification when no relevant news is found.
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            message = {
                'default': self._get_no_news_text(),
                'email': self._get_no_news_html()
            }
            
            message_attributes = {
                'MessageType': {
                    'DataType': 'String',
                    'StringValue': 'NoNewsNotification'
                }
            }
            
            return await self._publish_with_retry(
                message=json.dumps(message),
                subject="AI News Summary - No Updates Today",
                message_attributes=message_attributes
            )
            
        except Exception as e:
            logger.error(f"Failed to send no-news notification: {str(e)}")
            return False
    
    async def get_subscription_status(self) -> Dict[str, Any]:
        """
        Get the status of all subscriptions for the topic.
        
        Returns:
            Dictionary containing subscription information
        """
        try:
            response = self.sns_client.list_subscriptions_by_topic(TopicArn=self.topic_arn)
            subscriptions = response.get('Subscriptions', [])
            
            status_info = {
                'topic_arn': self.topic_arn,
                'total_subscriptions': len(subscriptions),
                'confirmed_subscriptions': 0,
                'pending_subscriptions': 0,
                'subscriptions': []
            }
            
            for sub in subscriptions:
                sub_info = {
                    'subscription_arn': sub.get('SubscriptionArn'),
                    'protocol': sub.get('Protocol'),
                    'endpoint': sub.get('Endpoint'),
                    'confirmed': sub.get('SubscriptionArn') != 'PendingConfirmation'
                }
                
                if sub_info['confirmed']:
                    status_info['confirmed_subscriptions'] += 1
                else:
                    status_info['pending_subscriptions'] += 1
                
                status_info['subscriptions'].append(sub_info)
            
            logger.info(f"Retrieved subscription status: {status_info['confirmed_subscriptions']} confirmed, {status_info['pending_subscriptions']} pending")
            return status_info
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get subscription status: {str(e)}")
            return {'error': str(e)}
    
    async def track_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Track delivery status for a published message.
        
        Args:
            message_id: SNS message ID to track
            
        Returns:
            Dictionary containing delivery status information
        """
        try:
            # Get topic attributes to check if delivery status logging is enabled
            topic_attrs = self.sns_client.get_topic_attributes(TopicArn=self.topic_arn)
            attributes = topic_attrs.get('Attributes', {})
            
            delivery_status = {
                'message_id': message_id,
                'topic_arn': self.topic_arn,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'delivery_status_logging_enabled': {
                    'http': attributes.get('DeliveryStatusLogging', {}).get('http', 'false') == 'true',
                    'email': attributes.get('DeliveryStatusLogging', {}).get('email', 'false') == 'true',
                    'sms': attributes.get('DeliveryStatusLogging', {}).get('sms', 'false') == 'true'
                }
            }
            
            logger.info(f"Tracked delivery status for message {message_id}")
            return delivery_status
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to track delivery status for message {message_id}: {str(e)}")
            return {'error': str(e), 'message_id': message_id}
    
    async def handle_subscription_confirmation(self, token: str, topic_arn: str) -> bool:
        """
        Handle subscription confirmation for pending subscriptions.
        
        Args:
            token: Confirmation token from SNS
            topic_arn: Topic ARN for the subscription
            
        Returns:
            True if confirmation was successful, False otherwise
        """
        try:
            response = self.sns_client.confirm_subscription(
                TopicArn=topic_arn,
                Token=token
            )
            
            subscription_arn = response.get('SubscriptionArn')
            logger.info(f"Successfully confirmed subscription: {subscription_arn}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to confirm subscription with token {token}: {str(e)}")
            return False
    
    async def log_delivery_attempt(self, message_id: str, delivery_info: Dict[str, Any]) -> None:
        """
        Log delivery attempt information for monitoring and debugging.
        
        Args:
            message_id: SNS message ID
            delivery_info: Dictionary containing delivery information
        """
        try:
            log_entry = {
                'message_id': message_id,
                'topic_arn': self.topic_arn,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'delivery_info': delivery_info
            }
            
            logger.info(f"Delivery attempt logged: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to log delivery attempt for message {message_id}: {str(e)}")

    async def _publish_with_retry(self, message: str, subject: str, 
                                message_attributes: Dict[str, Any]) -> bool:
        """
        Publish message to SNS with exponential backoff retry logic and delivery tracking.
        
        Args:
            message: Message content to publish
            subject: Message subject
            message_attributes: SNS message attributes
            
        Returns:
            True if published successfully, False otherwise
        """
        last_exception = None
        message_id = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.sns_client.publish(
                    TopicArn=self.topic_arn,
                    Message=message,
                    Subject=subject,
                    MessageAttributes=message_attributes,
                    MessageStructure='json'
                )
                
                message_id = response.get('MessageId')
                logger.info(f"Successfully published message {message_id} to SNS topic")
                
                # Track delivery status
                delivery_status = await self.track_delivery_status(message_id)
                await self.log_delivery_attempt(message_id, {
                    'status': 'published',
                    'attempt': attempt + 1,
                    'subject': subject,
                    'delivery_status': delivery_status
                })
                
                return True
                
            except (ClientError, BotoCoreError) as e:
                last_exception = e
                error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
                
                logger.warning(f"SNS publish attempt {attempt + 1} failed: {error_code} - {str(e)}")
                
                # Log failed attempt
                await self.log_delivery_attempt(f"failed-{attempt}", {
                    'status': 'failed',
                    'attempt': attempt + 1,
                    'error_code': error_code,
                    'error_message': str(e),
                    'subject': subject
                })
                
                # Don't retry on certain error types
                if error_code in ['InvalidParameter', 'AuthorizationError', 'NotFound']:
                    logger.error(f"Non-retryable error: {error_code}")
                    break
                
                # Calculate delay for next retry
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
            
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error during SNS publish: {str(e)}")
                
                # Log unexpected error
                await self.log_delivery_attempt(f"error-{attempt}", {
                    'status': 'error',
                    'attempt': attempt + 1,
                    'error_message': str(e),
                    'subject': subject
                })
                break
        
        logger.error(f"Failed to publish message after {self.max_retries + 1} attempts. Last error: {str(last_exception)}")
        return False
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (multiplier ^ attempt)
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        
        # Cap at maximum delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _format_html_message(self, summary: NewsSummary) -> str:
        """
        Format summary as HTML for email delivery.
        
        Args:
            summary: NewsSummary object to format
            
        Returns:
            HTML formatted message
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ margin-bottom: 20px; }}
                .key-points {{ margin-bottom: 20px; }}
                .sources {{ margin-bottom: 20px; }}
                .source-item {{ margin-bottom: 10px; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #007cba; }}
                .source-title {{ font-weight: bold; color: #007cba; }}
                .source-meta {{ color: #666; font-size: 0.9em; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 8px; }}
                a {{ color: #007cba; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI News Summary</h1>
                <p><strong>Date:</strong> {summary.generated_at.strftime('%B %d, %Y')}</p>
                <p><strong>Generated at:</strong> {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Articles analyzed:</strong> {summary.article_count}</p>
            </div>
            
            <div class="summary">
                <h2>📋 Summary</h2>
                <p>{summary.summary}</p>
            </div>
        """
        
        if summary.key_points:
            html += """
            <div class="key-points">
                <h2>🔑 Key Points</h2>
                <ul>
            """
            for point in summary.key_points:
                html += f"<li>{point}</li>"
            html += "</ul></div>"
        
        if summary.sources:
            html += """
            <div class="sources">
                <h2>📰 Sources</h2>
            """
            for i, source in enumerate(summary.sources, 1):
                formatted_date = source.published_at.strftime('%Y-%m-%d')
                html += f"""
                <div class="source-item">
                    <div class="source-title">{i}. {source.title}</div>
                    <div class="source-meta">{source.source} • {formatted_date}</div>
                    <div><a href="{source.url}" target="_blank">Read full article</a></div>
                </div>
                """
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _get_no_news_text(self) -> str:
        """Get plain text no-news notification."""
        return """AI News Summary - No Updates Today

No relevant Generative AI news articles were found in the last 72 hours.

This could mean:
- There were no significant developments in Generative AI today
- News sources may not have published relevant content yet
- The search criteria may need adjustment

You'll receive the next summary when relevant news becomes available.

---
AI News Agent
"""
    
    def _get_no_news_html(self) -> str:
        """Get HTML no-news notification."""
        return """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .content { margin-bottom: 20px; }
                .footer { color: #666; font-size: 0.9em; border-top: 1px solid #ddd; padding-top: 10px; }
                ul { padding-left: 20px; }
                li { margin-bottom: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI News Summary</h1>
                <h2>No Updates Today</h2>
            </div>
            
            <div class="content">
                <p>No relevant Generative AI news articles were found in the last 72 hours.</p>
                
                <p>This could mean:</p>
                <ul>
                    <li>There were no significant developments in Generative AI today</li>
                    <li>News sources may not have published relevant content yet</li>
                    <li>The search criteria may need adjustment</li>
                </ul>
                
                <p>You'll receive the next summary when relevant news becomes available.</p>
            </div>
            
            <div class="footer">
                <p>AI News Agent</p>
            </div>
        </body>
        </html>
        """
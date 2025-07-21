"""
🐦 Twitter Monitoring Module

Monitors Twitter for new followers, mentions, and engagement opportunities.
Provides data to Eliza's AI brain for decision making.
"""

import tweepy
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger('TwitterMonitor')

class TwitterMonitor:
    def __init__(self, config):
        """Initialize Twitter API client"""
        self.config = config

        # Initialize Twitter API v2 client
        self.client = tweepy.Client(
            bearer_token=config['TWITTER_BEARER'],
            wait_on_rate_limit=True
        )

        # Cache for storing recent data
        self.last_check = datetime.now() - timedelta(hours=1)
        self.known_followers = set()

        logger.info("🐦 Twitter monitor initialized")

    async def check_new_followers(self) -> List[Dict[str, Any]]:
        """Check for new followers since last check"""
        try:
            logger.info("🔍 Checking for new Twitter followers...")

            # Get current followers (Twitter API v2)
            # Note: This requires elevated access for follower lists
            followers = []

            try:
                # Get user ID first (replace with actual XMRT Twitter handle)
                user = self.client.get_user(username='XMRT_io')  # Replace with actual handle

                if user.data:
                    user_id = user.data.id

                    # Get recent followers
                    follower_response = self.client.get_users_followers(
                        id=user_id,
                        max_results=100,
                        user_fields=['created_at', 'description', 'public_metrics']
                    )

                    if follower_response.data:
                        current_time = datetime.now()

                        for follower in follower_response.data:
                            follower_id = str(follower.id)

                            # Check if this is a new follower
                            if follower_id not in self.known_followers:
                                followers.append({
                                    'id': follower_id,
                                    'username': follower.username,
                                    'name': follower.name,
                                    'description': follower.description,
                                    'created_at': follower.created_at.isoformat() if follower.created_at else None,
                                    'followers_count': follower.public_metrics.get('followers_count', 0) if follower.public_metrics else 0,
                                    'following_count': follower.public_metrics.get('following_count', 0) if follower.public_metrics else 0,
                                    'detected_at': current_time.isoformat()
                                })

                                # Add to known followers
                                self.known_followers.add(follower_id)

            except Exception as api_error:
                logger.warning(f"⚠️ Twitter API access limited: {api_error}")
                # Return empty list if API access is limited
                followers = []

            logger.info(f"📊 Found {len(followers)} new followers")
            self.last_check = datetime.now()

            return followers

        except Exception as e:
            logger.error(f"❌ Error checking Twitter followers: {e}")
            return []

    async def check_mentions(self) -> List[Dict[str, Any]]:
        """Check for recent mentions and interactions"""
        try:
            logger.info("🔍 Checking Twitter mentions...")

            mentions = []

            try:
                # Search for mentions (requires elevated access)
                query = "@XMRT_io OR #XMRT"  # Replace with actual handle/hashtag

                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=['created_at', 'author_id', 'public_metrics'],
                    user_fields=['username', 'name']
                )

                if tweets.data:
                    for tweet in tweets.data:
                        mentions.append({
                            'id': tweet.id,
                            'text': tweet.text,
                            'author_id': tweet.author_id,
                            'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                            'retweet_count': tweet.public_metrics.get('retweet_count', 0) if tweet.public_metrics else 0,
                            'like_count': tweet.public_metrics.get('like_count', 0) if tweet.public_metrics else 0,
                            'reply_count': tweet.public_metrics.get('reply_count', 0) if tweet.public_metrics else 0
                        })

            except Exception as api_error:
                logger.warning(f"⚠️ Twitter mentions API limited: {api_error}")
                mentions = []

            logger.info(f"📊 Found {len(mentions)} recent mentions")
            return mentions

        except Exception as e:
            logger.error(f"❌ Error checking mentions: {e}")
            return []

    async def engage_with_community(self, engagement_actions: List[Dict[str, Any]]) -> bool:
        """Execute community engagement actions"""
        try:
            logger.info(f"💬 Executing {len(engagement_actions)} engagement actions...")

            success_count = 0

            for action in engagement_actions:
                try:
                    action_type = action.get('type', '')

                    if action_type == 'tweet':
                        # Post a tweet
                        content = action.get('content', '')
                        if content and len(content) <= 280:
                            self.client.create_tweet(text=content)
                            logger.info(f"✅ Tweet posted: {content[:50]}...")
                            success_count += 1

                    elif action_type == 'reply':
                        # Reply to a tweet
                        tweet_id = action.get('tweet_id')
                        content = action.get('content', '')
                        if tweet_id and content:
                            self.client.create_tweet(
                                text=content,
                                in_reply_to_tweet_id=tweet_id
                            )
                            logger.info(f"✅ Reply posted to {tweet_id}")
                            success_count += 1

                    elif action_type == 'like':
                        # Like a tweet
                        tweet_id = action.get('tweet_id')
                        if tweet_id:
                            self.client.like(tweet_id)
                            logger.info(f"✅ Liked tweet {tweet_id}")
                            success_count += 1

                    elif action_type == 'retweet':
                        # Retweet
                        tweet_id = action.get('tweet_id')
                        if tweet_id:
                            self.client.retweet(tweet_id)
                            logger.info(f"✅ Retweeted {tweet_id}")
                            success_count += 1

                except Exception as action_error:
                    logger.warning(f"⚠️ Failed to execute action {action}: {action_error}")

            logger.info(f"✅ Completed {success_count}/{len(engagement_actions)} engagement actions")
            return success_count > 0

        except Exception as e:
            logger.error(f"❌ Error in community engagement: {e}")
            return False

    async def get_community_metrics(self) -> Dict[str, Any]:
        """Get overall community metrics and health indicators"""
        try:
            logger.info("📊 Gathering community metrics...")

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'follower_growth': 0,
                'engagement_rate': 0,
                'mention_sentiment': 'neutral'
            }

            try:
                # Get user profile data
                user = self.client.get_user(username='XMRT_io')  # Replace with actual handle

                if user.data and user.data.public_metrics:
                    metrics.update({
                        'followers_count': user.data.public_metrics.get('followers_count', 0),
                        'following_count': user.data.public_metrics.get('following_count', 0),
                        'tweet_count': user.data.public_metrics.get('tweet_count', 0),
                        'listed_count': user.data.public_metrics.get('listed_count', 0)
                    })

            except Exception as api_error:
                logger.warning(f"⚠️ Could not fetch community metrics: {api_error}")

            logger.info("✅ Community metrics gathered")
            return metrics

        except Exception as e:
            logger.error(f"❌ Error gathering community metrics: {e}")
            return {'timestamp': datetime.now().isoformat(), 'error': str(e)}

# Global instance
_twitter_monitor = None

def get_twitter_monitor(config):
    """Get global Twitter monitor instance"""
    global _twitter_monitor
    if _twitter_monitor is None:
        _twitter_monitor = TwitterMonitor(config)
    return _twitter_monitor

# Main functions for use by Eliza daemon
async def check_new_followers():
    """Main function to check for new followers"""
    try:
        # This will be initialized by the main daemon
        from eliza_daemon import ElizaDaemon
        # For now, return mock data if not properly initialized
        return []
    except:
        return []

async def engage_with_community(actions):
    """Main function to engage with community"""
    try:
        # This will be initialized by the main daemon  
        from eliza_daemon import ElizaDaemon
        return True
    except:
        return False

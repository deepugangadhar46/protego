"""
Platform monitoring modules for VIP threat detection
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiohttp
import praw
from newsapi import NewsApiClient
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BasePlatformMonitor:
    """Base class for platform monitors"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.is_enabled = False
        
    async def monitor_vip(self, vip_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Monitor a VIP on this platform"""
        raise NotImplementedError
        
    def is_api_configured(self) -> bool:
        """Check if API credentials are configured"""
        raise NotImplementedError

class RedditMonitor(BasePlatformMonitor):
    """Reddit monitoring using PRAW"""
    
    def __init__(self):
        super().__init__("reddit")
        self.reddit = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Reddit client"""
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'Protego-VIP-Monitor-v1.0')
            
            if client_id and client_secret:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                    check_for_async=False  # silence async environment warnings
                )
                self.is_enabled = True
                logger.info("Reddit monitor initialized successfully")
            else:
                logger.warning("Reddit API credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            
    def is_api_configured(self) -> bool:
        return self.reddit is not None
        
    async def monitor_vip(self, vip_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Monitor VIP mentions on Reddit (run blocking PRAW calls in a thread)."""
        if not self.is_enabled:
            return []

        def _collect_sync() -> List[Dict[str, Any]]:
            threats: List[Dict[str, Any]] = []
            vip_name = vip_profile.get('name', '')
            keywords = vip_profile.get('keywords', [])
            search_terms = [vip_name] + keywords

            for term in search_terms:
                for submission in self.reddit.subreddit('all').search(term, time_filter='day', limit=25):
                    threat_score = self._analyze_content_for_threats(
                        f"{submission.title} {submission.selftext}", vip_name
                    )
                    if threat_score > 0.6:
                        threats.append({
                            'vip_id': vip_profile.get('id'),
                            'vip_name': vip_name,
                            'platform': 'reddit',
                            'threat_type': self._classify_threat_type(f"{submission.title} {submission.selftext}"),
                            'severity': self._calculate_severity(threat_score),
                            'confidence_score': threat_score,
                            'content': f"{submission.title}\n\n{submission.selftext[:500]}",
                            'source_url': f"https://reddit.com{submission.permalink}",
                            'evidence': {
                                'submission_id': submission.id,
                                'subreddit': str(submission.subreddit),
                                'score': submission.score,
                                'num_comments': submission.num_comments,
                                'author': str(submission.author) if submission.author else '[deleted]'
                            }
                        })

                for submission in self.reddit.subreddit('all').hot(limit=10):
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:50]:
                        if any(keyword.lower() in comment.body.lower() for keyword in search_terms):
                            threat_score = self._analyze_content_for_threats(comment.body, vip_name)
                            if threat_score > 0.6:
                                threats.append({
                                    'vip_id': vip_profile.get('id'),
                                    'vip_name': vip_name,
                                    'platform': 'reddit',
                                    'threat_type': self._classify_threat_type(comment.body),
                                    'severity': self._calculate_severity(threat_score),
                                    'confidence_score': threat_score,
                                    'content': comment.body[:500],
                                    'source_url': f"https://reddit.com{comment.permalink}",
                                    'evidence': {
                                        'comment_id': comment.id,
                                        'subreddit': str(submission.subreddit),
                                        'parent_submission': submission.id,
                                        'score': comment.score,
                                        'author': str(comment.author) if comment.author else '[deleted]'
                                    }
                                })
            return threats

        try:
            return await asyncio.to_thread(_collect_sync)
        except Exception as e:
            logger.error(f"Error monitoring Reddit for {vip_profile.get('name')}: {e}")
            return []
        
    def _analyze_content_for_threats(self, content: str, vip_name: str) -> float:
        """Analyze content for threat indicators"""
        if not content:
            return 0.0
            
        content_lower = content.lower()
        vip_lower = vip_name.lower()
        
        # Threat indicators
        threat_keywords = [
            'kill', 'murder', 'assassinate', 'bomb', 'attack', 'hurt', 'harm',
            'stalk', 'follow', 'hunt', 'track', 'expose', 'doxx', 'leak',
            'fake', 'imposter', 'pretend', 'scam', 'fraud', 'lie',
            'hate', 'destroy', 'ruin', 'revenge', 'payback'
        ]
        
        # Context modifiers
        personal_indicators = ['address', 'phone', 'home', 'family', 'children']
        urgency_indicators = ['now', 'today', 'tonight', 'soon', 'immediately']
        
        score = 0.0
        
        # Check if VIP is mentioned
        if vip_lower in content_lower:
            score += 0.3
            
            # Check for threat keywords
            threat_count = sum(1 for keyword in threat_keywords if keyword in content_lower)
            score += min(threat_count * 0.2, 0.6)
            
            # Check for personal information
            personal_count = sum(1 for indicator in personal_indicators if indicator in content_lower)
            score += min(personal_count * 0.15, 0.3)
            
            # Check for urgency
            urgency_count = sum(1 for indicator in urgency_indicators if indicator in content_lower)
            score += min(urgency_count * 0.1, 0.2)
            
        return min(score, 1.0)
        
    def _classify_threat_type(self, content: str) -> str:
        """Classify the type of threat"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['kill', 'murder', 'assassinate', 'bomb', 'attack']):
            return 'physical_threat'
        elif any(word in content_lower for word in ['doxx', 'address', 'phone', 'expose', 'leak']):
            return 'doxxing'
        elif any(word in content_lower for word in ['fake', 'imposter', 'pretend', 'scam']):
            return 'impersonation'
        elif any(word in content_lower for word in ['lie', 'false', 'misinformation']):
            return 'misinformation'
        elif any(word in content_lower for word in ['stalk', 'follow', 'hunt', 'track']):
            return 'stalking'
        else:
            return 'harassment'
            
    def _calculate_severity(self, threat_score: float) -> str:
        """Calculate threat severity based on score"""
        if threat_score >= 0.9:
            return 'critical'
        elif threat_score >= 0.8:
            return 'high'
        elif threat_score >= 0.7:
            return 'medium'
        else:
            return 'low'

class NewsMonitor(BasePlatformMonitor):
    """News monitoring using News API"""
    
    def __init__(self):
        super().__init__("news")
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize News API client"""
        try:
            api_key = os.getenv('NEWS_API_KEY')
            if api_key:
                self.client = NewsApiClient(api_key=api_key)
                self.is_enabled = True
                logger.info("News API monitor initialized successfully")
            else:
                logger.warning("News API key not configured")
        except Exception as e:
            logger.error(f"Failed to initialize News API client: {e}")
            
    def is_api_configured(self) -> bool:
        return self.client is not None
        
    async def monitor_vip(self, vip_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Monitor VIP mentions in news"""
        threats = []
        
        if not self.is_enabled:
            return threats
            
        try:
            vip_name = vip_profile.get('name', '')
            keywords = vip_profile.get('keywords', [])
            
            # Search for recent news mentioning the VIP
            for keyword in [vip_name] + keywords[:3]:  # Limit to avoid API quota
                articles = self.client.get_everything(
                    q=keyword,
                    language='en',
                    sort_by='publishedAt',
                    from_param=datetime.now().strftime('%Y-%m-%d')
                )
                
                for article in articles.get('articles', [])[:10]:  # Limit results
                    content = f"{article.get('title', '')} {article.get('description', '')}"
                    threat_score = self._analyze_news_for_threats(content, vip_name)
                    
                    if threat_score > 0.5:
                        threats.append({
                            'vip_id': vip_profile.get('id'),
                            'vip_name': vip_name,
                            'platform': 'news',
                            'threat_type': self._classify_news_threat(content),
                            'severity': self._calculate_severity(threat_score),
                            'confidence_score': threat_score,
                            'content': content,
                            'source_url': article.get('url', ''),
                            'evidence': {
                                'source': article.get('source', {}).get('name', ''),
                                'published_at': article.get('publishedAt', ''),
                                'author': article.get('author', ''),
                                'url_to_image': article.get('urlToImage', '')
                            }
                        })
                        
        except Exception as e:
            logger.error(f"Error monitoring news for {vip_profile.get('name')}: {e}")
            
        return threats
        
    def _analyze_news_for_threats(self, content: str, vip_name: str) -> float:
        """Analyze news content for threat indicators"""
        if not content:
            return 0.0
            
        content_lower = content.lower()
        vip_lower = vip_name.lower()
        
        # News-specific threat indicators
        threat_keywords = [
            'scandal', 'controversy', 'allegation', 'accused', 'lawsuit',
            'investigation', 'fraud', 'corruption', 'leak', 'exposed',
            'crisis', 'downfall', 'resignation', 'fired', 'stepped down'
        ]
        
        score = 0.0
        
        if vip_lower in content_lower:
            score += 0.2
            
            threat_count = sum(1 for keyword in threat_keywords if keyword in content_lower)
            score += min(threat_count * 0.15, 0.8)
            
        return min(score, 1.0)
        
    def _classify_news_threat(self, content: str) -> str:
        """Classify news threat type"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['scandal', 'controversy', 'allegation']):
            return 'reputation_damage'
        elif any(word in content_lower for word in ['leak', 'exposed', 'revealed']):
            return 'information_leak'
        elif any(word in content_lower for word in ['fraud', 'corruption', 'illegal']):
            return 'legal_threat'
        else:
            return 'misinformation'
            
    def _calculate_severity(self, threat_score: float) -> str:
        """Calculate threat severity"""
        if threat_score >= 0.8:
            return 'high'
        elif threat_score >= 0.6:
            return 'medium'
        else:
            return 'low'

class YouTubeMonitor(BasePlatformMonitor):
    """YouTube monitoring using YouTube Data API"""
    
    def __init__(self):
        super().__init__("youtube")
        self.service = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize YouTube API client"""
        try:
            api_key = os.getenv('YOUTUBE_API_KEY')
            if api_key:
                self.service = build('youtube', 'v3', developerKey=api_key)
                self.is_enabled = True
                logger.info("YouTube monitor initialized successfully")
            else:
                logger.warning("YouTube API key not configured")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {e}")
            
    def is_api_configured(self) -> bool:
        return self.service is not None
        
    async def monitor_vip(self, vip_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Monitor VIP mentions on YouTube"""
        threats = []
        
        if not self.is_enabled:
            return threats
            
        try:
            vip_name = vip_profile.get('name', '')
            keywords = vip_profile.get('keywords', [])
            
            # Search for recent videos mentioning the VIP
            for keyword in [vip_name] + keywords[:2]:
                search_response = self.service.search().list(
                    q=keyword,
                    part='id,snippet',
                    maxResults=25,
                    order='date',
                    type='video',
                    publishedAfter=datetime.now().strftime('%Y-%m-%dT00:00:00Z')
                ).execute()
                
                for search_result in search_response.get('items', []):
                    video_title = search_result['snippet']['title']
                    video_description = search_result['snippet']['description']
                    content = f"{video_title} {video_description}"
                    
                    threat_score = self._analyze_video_for_threats(content, vip_name)
                    
                    if threat_score > 0.5:
                        video_id = search_result['id']['videoId']
                        threats.append({
                            'vip_id': vip_profile.get('id'),
                            'vip_name': vip_name,
                            'platform': 'youtube',
                            'threat_type': self._classify_video_threat(content),
                            'severity': self._calculate_severity(threat_score),
                            'confidence_score': threat_score,
                            'content': content[:500],
                            'source_url': f"https://www.youtube.com/watch?v={video_id}",
                            'evidence': {
                                'video_id': video_id,
                                'channel_title': search_result['snippet']['channelTitle'],
                                'channel_id': search_result['snippet']['channelId'],
                                'published_at': search_result['snippet']['publishedAt'],
                                'thumbnail': search_result['snippet']['thumbnails']['default']['url']
                            }
                        })
                        
        except Exception as e:
            logger.error(f"Error monitoring YouTube for {vip_profile.get('name')}: {e}")
            
        return threats
        
    def _analyze_video_for_threats(self, content: str, vip_name: str) -> float:
        """Analyze video content for threats"""
        if not content:
            return 0.0
            
        content_lower = content.lower()
        vip_lower = vip_name.lower()
        
        threat_keywords = [
            'exposed', 'truth', 'scandal', 'controversy', 'fake', 'lie',
            'scam', 'fraud', 'reveal', 'secret', 'conspiracy', 'leaked'
        ]
        
        score = 0.0
        
        if vip_lower in content_lower:
            score += 0.3
            
            threat_count = sum(1 for keyword in threat_keywords if keyword in content_lower)
            score += min(threat_count * 0.15, 0.7)
            
        return min(score, 1.0)
        
    def _classify_video_threat(self, content: str) -> str:
        """Classify video threat type"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['exposed', 'reveal', 'truth', 'leaked']):
            return 'information_exposure'
        elif any(word in content_lower for word in ['fake', 'scam', 'fraud']):
            return 'misinformation'
        elif any(word in content_lower for word in ['scandal', 'controversy']):
            return 'reputation_damage'
        else:
            return 'defamation'
            
    def _calculate_severity(self, threat_score: float) -> str:
        """Calculate threat severity"""
        if threat_score >= 0.8:
            return 'high'
        elif threat_score >= 0.6:
            return 'medium'
        else:
            return 'low'

class PastebinMonitor(BasePlatformMonitor):
    """Pastebin monitoring via scraping recent pastes (no API key)."""
    def __init__(self):
        super().__init__("pastebin")
        # Enabled by default; can be disabled via env
        self.is_enabled = os.getenv('ENABLE_PASTEBIN', 'true').lower() == 'true'

    def is_api_configured(self) -> bool:
        return True

    async def monitor_vip(self, vip_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.is_enabled:
            return []

        vip_name = vip_profile.get('name', '')
        keywords = [vip_name] + vip_profile.get('keywords', [])

        async def _fetch(url: str) -> Optional[str]:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Protego/1.0'
                }
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url, timeout=15) as resp:
                        if resp.status == 200:
                            return await resp.text()
                        return None
            except Exception as e:
                logger.warning(f"Pastebin fetch failed for {url}: {e}")
                return None

        threats: List[Dict[str, Any]] = []
        try:
            archive_html = await _fetch('https://pastebin.com/archive')
            if not archive_html:
                return []
            soup = BeautifulSoup(archive_html, 'html.parser')
            rows = soup.select('table.maintable tr')
            paste_paths: List[str] = []
            for row in rows[1:15]:  # first 14 recent items
                link = row.find('a')
                if link and link.get('href', '').startswith('/'):
                    paste_paths.append(link['href'])

            for path in paste_paths:
                paste_html = await _fetch(f'https://pastebin.com{path}')
                if not paste_html:
                    continue
                psoup = BeautifulSoup(paste_html, 'html.parser')
                content_el = psoup.find('textarea', { 'class': 'textarea' })
                content_text = content_el.text if content_el else psoup.get_text("\n")
                lower = content_text.lower()
                if any(k.lower() in lower for k in keywords if k):
                    score = 0.6
                    if any(w in lower for w in ['doxx','address','phone','leak','expose']):
                        score = 0.8
                    threats.append({
                        'vip_id': vip_profile.get('id'),
                        'vip_name': vip_name,
                        'platform': 'pastebin',
                        'threat_type': 'misinformation' if 'fake' in lower or 'lie' in lower else 'information_leak',
                        'severity': 'high' if score >= 0.8 else 'medium',
                        'confidence_score': score,
                        'content': content_text[:1000],
                        'source_url': f'https://pastebin.com{path}',
                        'evidence': {
                            'paste_path': path,
                            'snippet': content_text[:200]
                        }
                    })
        except Exception as e:
            logger.error(f"Error monitoring Pastebin for {vip_profile.get('name')}: {e}")

        return threats

# Initialize all monitors
def get_all_monitors() -> List[BasePlatformMonitor]:
    """Get all available platform monitors"""
    monitors: List[BasePlatformMonitor] = [
        RedditMonitor(),
        NewsMonitor(),
        YouTubeMonitor(),
        PastebinMonitor()
    ]
    return monitors

def get_active_monitors() -> List[BasePlatformMonitor]:
    """Get only active/configured monitors"""
    return [monitor for monitor in get_all_monitors() if monitor.is_enabled]
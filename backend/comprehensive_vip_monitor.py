#!/usr/bin/env python3
"""
Comprehensive VIP Monitoring System
Multi-source threat detection, impersonation identification, and evidence collection
"""

import asyncio
import aiohttp
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import base64
import os

@dataclass
class VIPProfile:
    """VIP profile with monitoring parameters"""
    name: str
    aliases: List[str]
    official_accounts: Dict[str, str]  # platform -> username
    keywords: List[str]
    image_hashes: List[str]  # Known image fingerprints
    protection_level: str  # high, medium, low
    
@dataclass
class ThreatDetection:
    """Detected threat with evidence"""
    id: str
    vip_name: str
    threat_type: str  # impersonation, misinformation, data_leak, fake_campaign
    platform: str
    source_url: str
    content: str
    confidence_score: float
    severity: str  # critical, high, medium, low
    evidence: Dict[str, Any]
    timestamp: datetime
    cluster_id: Optional[str] = None

class MultiSourceMonitor:
    """Multi-platform monitoring system"""
    
    def __init__(self):
        self.vip_profiles: Dict[str, VIPProfile] = {}
        self.active_monitors: Set[str] = set()
        self.threat_patterns = self._load_threat_patterns()
        self.session: Optional[aiohttp.ClientSession] = None
        
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat detection patterns"""
        return {
            "impersonation": [
                r"official\s+account",
                r"verified\s+profile", 
                r"real\s+{vip_name}",
                r"{vip_name}\s+official",
                r"authentic\s+{vip_name}"
            ],
            "misinformation": [
                r"{vip_name}\s+caught",
                r"{vip_name}\s+scandal",
                r"{vip_name}\s+leaked",
                r"breaking.*{vip_name}",
                r"{vip_name}.*conspiracy"
            ],
            "data_leak": [
                r"{vip_name}.*password",
                r"{vip_name}.*private",
                r"{vip_name}.*confidential",
                r"leaked.*{vip_name}",
                r"{vip_name}.*documents"
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def add_vip(self, profile: VIPProfile):
        """Add VIP profile for monitoring"""
        self.vip_profiles[profile.name] = profile
        
    async def monitor_social_media(self, vip_name: str) -> List[ThreatDetection]:
        """Monitor social media platforms for VIP mentions"""
        threats = []
        vip = self.vip_profiles.get(vip_name)
        if not vip:
            return threats
            
        platforms = {
            "twitter": self._monitor_twitter,
            "facebook": self._monitor_facebook,
            "instagram": self._monitor_instagram,
            "linkedin": self._monitor_linkedin,
            "telegram": self._monitor_telegram
        }
        
        for platform, monitor_func in platforms.items():
            try:
                platform_threats = await monitor_func(vip)
                threats.extend(platform_threats)
            except Exception as e:
                print(f"Error monitoring {platform} for {vip_name}: {e}")
                
        return threats
    
    async def _monitor_twitter(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor Twitter/X for VIP threats"""
        threats = []
        
        # Simulate Twitter API calls (replace with real API)
        mock_tweets = [
            {
                "id": "1234567890",
                "text": f"BREAKING: {vip.name} caught in major scandal with leaked documents",
                "user": {"screen_name": f"real_{vip.name.lower()}", "verified": False},
                "url": "https://twitter.com/fake_account/status/1234567890",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "1234567891", 
                "text": f"Official statement from {vip.name} regarding recent events",
                "user": {"screen_name": f"{vip.name.lower()}_official", "verified": False},
                "url": "https://twitter.com/impersonator/status/1234567891",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        for tweet in mock_tweets:
            threat = await self._analyze_content(
                content=tweet["text"],
                platform="twitter",
                source_url=tweet["url"],
                vip=vip,
                metadata=tweet
            )
            if threat:
                threats.append(threat)
                
        return threats
    
    async def _monitor_facebook(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor Facebook for VIP threats"""
        threats = []
        
        # Mock Facebook posts
        mock_posts = [
            {
                "id": "fb_123456",
                "message": f"URGENT: {vip.name} threatens to destroy economy if demands not met",
                "from": {"name": f"{vip.name} Official Page", "id": "fake_page_id"},
                "link": "https://facebook.com/fake_page/posts/123456",
                "created_time": datetime.now().isoformat()
            }
        ]
        
        for post in mock_posts:
            threat = await self._analyze_content(
                content=post.get("message", ""),
                platform="facebook", 
                source_url=post["link"],
                vip=vip,
                metadata=post
            )
            if threat:
                threats.append(threat)
                
        return threats
    
    async def _monitor_instagram(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor Instagram for VIP threats"""
        # Similar implementation for Instagram
        return []
    
    async def _monitor_linkedin(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor LinkedIn for VIP threats"""
        # Similar implementation for LinkedIn
        return []
    
    async def _monitor_telegram(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor Telegram channels for VIP threats"""
        threats = []
        
        # Mock Telegram messages
        mock_messages = [
            {
                "message_id": 12345,
                "text": f"Leaked: {vip.name} private conversations reveal shocking truth",
                "chat": {"title": "VIP Leaks Channel", "username": "vip_leaks"},
                "date": datetime.now().timestamp()
            }
        ]
        
        for msg in mock_messages:
            threat = await self._analyze_content(
                content=msg.get("text", ""),
                platform="telegram",
                source_url=f"https://t.me/{msg['chat'].get('username', 'unknown')}/{msg['message_id']}",
                vip=vip,
                metadata=msg
            )
            if threat:
                threats.append(threat)
                
        return threats
    
    async def monitor_data_leak_platforms(self, vip_name: str) -> List[ThreatDetection]:
        """Monitor data leak and code sharing platforms"""
        threats = []
        vip = self.vip_profiles.get(vip_name)
        if not vip:
            return threats
            
        platforms = {
            "pastebin": self._monitor_pastebin,
            "github": self._monitor_github,
            "forums": self._monitor_forums
        }
        
        for platform, monitor_func in platforms.items():
            try:
                platform_threats = await monitor_func(vip)
                threats.extend(platform_threats)
            except Exception as e:
                print(f"Error monitoring {platform} for {vip_name}: {e}")
                
        return threats
    
    async def _monitor_pastebin(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor Pastebin for VIP data leaks"""
        threats = []
        
        # Mock Pastebin entries
        mock_pastes = [
            {
                "key": "abc123def",
                "title": f"{vip.name} Private Data Dump",
                "raw": f"Username: {vip.name.lower()}\nPassword: leaked_password_123\nPrivate info...",
                "url": "https://pastebin.com/abc123def",
                "date": datetime.now().isoformat()
            }
        ]
        
        for paste in mock_pastes:
            threat = await self._analyze_content(
                content=paste["raw"],
                platform="pastebin",
                source_url=paste["url"],
                vip=vip,
                metadata=paste
            )
            if threat:
                threat.threat_type = "data_leak"
                threats.append(threat)
                
        return threats
    
    async def _monitor_github(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor GitHub for VIP-related leaks"""
        # Similar implementation for GitHub
        return []
    
    async def _monitor_forums(self, vip: VIPProfile) -> List[ThreatDetection]:
        """Monitor forums for VIP discussions"""
        # Similar implementation for forums
        return []
    
    async def _analyze_content(self, content: str, platform: str, source_url: str, 
                             vip: VIPProfile, metadata: Dict) -> Optional[ThreatDetection]:
        """Analyze content for threats"""
        if not content:
            return None
            
        # Check for VIP mentions
        vip_mentioned = any(
            name.lower() in content.lower() 
            for name in [vip.name] + vip.aliases
        )
        
        if not vip_mentioned:
            return None
        
        # Detect threat type and calculate confidence
        threat_type, confidence = self._classify_threat(content, vip, metadata)
        
        if confidence < 0.3:  # Threshold for threat detection
            return None
        
        # Determine severity
        severity = self._calculate_severity(threat_type, confidence, platform)
        
        # Collect evidence
        evidence = await self._collect_evidence(content, platform, source_url, metadata)
        
        # Generate threat ID
        threat_id = hashlib.md5(f"{vip.name}_{source_url}_{content[:100]}".encode()).hexdigest()
        
        return ThreatDetection(
            id=threat_id,
            vip_name=vip.name,
            threat_type=threat_type,
            platform=platform,
            source_url=source_url,
            content=content[:500],  # Truncate for storage
            confidence_score=confidence,
            severity=severity,
            evidence=evidence,
            timestamp=datetime.now()
        )
    
    def _classify_threat(self, content: str, vip: VIPProfile, metadata: Dict) -> tuple[str, float]:
        """Classify threat type and calculate confidence"""
        content_lower = content.lower()
        vip_name_lower = vip.name.lower()
        
        # Check for impersonation
        if self._is_impersonation(content, vip, metadata):
            return "impersonation", 0.8
        
        # Check for misinformation patterns
        misinformation_score = 0
        for pattern in self.threat_patterns["misinformation"]:
            pattern_filled = pattern.format(vip_name=vip_name_lower)
            if re.search(pattern_filled, content_lower):
                misinformation_score += 0.2
        
        if misinformation_score >= 0.4:
            return "misinformation", min(misinformation_score, 0.95)
        
        # Check for data leak patterns
        data_leak_score = 0
        for pattern in self.threat_patterns["data_leak"]:
            pattern_filled = pattern.format(vip_name=vip_name_lower)
            if re.search(pattern_filled, content_lower):
                data_leak_score += 0.3
        
        if data_leak_score >= 0.3:
            return "data_leak", min(data_leak_score, 0.9)
        
        # Default to general threat
        return "general_threat", 0.5
    
    def _is_impersonation(self, content: str, vip: VIPProfile, metadata: Dict) -> bool:
        """Detect impersonation attempts"""
        # Check username/profile name
        username = metadata.get("user", {}).get("screen_name", "")
        profile_name = metadata.get("from", {}).get("name", "")
        
        vip_name_variations = [
            vip.name.lower(),
            vip.name.lower().replace(" ", "_"),
            vip.name.lower().replace(" ", ""),
            f"real_{vip.name.lower()}",
            f"{vip.name.lower()}_official"
        ]
        
        # Check if username matches VIP but isn't verified
        is_verified = metadata.get("user", {}).get("verified", False)
        username_matches = any(var in username.lower() for var in vip_name_variations)
        
        if username_matches and not is_verified:
            # Check if it's actually an official account
            official_accounts = vip.official_accounts.values()
            if username not in official_accounts:
                return True
        
        # Check for impersonation keywords in content
        impersonation_patterns = [
            "i am the real",
            "official account", 
            "verified profile",
            "authentic"
        ]
        
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in impersonation_patterns)
    
    def _calculate_severity(self, threat_type: str, confidence: float, platform: str) -> str:
        """Calculate threat severity"""
        base_severity = {
            "impersonation": 0.7,
            "misinformation": 0.6,
            "data_leak": 0.9,
            "general_threat": 0.4
        }.get(threat_type, 0.4)
        
        platform_multiplier = {
            "twitter": 1.2,
            "facebook": 1.1,
            "telegram": 1.3,
            "pastebin": 1.4,
            "github": 1.2
        }.get(platform, 1.0)
        
        final_score = base_severity * confidence * platform_multiplier
        
        if final_score >= 0.8:
            return "critical"
        elif final_score >= 0.6:
            return "high"
        elif final_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    async def _collect_evidence(self, content: str, platform: str, source_url: str, 
                               metadata: Dict) -> Dict[str, Any]:
        """Collect evidence for the threat"""
        evidence = {
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "platform": platform,
            "source_url": source_url,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        # Add platform-specific evidence
        if platform == "twitter":
            evidence.update({
                "user_verified": metadata.get("user", {}).get("verified", False),
                "user_followers": metadata.get("user", {}).get("followers_count", 0),
                "retweet_count": metadata.get("retweet_count", 0)
            })
        elif platform == "facebook":
            evidence.update({
                "page_verified": metadata.get("from", {}).get("verified", False),
                "post_type": metadata.get("type", "status")
            })
        
        # Generate screenshot URL (mock)
        evidence["screenshot_url"] = f"https://screenshots.protego.com/{hashlib.md5(source_url.encode()).hexdigest()}.png"
        
        return evidence

class CampaignDetector:
    """Detect coordinated misinformation campaigns"""
    
    def __init__(self):
        self.threat_clusters: Dict[str, List[ThreatDetection]] = {}
        
    def analyze_campaign_patterns(self, threats: List[ThreatDetection]) -> Dict[str, List[ThreatDetection]]:
        """Analyze threats for coordinated campaign patterns"""
        campaigns = {}
        
        # Group by content similarity
        content_groups = self._group_by_content_similarity(threats)
        
        # Group by temporal patterns
        temporal_groups = self._group_by_temporal_patterns(threats)
        
        # Combine groupings to identify campaigns
        for group_id, group_threats in content_groups.items():
            if len(group_threats) >= 3:  # Minimum threshold for campaign
                campaign_id = f"campaign_{group_id}"
                campaigns[campaign_id] = group_threats
                
                # Update threats with cluster ID
                for threat in group_threats:
                    threat.cluster_id = campaign_id
        
        return campaigns
    
    def _group_by_content_similarity(self, threats: List[ThreatDetection]) -> Dict[str, List[ThreatDetection]]:
        """Group threats by content similarity"""
        groups = {}
        
        for threat in threats:
            # Simple similarity based on common words
            content_words = set(threat.content.lower().split())
            
            # Find similar existing groups
            best_group = None
            best_similarity = 0
            
            for group_id, group_threats in groups.items():
                for existing_threat in group_threats:
                    existing_words = set(existing_threat.content.lower().split())
                    similarity = len(content_words & existing_words) / len(content_words | existing_words)
                    
                    if similarity > best_similarity and similarity > 0.3:
                        best_similarity = similarity
                        best_group = group_id
            
            if best_group:
                groups[best_group].append(threat)
            else:
                # Create new group
                group_id = f"content_group_{len(groups)}"
                groups[group_id] = [threat]
        
        return groups
    
    def _group_by_temporal_patterns(self, threats: List[ThreatDetection]) -> Dict[str, List[ThreatDetection]]:
        """Group threats by temporal patterns"""
        # Sort threats by timestamp
        sorted_threats = sorted(threats, key=lambda t: t.timestamp)
        
        groups = {}
        current_group = []
        group_id = 0
        
        for i, threat in enumerate(sorted_threats):
            if not current_group:
                current_group.append(threat)
                continue
            
            # Check if threat is within time window of current group
            time_diff = (threat.timestamp - current_group[-1].timestamp).total_seconds()
            
            if time_diff <= 3600:  # 1 hour window
                current_group.append(threat)
            else:
                # Save current group and start new one
                if len(current_group) >= 2:
                    groups[f"temporal_group_{group_id}"] = current_group.copy()
                    group_id += 1
                current_group = [threat]
        
        # Don't forget the last group
        if len(current_group) >= 2:
            groups[f"temporal_group_{group_id}"] = current_group
        
        return groups

# Example usage and demo
async def demo_comprehensive_monitoring():
    """Demonstrate comprehensive VIP monitoring"""
    print("🎯 COMPREHENSIVE VIP MONITORING SYSTEM DEMO")
    print("=" * 60)
    
    # Create VIP profiles
    vip_profiles = [
        VIPProfile(
            name="John Politician",
            aliases=["JP", "Senator John"],
            official_accounts={
                "twitter": "@john_politician_official",
                "facebook": "john.politician.official"
            },
            keywords=["john politician", "senator john", "jp"],
            image_hashes=["hash1", "hash2"],
            protection_level="high"
        ),
        VIPProfile(
            name="Jane Celebrity",
            aliases=["JC", "Jane C"],
            official_accounts={
                "instagram": "@jane_celebrity_real",
                "twitter": "@jane_celebrity"
            },
            keywords=["jane celebrity", "jane c", "jc"],
            image_hashes=["hash3", "hash4"],
            protection_level="medium"
        )
    ]
    
    async with MultiSourceMonitor() as monitor:
        # Add VIP profiles
        for profile in vip_profiles:
            monitor.add_vip(profile)
        
        print(f"\n📋 Monitoring {len(vip_profiles)} VIPs across multiple platforms")
        
        all_threats = []
        
        # Monitor each VIP
        for profile in vip_profiles:
            print(f"\n🔍 Monitoring {profile.name}...")
            
            # Social media monitoring
            social_threats = await monitor.monitor_social_media(profile.name)
            print(f"   📱 Social Media: {len(social_threats)} threats detected")
            
            # Data leak monitoring
            leak_threats = await monitor.monitor_data_leak_platforms(profile.name)
            print(f"   💾 Data Leaks: {len(leak_threats)} threats detected")
            
            all_threats.extend(social_threats + leak_threats)
        
        print(f"\n📊 TOTAL THREATS DETECTED: {len(all_threats)}")
        
        # Campaign analysis
        campaign_detector = CampaignDetector()
        campaigns = campaign_detector.analyze_campaign_patterns(all_threats)
        
        print(f"🕸️ COORDINATED CAMPAIGNS: {len(campaigns)}")
        
        # Display results
        print("\n" + "="*60)
        print("THREAT ANALYSIS RESULTS")
        print("="*60)
        
        for threat in all_threats:
            print(f"\n🚨 {threat.severity.upper()} THREAT")
            print(f"   VIP: {threat.vip_name}")
            print(f"   Type: {threat.threat_type}")
            print(f"   Platform: {threat.platform}")
            print(f"   Confidence: {threat.confidence_score:.2f}")
            print(f"   Content: {threat.content[:100]}...")
            print(f"   Source: {threat.source_url}")
            if threat.cluster_id:
                print(f"   Campaign: {threat.cluster_id}")
        
        print(f"\n🎉 COMPREHENSIVE MONITORING COMPLETE!")
        return all_threats

if __name__ == "__main__":
    asyncio.run(demo_comprehensive_monitoring())

#!/usr/bin/env python3
"""
Phase 1: Fake Profile Detection
Detects impersonation attempts using string similarity and profile analysis
"""

import os
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)

class FakeProfileDetector:
    """Detects fake profiles impersonating VIPs"""
    
    def __init__(self, db_path: str = "backend/monitoring/vip_profiles.db"):
        self.db_path = db_path
        self._init_database()
        self.similarity_threshold = 0.8  # Levenshtein similarity threshold
        self.recent_account_days = 30  # Consider accounts created within 30 days as "recent"
    
    def _init_database(self):
        """Initialize VIP profiles database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Official VIP profiles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS official_vip_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vip_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        username TEXT NOT NULL,
                        display_name TEXT,
                        profile_url TEXT,
                        profile_image_url TEXT,
                        verified BOOLEAN DEFAULT FALSE,
                        follower_count INTEGER,
                        created_date TEXT,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, username)
                    )
                """)
                
                # Detected fake profiles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detected_fake_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suspicious_username TEXT NOT NULL,
                        suspicious_display_name TEXT,
                        platform TEXT NOT NULL,
                        profile_url TEXT,
                        profile_image_url TEXT,
                        impersonated_vip TEXT,
                        similarity_score REAL,
                        risk_factors TEXT,
                        follower_count INTEGER,
                        account_age_days INTEGER,
                        detection_reason TEXT,
                        confidence_score REAL,
                        status TEXT DEFAULT 'pending',
                        detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        verified_at TEXT,
                        verified_by TEXT
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vip_platform ON official_vip_profiles (vip_name, platform)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_fake_username ON detected_fake_profiles (suspicious_username)")
                
                conn.commit()
                logger.info("VIP profiles database initialized")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def add_official_vip_profile(self, vip_name: str, platform: str, username: str, 
                                display_name: str = None, **kwargs) -> bool:
        """Add official VIP profile to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO official_vip_profiles 
                    (vip_name, platform, username, display_name, profile_url, 
                     profile_image_url, verified, follower_count, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vip_name,
                    platform,
                    username,
                    display_name,
                    kwargs.get('profile_url'),
                    kwargs.get('profile_image_url'),
                    kwargs.get('verified', False),
                    kwargs.get('follower_count', 0),
                    kwargs.get('created_date')
                ))
                
                conn.commit()
                logger.info(f"Added official VIP profile: {username} on {platform}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add VIP profile: {e}")
            return False
    
    def get_official_profiles(self, vip_name: str = None, platform: str = None) -> List[Dict]:
        """Get official VIP profiles"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM official_vip_profiles WHERE 1=1"
                params = []
                
                if vip_name:
                    query += " AND vip_name = ?"
                    params.append(vip_name)
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get official profiles: {e}")
            return []
    
    def calculate_username_similarity(self, username1: str, username2: str) -> float:
        """Calculate similarity between usernames using multiple methods"""
        # Normalize usernames
        u1 = username1.lower().strip()
        u2 = username2.lower().strip()
        
        # Exact match
        if u1 == u2:
            return 1.0
        
        # Sequence matcher similarity
        seq_similarity = SequenceMatcher(None, u1, u2).ratio()
        
        # Character-based similarity (ignoring common variations)
        u1_clean = re.sub(r'[._\-0-9]', '', u1)
        u2_clean = re.sub(r'[._\-0-9]', '', u2)
        clean_similarity = SequenceMatcher(None, u1_clean, u2_clean).ratio()
        
        # Substring similarity
        substring_similarity = 0.0
        if len(u1_clean) > 3 and len(u2_clean) > 3:
            if u1_clean in u2_clean or u2_clean in u1_clean:
                substring_similarity = 0.8
        
        # Return highest similarity
        return max(seq_similarity, clean_similarity, substring_similarity)
    
    def detect_suspicious_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if a profile is suspicious impersonation"""
        username = profile_data.get('username', '')
        display_name = profile_data.get('display_name', '')
        platform = profile_data.get('platform', '')
        follower_count = profile_data.get('follower_count', 0)
        account_created = profile_data.get('created_date')
        
        # Get all official profiles for comparison
        official_profiles = self.get_official_profiles(platform=platform)
        
        detection_result = {
            "is_suspicious": False,
            "impersonated_vip": None,
            "similarity_score": 0.0,
            "risk_factors": [],
            "confidence_score": 0.0,
            "detection_reasons": []
        }
        
        max_similarity = 0.0
        best_match_vip = None
        
        # Check against all official profiles
        for official in official_profiles:
            # Username similarity
            username_sim = self.calculate_username_similarity(username, official['username'])
            
            # Display name similarity
            display_sim = 0.0
            if display_name and official['display_name']:
                display_sim = self.calculate_username_similarity(display_name, official['display_name'])
            
            # Take highest similarity
            overall_sim = max(username_sim, display_sim)
            
            if overall_sim > max_similarity:
                max_similarity = overall_sim
                best_match_vip = official['vip_name']
        
        detection_result["similarity_score"] = max_similarity
        detection_result["impersonated_vip"] = best_match_vip
        
        # Risk factor analysis
        risk_factors = []
        risk_score = 0.0
        
        # High username similarity
        if max_similarity > self.similarity_threshold:
            risk_factors.append(f"High username similarity ({max_similarity:.2f})")
            risk_score += 0.4
            detection_result["detection_reasons"].append("Similar username to official VIP account")
        
        # Low follower count
        if follower_count < 1000:
            risk_factors.append(f"Low follower count ({follower_count})")
            risk_score += 0.2
        
        # Recent account creation
        if account_created:
            try:
                created_date = datetime.fromisoformat(account_created.replace('Z', '+00:00'))
                account_age = (datetime.now() - created_date).days
                
                if account_age < self.recent_account_days:
                    risk_factors.append(f"Recent account creation ({account_age} days)")
                    risk_score += 0.3
                    detection_result["detection_reasons"].append("Recently created account")
            except:
                pass
        
        # Unverified account (if verification status available)
        if not profile_data.get('verified', False):
            risk_factors.append("Unverified account")
            risk_score += 0.1
        
        detection_result["risk_factors"] = risk_factors
        detection_result["confidence_score"] = min(risk_score, 1.0)
        
        # Determine if suspicious
        if max_similarity > self.similarity_threshold and risk_score > 0.5:
            detection_result["is_suspicious"] = True
        
        return detection_result
    
    def save_suspicious_profile(self, profile_data: Dict[str, Any], 
                               detection_result: Dict[str, Any]) -> Optional[int]:
        """Save detected suspicious profile to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate account age
                account_age_days = None
                if profile_data.get('created_date'):
                    try:
                        created_date = datetime.fromisoformat(profile_data['created_date'].replace('Z', '+00:00'))
                        account_age_days = (datetime.now() - created_date).days
                    except:
                        pass
                
                cursor.execute("""
                    INSERT INTO detected_fake_profiles 
                    (suspicious_username, suspicious_display_name, platform, profile_url,
                     profile_image_url, impersonated_vip, similarity_score, risk_factors,
                     follower_count, account_age_days, detection_reason, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile_data.get('username'),
                    profile_data.get('display_name'),
                    profile_data.get('platform'),
                    profile_data.get('profile_url'),
                    profile_data.get('profile_image_url'),
                    detection_result.get('impersonated_vip'),
                    detection_result.get('similarity_score'),
                    '; '.join(detection_result.get('risk_factors', [])),
                    profile_data.get('follower_count'),
                    account_age_days,
                    '; '.join(detection_result.get('detection_reasons', [])),
                    detection_result.get('confidence_score')
                ))
                
                profile_id = cursor.lastrowid
                conn.commit()
                
                logger.warning(f"Suspicious profile detected: {profile_data.get('username')} (ID: {profile_id})")
                return profile_id
                
        except Exception as e:
            logger.error(f"Failed to save suspicious profile: {e}")
            return None
    
    def get_suspicious_profiles(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get detected suspicious profiles"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM detected_fake_profiles"
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                
                query += " ORDER BY detected_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get suspicious profiles: {e}")
            return []
    
    def verify_profile(self, profile_id: int, is_fake: bool, verified_by: str) -> bool:
        """Mark a suspicious profile as verified fake or legitimate"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                status = "confirmed_fake" if is_fake else "legitimate"
                
                cursor.execute("""
                    UPDATE detected_fake_profiles 
                    SET status = ?, verified_at = ?, verified_by = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), verified_by, profile_id))
                
                conn.commit()
                logger.info(f"Profile {profile_id} verified as {status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify profile: {e}")
            return False

# Global detector instance
_profile_detector = None

def get_fake_profile_detector() -> FakeProfileDetector:
    """Get global fake profile detector instance"""
    global _profile_detector
    if _profile_detector is None:
        _profile_detector = FakeProfileDetector()
    return _profile_detector

def detect_fake_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for fake profile detection
    
    Args:
        profile_data: Profile information dictionary
        
    Returns:
        Detection results
    """
    detector = get_fake_profile_detector()
    return detector.detect_suspicious_profile(profile_data)

def setup_official_vip_profiles():
    """Setup some example official VIP profiles"""
    detector = get_fake_profile_detector()
    
    # Example VIP profiles (replace with real ones)
    official_profiles = [
        {
            "vip_name": "President Biden",
            "platform": "twitter",
            "username": "POTUS",
            "display_name": "President Biden",
            "verified": True,
            "follower_count": 32000000
        },
        {
            "vip_name": "Elon Musk",
            "platform": "twitter", 
            "username": "elonmusk",
            "display_name": "Elon Musk",
            "verified": True,
            "follower_count": 150000000
        }
    ]
    
    for profile in official_profiles:
        detector.add_official_vip_profile(**profile)

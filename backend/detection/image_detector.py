#!/usr/bin/env python3
"""
Phase 1: Image Detection
Reverse image search and VIP image verification
"""

import os
import logging
import sqlite3
import hashlib
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class ImageDetector:
    """Detects reused/manipulated images and maintains VIP image database"""
    
    def __init__(self, db_path: str = "backend/monitoring/vip_images.db"):
        self.db_path = db_path
        self.bing_api_key = os.getenv("BING_SEARCH_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cx = os.getenv("GOOGLE_SEARCH_CX")
        self._init_database()
    
    def _init_database(self):
        """Initialize VIP images database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Official VIP images table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS official_vip_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vip_name TEXT NOT NULL,
                        image_url TEXT NOT NULL,
                        image_hash TEXT UNIQUE,
                        image_type TEXT,
                        description TEXT,
                        source_url TEXT,
                        verified BOOLEAN DEFAULT TRUE,
                        added_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Suspicious images table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suspicious_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_url TEXT NOT NULL,
                        image_hash TEXT,
                        post_url TEXT,
                        platform TEXT,
                        username TEXT,
                        matched_vip_image_id INTEGER,
                        similarity_score REAL,
                        reverse_search_results TEXT,
                        detection_reason TEXT,
                        risk_score REAL,
                        status TEXT DEFAULT 'pending',
                        detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (matched_vip_image_id) REFERENCES official_vip_images (id)
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_hash ON official_vip_images (image_hash)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_suspicious_hash ON suspicious_images (image_hash)")
                
                conn.commit()
                logger.info("VIP images database initialized")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate perceptual hash of image"""
        try:
            # Simple MD5 hash for now - in production use perceptual hashing
            return hashlib.md5(image_data).hexdigest()
        except Exception as e:
            logger.error(f"Image hashing failed: {e}")
            return ""
    
    def add_official_vip_image(self, vip_name: str, image_url: str, 
                              image_type: str = "profile", **kwargs) -> bool:
        """Add official VIP image to database"""
        try:
            # Download and hash image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to download image: {image_url}")
                return False
            
            image_hash = self.calculate_image_hash(response.content)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO official_vip_images 
                    (vip_name, image_url, image_hash, image_type, description, source_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    vip_name,
                    image_url,
                    image_hash,
                    image_type,
                    kwargs.get('description'),
                    kwargs.get('source_url')
                ))
                
                conn.commit()
                logger.info(f"Added official VIP image: {vip_name} - {image_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add VIP image: {e}")
            return False
    
    def check_against_official_images(self, image_url: str) -> Dict[str, Any]:
        """Check if image matches any official VIP images"""
        try:
            # Download and hash the suspicious image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return {"error": "Failed to download image"}
            
            suspicious_hash = self.calculate_image_hash(response.content)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check for exact hash match
                cursor.execute("""
                    SELECT * FROM official_vip_images 
                    WHERE image_hash = ?
                """, (suspicious_hash,))
                
                exact_match = cursor.fetchone()
                
                if exact_match:
                    columns = [desc[0] for desc in cursor.description]
                    match_data = dict(zip(columns, exact_match))
                    
                    return {
                        "is_match": True,
                        "match_type": "exact",
                        "similarity_score": 1.0,
                        "matched_vip": match_data["vip_name"],
                        "matched_image": match_data,
                        "risk_level": "high"
                    }
                
                # TODO: Implement perceptual hashing for similar images
                return {
                    "is_match": False,
                    "match_type": "none",
                    "similarity_score": 0.0,
                    "risk_level": "low"
                }
                
        except Exception as e:
            logger.error(f"Official image check failed: {e}")
            return {"error": str(e)}
    
    def reverse_image_search_bing(self, image_url: str) -> Dict[str, Any]:
        """Perform reverse image search using Bing API"""
        if not self.bing_api_key:
            return {"error": "Bing API key not configured"}
        
        try:
            endpoint = "https://api.bing.microsoft.com/v7.0/images/visualsearch"
            
            headers = {
                "Ocp-Apim-Subscription-Key": self.bing_api_key,
                "Content-Type": "application/json"
            }
            
            # Prepare image data
            image_response = requests.get(image_url, timeout=10)
            if image_response.status_code != 200:
                return {"error": "Failed to download image for search"}
            
            image_data = base64.b64encode(image_response.content).decode()
            
            data = {
                "imageInfo": {
                    "url": image_url
                }
            }
            
            response = requests.post(endpoint, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                results = response.json()
                
                # Extract relevant information
                similar_images = []
                if "tags" in results:
                    for tag in results["tags"]:
                        if "actions" in tag:
                            for action in tag["actions"]:
                                if action.get("actionType") == "VisualSearch":
                                    data_items = action.get("data", {}).get("value", [])
                                    for item in data_items[:10]:  # Limit results
                                        similar_images.append({
                                            "url": item.get("contentUrl"),
                                            "source": item.get("hostPageUrl"),
                                            "title": item.get("name"),
                                            "date": item.get("datePublished")
                                        })
                
                return {
                    "found_similar": len(similar_images) > 0,
                    "similar_count": len(similar_images),
                    "similar_images": similar_images,
                    "oldest_usage": self._find_oldest_usage(similar_images)
                }
            else:
                return {"error": f"Bing API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Bing reverse search failed: {e}")
            return {"error": str(e)}
    
    def reverse_image_search_google(self, image_url: str) -> Dict[str, Any]:
        """Perform reverse image search using Google Custom Search API"""
        if not self.google_api_key or not self.google_cx:
            return {"error": "Google API credentials not configured"}
        
        try:
            endpoint = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "searchType": "image",
                "imgType": "photo",
                "q": f"site:* {image_url}",  # Search for the image URL
                "num": 10
            }
            
            response = requests.get(endpoint, params=params, timeout=15)
            
            if response.status_code == 200:
                results = response.json()
                items = results.get("items", [])
                
                similar_images = []
                for item in items:
                    similar_images.append({
                        "url": item.get("link"),
                        "source": item.get("image", {}).get("contextLink"),
                        "title": item.get("title"),
                        "snippet": item.get("snippet")
                    })
                
                return {
                    "found_similar": len(similar_images) > 0,
                    "similar_count": len(similar_images),
                    "similar_images": similar_images,
                    "oldest_usage": self._find_oldest_usage(similar_images)
                }
            else:
                return {"error": f"Google API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Google reverse search failed: {e}")
            return {"error": str(e)}
    
    def _find_oldest_usage(self, similar_images: List[Dict]) -> Optional[Dict]:
        """Find the oldest usage of an image from search results"""
        oldest = None
        oldest_date = None
        
        for image in similar_images:
            date_str = image.get("date")
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if oldest_date is None or date_obj < oldest_date:
                        oldest_date = date_obj
                        oldest = image
                except:
                    continue
        
        return oldest
    
    def analyze_image_suspicious(self, image_url: str, post_context: Dict[str, Any]) -> Dict[str, Any]:
        """Complete analysis of suspicious image"""
        analysis = {
            "image_url": image_url,
            "post_context": post_context,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check against official VIP images
        analysis["vip_match"] = self.check_against_official_images(image_url)
        
        # Reverse image search
        analysis["bing_search"] = self.reverse_image_search_bing(image_url)
        analysis["google_search"] = self.reverse_image_search_google(image_url)
        
        # Calculate risk assessment
        analysis["risk_assessment"] = self._calculate_image_risk(analysis)
        
        return analysis
    
    def _calculate_image_risk(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk score for suspicious image"""
        risk_factors = []
        risk_score = 0.0
        
        # VIP image match
        vip_match = analysis.get("vip_match", {})
        if vip_match.get("is_match"):
            risk_factors.append("Matches official VIP image")
            risk_score += 0.8
        
        # Reverse search results
        bing_results = analysis.get("bing_search", {})
        google_results = analysis.get("google_search", {})
        
        total_similar = (bing_results.get("similar_count", 0) + 
                        google_results.get("similar_count", 0))
        
        if total_similar > 5:
            risk_factors.append(f"Found in {total_similar} other locations")
            risk_score += 0.4
        elif total_similar > 0:
            risk_factors.append(f"Found in {total_similar} other locations")
            risk_score += 0.2
        
        # Old image usage
        oldest_bing = bing_results.get("oldest_usage")
        oldest_google = google_results.get("oldest_usage")
        
        if oldest_bing or oldest_google:
            risk_factors.append("Image has previous usage history")
            risk_score += 0.3
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": min(risk_score, 1.0),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "requires_action": risk_score > 0.5
        }
    
    def save_suspicious_image(self, analysis: Dict[str, Any]) -> Optional[int]:
        """Save suspicious image analysis to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                vip_match = analysis.get("vip_match", {})
                risk_assessment = analysis.get("risk_assessment", {})
                
                # Combine reverse search results
                search_results = {
                    "bing": analysis.get("bing_search", {}),
                    "google": analysis.get("google_search", {})
                }
                
                cursor.execute("""
                    INSERT INTO suspicious_images 
                    (image_url, post_url, platform, username, matched_vip_image_id,
                     similarity_score, reverse_search_results, detection_reason, risk_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis["image_url"],
                    analysis.get("post_context", {}).get("post_url"),
                    analysis.get("post_context", {}).get("platform"),
                    analysis.get("post_context", {}).get("username"),
                    vip_match.get("matched_image", {}).get("id"),
                    vip_match.get("similarity_score", 0.0),
                    str(search_results),
                    "; ".join(risk_assessment.get("risk_factors", [])),
                    risk_assessment.get("risk_score", 0.0)
                ))
                
                image_id = cursor.lastrowid
                conn.commit()
                
                logger.warning(f"Suspicious image detected: {analysis['image_url']} (ID: {image_id})")
                return image_id
                
        except Exception as e:
            logger.error(f"Failed to save suspicious image: {e}")
            return None

# Global detector instance
_image_detector = None

def get_image_detector() -> ImageDetector:
    """Get global image detector instance"""
    global _image_detector
    if _image_detector is None:
        _image_detector = ImageDetector()
    return _image_detector

def analyze_suspicious_image(image_url: str, post_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for image analysis
    
    Args:
        image_url: URL of image to analyze
        post_context: Context about the post containing the image
        
    Returns:
        Image analysis results
    """
    detector = get_image_detector()
    return detector.analyze_image_suspicious(image_url, post_context)

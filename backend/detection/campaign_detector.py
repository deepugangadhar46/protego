#!/usr/bin/env python3
"""
Phase 1: Campaign Detection
Detects coordinated campaigns using text clustering and timing analysis
"""

import os
import logging
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# Text similarity imports
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False
    logging.warning("Sentence transformers not available. Install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)

class CampaignDetector:
    """Detects coordinated campaigns and duplicate content"""
    
    def __init__(self, db_path: str = "backend/monitoring/campaigns.db"):
        self.db_path = db_path
        self.embedding_model = None
        self.similarity_threshold = 0.85  # Cosine similarity threshold for duplicates
        self.time_window_minutes = 60  # Time window for campaign detection
        self.min_cluster_size = 3  # Minimum posts to consider a campaign
        self._init_database()
        self._init_models()
    
    def _init_database(self):
        """Initialize campaigns database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Posts table for clustering analysis
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS campaign_posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id TEXT UNIQUE,
                        platform TEXT NOT NULL,
                        username TEXT,
                        user_id TEXT,
                        content TEXT NOT NULL,
                        content_hash TEXT,
                        embedding_vector BLOB,
                        timestamp TEXT NOT NULL,
                        vip_mentioned TEXT,
                        cluster_id INTEGER,
                        is_duplicate BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Detected campaigns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detected_campaigns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_hash TEXT UNIQUE,
                        content_sample TEXT,
                        post_count INTEGER,
                        unique_users INTEGER,
                        platforms TEXT,
                        time_span_minutes INTEGER,
                        similarity_score REAL,
                        vip_mentioned TEXT,
                        campaign_type TEXT,
                        risk_score REAL,
                        status TEXT DEFAULT 'active',
                        first_seen TEXT,
                        last_seen TEXT,
                        detected_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Campaign posts relationship
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS campaign_post_relations (
                        campaign_id INTEGER,
                        post_id INTEGER,
                        FOREIGN KEY (campaign_id) REFERENCES detected_campaigns (id),
                        FOREIGN KEY (post_id) REFERENCES campaign_posts (id)
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON campaign_posts (timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON campaign_posts (content_hash)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON campaign_posts (cluster_id)")
                
                conn.commit()
                logger.info("Campaign detection database initialized")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _init_models(self):
        """Initialize embedding models"""
        if CLUSTERING_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
    
    def add_post(self, post_data: Dict[str, Any]) -> Optional[int]:
        """Add post for campaign analysis"""
        try:
            content = post_data.get('content', '')
            if not content.strip():
                return None
            
            # Generate content hash
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Generate embedding if model available
            embedding_blob = None
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode([content])[0]
                    embedding_blob = embedding.tobytes()
                except Exception as e:
                    logger.error(f"Embedding generation failed: {e}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO campaign_posts 
                    (post_id, platform, username, user_id, content, content_hash, 
                     embedding_vector, timestamp, vip_mentioned)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_data.get('post_id'),
                    post_data.get('platform'),
                    post_data.get('username'),
                    post_data.get('user_id'),
                    content,
                    content_hash,
                    embedding_blob,
                    post_data.get('timestamp', datetime.now().isoformat()),
                    post_data.get('vip_mentioned')
                ))
                
                post_db_id = cursor.lastrowid
                conn.commit()
                
                return post_db_id
                
        except Exception as e:
            logger.error(f"Failed to add post: {e}")
            return None
    
    def detect_exact_duplicates(self, time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """Detect posts with identical content hashes"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=time_window_hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT content_hash, COUNT(*) as count, 
                           GROUP_CONCAT(id) as post_ids,
                           GROUP_CONCAT(DISTINCT username) as usernames,
                           GROUP_CONCAT(DISTINCT platform) as platforms,
                           MIN(timestamp) as first_seen,
                           MAX(timestamp) as last_seen,
                           content
                    FROM campaign_posts 
                    WHERE timestamp > ?
                    GROUP BY content_hash 
                    HAVING COUNT(*) >= ?
                    ORDER BY count DESC
                """, (cutoff_time, self.min_cluster_size))
                
                duplicates = []
                for row in cursor.fetchall():
                    content_hash, count, post_ids, usernames, platforms, first_seen, last_seen, content = row
                    
                    # Calculate time span
                    first_dt = datetime.fromisoformat(first_seen)
                    last_dt = datetime.fromisoformat(last_seen)
                    time_span = (last_dt - first_dt).total_seconds() / 60  # minutes
                    
                    duplicates.append({
                        "content_hash": content_hash,
                        "post_count": count,
                        "post_ids": [int(x) for x in post_ids.split(',')],
                        "unique_users": len(set(usernames.split(','))),
                        "usernames": usernames.split(','),
                        "platforms": list(set(platforms.split(','))),
                        "time_span_minutes": time_span,
                        "first_seen": first_seen,
                        "last_seen": last_seen,
                        "content_sample": content[:200] + "..." if len(content) > 200 else content,
                        "campaign_type": "exact_duplicate"
                    })
                
                return duplicates
                
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            return []
    
    def detect_similar_campaigns(self, time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """Detect campaigns using text embeddings and clustering"""
        if not CLUSTERING_AVAILABLE or not self.embedding_model:
            logger.warning("Clustering not available, using exact duplicates only")
            return self.detect_exact_duplicates(time_window_hours)
        
        try:
            cutoff_time = (datetime.now() - timedelta(hours=time_window_hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent posts with embeddings
                cursor.execute("""
                    SELECT id, content, embedding_vector, timestamp, username, platform, vip_mentioned
                    FROM campaign_posts 
                    WHERE timestamp > ? AND embedding_vector IS NOT NULL
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
                
                posts = cursor.fetchall()
                
                if len(posts) < self.min_cluster_size:
                    return []
                
                # Extract embeddings
                embeddings = []
                post_info = []
                
                for post in posts:
                    post_id, content, embedding_blob, timestamp, username, platform, vip_mentioned = post
                    
                    try:
                        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                        embeddings.append(embedding)
                        post_info.append({
                            "id": post_id,
                            "content": content,
                            "timestamp": timestamp,
                            "username": username,
                            "platform": platform,
                            "vip_mentioned": vip_mentioned
                        })
                    except Exception as e:
                        logger.error(f"Failed to decode embedding: {e}")
                        continue
                
                if len(embeddings) < self.min_cluster_size:
                    return []
                
                # Perform clustering
                embeddings_array = np.array(embeddings)
                
                # Use DBSCAN for clustering
                clustering = DBSCAN(
                    eps=1 - self.similarity_threshold,  # Convert similarity to distance
                    min_samples=self.min_cluster_size,
                    metric='cosine'
                ).fit(embeddings_array)
                
                # Group posts by cluster
                clusters = defaultdict(list)
                for i, cluster_id in enumerate(clustering.labels_):
                    if cluster_id != -1:  # Ignore noise points
                        clusters[cluster_id].append(post_info[i])
                
                # Analyze clusters for campaigns
                campaigns = []
                for cluster_id, cluster_posts in clusters.items():
                    if len(cluster_posts) >= self.min_cluster_size:
                        campaign = self._analyze_cluster(cluster_posts, embeddings_array, clustering.labels_)
                        if campaign:
                            campaigns.append(campaign)
                
                return campaigns
                
        except Exception as e:
            logger.error(f"Similar campaign detection failed: {e}")
            return []
    
    def _analyze_cluster(self, cluster_posts: List[Dict], embeddings: np.ndarray, labels: np.ndarray) -> Optional[Dict]:
        """Analyze a cluster of posts to determine if it's a campaign"""
        try:
            # Calculate cluster statistics
            timestamps = [datetime.fromisoformat(post['timestamp']) for post in cluster_posts]
            usernames = [post['username'] for post in cluster_posts if post['username']]
            platforms = [post['platform'] for post in cluster_posts]
            
            # Time analysis
            first_seen = min(timestamps)
            last_seen = max(timestamps)
            time_span = (last_seen - first_seen).total_seconds() / 60  # minutes
            
            # User analysis
            unique_users = len(set(usernames))
            unique_platforms = len(set(platforms))
            
            # Content analysis
            content_sample = cluster_posts[0]['content']
            
            # Calculate average similarity within cluster
            cluster_indices = [i for i, label in enumerate(labels) if label == labels[0]]
            if len(cluster_indices) > 1:
                cluster_embeddings = embeddings[cluster_indices]
                similarity_matrix = cosine_similarity(cluster_embeddings)
                avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
            else:
                avg_similarity = 1.0
            
            # Risk scoring
            risk_score = self._calculate_campaign_risk(
                post_count=len(cluster_posts),
                unique_users=unique_users,
                time_span=time_span,
                similarity=avg_similarity,
                platforms=unique_platforms
            )
            
            # Determine campaign type
            if avg_similarity > 0.95:
                campaign_type = "near_duplicate"
            elif time_span < 30 and unique_users > 5:
                campaign_type = "coordinated_burst"
            elif unique_users < len(cluster_posts) * 0.3:
                campaign_type = "bot_network"
            else:
                campaign_type = "similar_content"
            
            return {
                "post_count": len(cluster_posts),
                "unique_users": unique_users,
                "platforms": list(set(platforms)),
                "time_span_minutes": time_span,
                "similarity_score": avg_similarity,
                "first_seen": first_seen.isoformat(),
                "last_seen": last_seen.isoformat(),
                "content_sample": content_sample[:200] + "..." if len(content_sample) > 200 else content_sample,
                "campaign_type": campaign_type,
                "risk_score": risk_score,
                "post_ids": [post['id'] for post in cluster_posts],
                "vip_mentioned": cluster_posts[0].get('vip_mentioned')
            }
            
        except Exception as e:
            logger.error(f"Cluster analysis failed: {e}")
            return None
    
    def _calculate_campaign_risk(self, post_count: int, unique_users: int, 
                                time_span: float, similarity: float, platforms: int) -> float:
        """Calculate risk score for detected campaign"""
        risk_factors = []
        
        # High post volume
        if post_count > 20:
            risk_factors.append(0.3)
        elif post_count > 10:
            risk_factors.append(0.2)
        
        # Low user diversity (possible bots)
        user_diversity = unique_users / post_count
        if user_diversity < 0.3:
            risk_factors.append(0.4)
        elif user_diversity < 0.5:
            risk_factors.append(0.2)
        
        # Rapid posting (coordinated timing)
        if time_span < 15:  # 15 minutes
            risk_factors.append(0.3)
        elif time_span < 60:  # 1 hour
            risk_factors.append(0.2)
        
        # High similarity (copy-paste behavior)
        if similarity > 0.95:
            risk_factors.append(0.3)
        elif similarity > 0.85:
            risk_factors.append(0.2)
        
        # Cross-platform coordination
        if platforms > 2:
            risk_factors.append(0.2)
        
        return min(sum(risk_factors), 1.0)
    
    def save_detected_campaign(self, campaign_data: Dict[str, Any]) -> Optional[int]:
        """Save detected campaign to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Generate campaign hash
                campaign_content = campaign_data.get('content_sample', '')
                campaign_hash = hashlib.md5(
                    f"{campaign_content}_{campaign_data.get('first_seen')}".encode()
                ).hexdigest()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO detected_campaigns 
                    (campaign_hash, content_sample, post_count, unique_users, platforms,
                     time_span_minutes, similarity_score, vip_mentioned, campaign_type,
                     risk_score, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign_hash,
                    campaign_data.get('content_sample'),
                    campaign_data.get('post_count'),
                    campaign_data.get('unique_users'),
                    ','.join(campaign_data.get('platforms', [])),
                    campaign_data.get('time_span_minutes'),
                    campaign_data.get('similarity_score'),
                    campaign_data.get('vip_mentioned'),
                    campaign_data.get('campaign_type'),
                    campaign_data.get('risk_score'),
                    campaign_data.get('first_seen'),
                    campaign_data.get('last_seen')
                ))
                
                campaign_id = cursor.lastrowid
                
                # Link posts to campaign
                post_ids = campaign_data.get('post_ids', [])
                for post_id in post_ids:
                    cursor.execute("""
                        INSERT OR IGNORE INTO campaign_post_relations (campaign_id, post_id)
                        VALUES (?, ?)
                    """, (campaign_id, post_id))
                
                conn.commit()
                logger.warning(f"Campaign detected and saved: ID {campaign_id}, Type: {campaign_data.get('campaign_type')}")
                return campaign_id
                
        except Exception as e:
            logger.error(f"Failed to save campaign: {e}")
            return None
    
    def get_active_campaigns(self, limit: int = 50) -> List[Dict]:
        """Get active campaigns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM detected_campaigns 
                    WHERE status = 'active'
                    ORDER BY risk_score DESC, detected_at DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            return []
    
    def run_campaign_detection(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Run complete campaign detection analysis"""
        results = {
            "exact_duplicates": [],
            "similar_campaigns": [],
            "total_campaigns": 0,
            "high_risk_campaigns": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Detect exact duplicates
        exact_duplicates = self.detect_exact_duplicates(time_window_hours)
        results["exact_duplicates"] = exact_duplicates
        
        # Save exact duplicates as campaigns
        for duplicate in exact_duplicates:
            duplicate["risk_score"] = self._calculate_campaign_risk(
                duplicate["post_count"],
                duplicate["unique_users"], 
                duplicate["time_span_minutes"],
                1.0,  # Exact match
                len(duplicate["platforms"])
            )
            campaign_id = self.save_detected_campaign(duplicate)
            duplicate["campaign_id"] = campaign_id
        
        # Detect similar campaigns
        similar_campaigns = self.detect_similar_campaigns(time_window_hours)
        results["similar_campaigns"] = similar_campaigns
        
        # Save similar campaigns
        for campaign in similar_campaigns:
            campaign_id = self.save_detected_campaign(campaign)
            campaign["campaign_id"] = campaign_id
        
        # Calculate summary statistics
        all_campaigns = exact_duplicates + similar_campaigns
        results["total_campaigns"] = len(all_campaigns)
        results["high_risk_campaigns"] = len([c for c in all_campaigns if c.get("risk_score", 0) > 0.7])
        
        return results

# Global detector instance
_campaign_detector = None

def get_campaign_detector() -> CampaignDetector:
    """Get global campaign detector instance"""
    global _campaign_detector
    if _campaign_detector is None:
        _campaign_detector = CampaignDetector()
    return _campaign_detector

def detect_campaigns(time_window_hours: int = 24) -> Dict[str, Any]:
    """
    Convenience function for campaign detection
    
    Args:
        time_window_hours: Time window to analyze
        
    Returns:
        Campaign detection results
    """
    detector = get_campaign_detector()
    return detector.run_campaign_detection(time_window_hours)

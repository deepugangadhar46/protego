#!/usr/bin/env python3
"""
Content Logger for Protego System
Logs flagged content and classification results to database
"""

import os
import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ContentLogger:
    """Logger for flagged content and ML predictions"""
    
    def __init__(self, db_path: str = "backend/monitoring/flagged_content.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create flagged content table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS flagged_content (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        content TEXT NOT NULL,
                        vip_name TEXT,
                        platform TEXT,
                        prediction TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        threat_score REAL,
                        threat_type TEXT,
                        severity TEXT,
                        is_fake BOOLEAN,
                        is_real BOOLEAN,
                        model_type TEXT,
                        indicators TEXT,
                        recommendations TEXT,
                        user_id TEXT,
                        post_id TEXT,
                        url TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create alerts table for high-priority items
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_id INTEGER,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TEXT,
                        FOREIGN KEY (content_id) REFERENCES flagged_content (id)
                    )
                """)
                
                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON flagged_content (timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_vip_name 
                    ON flagged_content (vip_name)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def save_alert(self, text: str, result: Dict, vip_name: str = None, 
                   platform: str = None, **kwargs) -> Optional[int]:
        """
        Save flagged content to database
        
        Args:
            text: Original content text
            result: Classification result from ML model
            vip_name: Name of VIP mentioned
            platform: Platform where content was found
            **kwargs: Additional metadata (user_id, post_id, url, etc.)
            
        Returns:
            Database ID of saved record, or None if failed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract data from result
                prediction = result.get('prediction', 'unknown')
                confidence = result.get('confidence', 0.0)
                threat_score = result.get('threat_score', 0.0)
                threat_type = result.get('threat_type', '')
                severity = result.get('severity', '')
                is_fake = result.get('is_fake', False)
                is_real = result.get('is_real', False)
                model_type = result.get('model_type', '')
                
                # Handle complex fields
                indicators = json.dumps(result.get('indicators', []))
                recommendations = json.dumps(result.get('recommendations', []))
                
                cursor.execute("""
                    INSERT INTO flagged_content (
                        timestamp, content, vip_name, platform, prediction, confidence,
                        threat_score, threat_type, severity, is_fake, is_real, model_type,
                        indicators, recommendations, user_id, post_id, url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    text,
                    vip_name,
                    platform,
                    prediction,
                    confidence,
                    threat_score,
                    threat_type,
                    severity,
                    is_fake,
                    is_real,
                    model_type,
                    indicators,
                    recommendations,
                    kwargs.get('user_id'),
                    kwargs.get('post_id'),
                    kwargs.get('url')
                ))
                
                content_id = cursor.lastrowid
                
                # Create alert if high severity
                if severity in ['high', 'critical'] or (is_fake and confidence > 0.8):
                    self._create_alert(cursor, content_id, severity, prediction, confidence)
                
                conn.commit()
                logger.info(f"Flagged content saved with ID: {content_id}")
                return content_id
                
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
            return None
    
    def _create_alert(self, cursor, content_id: int, severity: str, 
                     prediction: str, confidence: float):
        """Create alert for high-priority content"""
        try:
            alert_type = "fake_news" if prediction == "fake" else "threat"
            message = f"{severity.title()} {alert_type} detected (confidence: {confidence:.2f})"
            
            cursor.execute("""
                INSERT INTO alerts (content_id, alert_type, severity, message)
                VALUES (?, ?, ?, ?)
            """, (content_id, alert_type, severity, message))
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent flagged content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT f.*, a.alert_type, a.message as alert_message, a.status
                    FROM flagged_content f
                    LEFT JOIN alerts a ON f.id = a.content_id
                    ORDER BY f.timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    # Parse JSON fields
                    try:
                        record['indicators'] = json.loads(record['indicators'] or '[]')
                        record['recommendations'] = json.loads(record['recommendations'] or '[]')
                    except:
                        record['indicators'] = []
                        record['recommendations'] = []
                    
                    results.append(record)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def get_vip_stats(self, vip_name: str, days: int = 30) -> Dict:
        """Get statistics for a specific VIP"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_mentions,
                        SUM(CASE WHEN is_fake = 1 THEN 1 ELSE 0 END) as fake_count,
                        AVG(confidence) as avg_confidence,
                        MAX(threat_score) as max_threat_score
                    FROM flagged_content 
                    WHERE vip_name = ? 
                    AND datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                """, (vip_name, days))
                
                result = cursor.fetchone()
                
                return {
                    'vip_name': vip_name,
                    'total_mentions': result[0] or 0,
                    'fake_count': result[1] or 0,
                    'avg_confidence': result[2] or 0.0,
                    'max_threat_score': result[3] or 0.0,
                    'fake_percentage': (result[1] / result[0] * 100) if result[0] else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get VIP stats: {e}")
            return {'error': str(e)}

# Global logger instance
_content_logger = None

def get_content_logger() -> ContentLogger:
    """Get global content logger instance"""
    global _content_logger
    if _content_logger is None:
        _content_logger = ContentLogger()
    return _content_logger

def save_alert(text: str, result: Dict, vip_name: str = None, 
               platform: str = None, **kwargs) -> Optional[int]:
    """
    Convenience function to save flagged content
    
    Args:
        text: Original content text
        result: Classification result
        vip_name: VIP name if applicable
        platform: Platform name
        **kwargs: Additional metadata
        
    Returns:
        Database ID of saved record
    """
    logger = get_content_logger()
    return logger.save_alert(text, result, vip_name, platform, **kwargs)

#!/usr/bin/env python3
"""
Phase 2: Evidence & Contextualization Manager
Stores structured evidence for all flagged content with screenshots and metadata
"""

import os
import logging
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from urllib.parse import urlparse

# Screenshot capture
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Install with: pip install playwright")

logger = logging.getLogger(__name__)

class EvidenceManager:
    """Manages evidence collection and storage for flagged content"""
    
    def __init__(self, db_path: str = "backend/monitoring/evidence.db", 
                 screenshots_dir: str = "backend/monitoring/screenshots"):
        self.db_path = db_path
        self.screenshots_dir = screenshots_dir
        self._init_database()
        self._ensure_directories()
    
    def _init_database(self):
        """Initialize evidence database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Main evidence table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evidence_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE,
                        source_platform TEXT NOT NULL,
                        post_url TEXT,
                        screenshot_url TEXT,
                        screenshot_path TEXT,
                        reason_flagged TEXT NOT NULL,
                        detection_type TEXT,
                        raw_text TEXT,
                        raw_metadata TEXT,
                        image_urls TEXT,
                        image_hashes TEXT,
                        username TEXT,
                        user_id TEXT,
                        vip_mentioned TEXT,
                        threat_score REAL,
                        confidence_score REAL,
                        verification_status TEXT DEFAULT 'pending',
                        verified_by TEXT,
                        verified_at TEXT,
                        verification_notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Detection details table for specific detection types
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detection_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        evidence_id INTEGER,
                        detection_type TEXT NOT NULL,
                        detection_data TEXT,
                        model_used TEXT,
                        confidence REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (evidence_id) REFERENCES evidence_records (id)
                    )
                """)
                
                # Related content table for campaigns/clusters
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS related_content (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        primary_evidence_id INTEGER,
                        related_evidence_id INTEGER,
                        relationship_type TEXT,
                        similarity_score REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (primary_evidence_id) REFERENCES evidence_records (id),
                        FOREIGN KEY (related_evidence_id) REFERENCES evidence_records (id)
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON evidence_records (source_platform)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_verification ON evidence_records (verification_status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_type ON evidence_records (detection_type)")
                
                conn.commit()
                logger.info("Evidence database initialized")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _ensure_directories(self):
        """Ensure screenshot directories exist"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def capture_screenshot(self, url: str, alert_id: str) -> Optional[str]:
        """Capture screenshot of the flagged content"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Screenshot capture not available - Playwright not installed")
            return None
        
        try:
            screenshot_filename = f"alert_{alert_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set viewport and user agent
                page.set_viewport_size({"width": 1280, "height": 720})
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                # Navigate and capture
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=10000)
                
                # Take screenshot
                page.screenshot(path=screenshot_path, full_page=True)
                browser.close()
                
                logger.info(f"Screenshot captured: {screenshot_path}")
                return screenshot_path
                
        except Exception as e:
            logger.error(f"Screenshot capture failed for {url}: {e}")
            return None
    
    def store_evidence(self, detection_result: Dict[str, Any]) -> Optional[str]:
        """Store comprehensive evidence for a detection"""
        try:
            # Generate unique alert ID
            alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(detection_result)) % 10000:04d}"
            
            # Extract core information
            post_url = detection_result.get('post_url')
            platform = detection_result.get('platform', 'unknown')
            detection_type = detection_result.get('detection_type', 'unknown')
            
            # Capture screenshot if URL available
            screenshot_path = None
            if post_url:
                screenshot_path = self.capture_screenshot(post_url, alert_id)
            
            # Process images
            image_urls = detection_result.get('image_urls', [])
            image_hashes = []
            
            for img_url in image_urls:
                try:
                    response = requests.get(img_url, timeout=10)
                    if response.status_code == 200:
                        import hashlib
                        img_hash = hashlib.md5(response.content).hexdigest()
                        image_hashes.append(img_hash)
                except:
                    image_hashes.append("")
            
            # Store main evidence record
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO evidence_records 
                    (alert_id, source_platform, post_url, screenshot_path, reason_flagged,
                     detection_type, raw_text, raw_metadata, image_urls, image_hashes,
                     username, user_id, vip_mentioned, threat_score, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_id,
                    platform,
                    post_url,
                    screenshot_path,
                    detection_result.get('reason_flagged', 'Unknown'),
                    detection_type,
                    detection_result.get('raw_text', ''),
                    json.dumps(detection_result.get('metadata', {})),
                    json.dumps(image_urls),
                    json.dumps(image_hashes),
                    detection_result.get('username'),
                    detection_result.get('user_id'),
                    detection_result.get('vip_mentioned'),
                    detection_result.get('threat_score', 0.0),
                    detection_result.get('confidence_score', 0.0)
                ))
                
                evidence_id = cursor.lastrowid
                
                # Store detailed detection information
                detection_details = detection_result.get('detection_details', [])
                for detail in detection_details:
                    cursor.execute("""
                        INSERT INTO detection_details 
                        (evidence_id, detection_type, detection_data, model_used, confidence)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        evidence_id,
                        detail.get('type'),
                        json.dumps(detail.get('data', {})),
                        detail.get('model'),
                        detail.get('confidence', 0.0)
                    ))
                
                conn.commit()
                
                logger.info(f"Evidence stored: {alert_id} (ID: {evidence_id})")
                return alert_id
                
        except Exception as e:
            logger.error(f"Failed to store evidence: {e}")
            return None
    
    def get_evidence(self, alert_id: str = None, verification_status: str = None, 
                    limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve evidence records"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM evidence_records WHERE 1=1"
                params = []
                
                if alert_id:
                    query += " AND alert_id = ?"
                    params.append(alert_id)
                
                if verification_status:
                    query += " AND verification_status = ?"
                    params.append(verification_status)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                
                evidence_records = []
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    try:
                        record['raw_metadata'] = json.loads(record['raw_metadata'] or '{}')
                        record['image_urls'] = json.loads(record['image_urls'] or '[]')
                        record['image_hashes'] = json.loads(record['image_hashes'] or '[]')
                    except:
                        pass
                    
                    # Get detection details
                    cursor.execute("""
                        SELECT detection_type, detection_data, model_used, confidence
                        FROM detection_details WHERE evidence_id = ?
                    """, (record['id'],))
                    
                    details = []
                    for detail_row in cursor.fetchall():
                        detail = {
                            'type': detail_row[0],
                            'data': json.loads(detail_row[1] or '{}'),
                            'model': detail_row[2],
                            'confidence': detail_row[3]
                        }
                        details.append(detail)
                    
                    record['detection_details'] = details
                    evidence_records.append(record)
                
                return evidence_records
                
        except Exception as e:
            logger.error(f"Failed to retrieve evidence: {e}")
            return []
    
    def verify_evidence(self, alert_id: str, is_confirmed: bool, 
                       verified_by: str, notes: str = "") -> bool:
        """Mark evidence as verified (confirmed fake or dismissed)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                status = "confirmed_fake" if is_confirmed else "dismissed"
                
                cursor.execute("""
                    UPDATE evidence_records 
                    SET verification_status = ?, verified_by = ?, verified_at = ?, 
                        verification_notes = ?, updated_at = ?
                    WHERE alert_id = ?
                """, (
                    status,
                    verified_by,
                    datetime.now().isoformat(),
                    notes,
                    datetime.now().isoformat(),
                    alert_id
                ))
                
                conn.commit()
                logger.info(f"Evidence {alert_id} verified as {status} by {verified_by}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify evidence: {e}")
            return False
    
    def link_related_content(self, primary_alert_id: str, related_alert_id: str,
                           relationship_type: str, similarity_score: float = 0.0) -> bool:
        """Link related content (e.g., campaign posts)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get evidence IDs
                cursor.execute("SELECT id FROM evidence_records WHERE alert_id = ?", (primary_alert_id,))
                primary_id = cursor.fetchone()
                
                cursor.execute("SELECT id FROM evidence_records WHERE alert_id = ?", (related_alert_id,))
                related_id = cursor.fetchone()
                
                if not primary_id or not related_id:
                    logger.error("One or both alert IDs not found")
                    return False
                
                cursor.execute("""
                    INSERT OR IGNORE INTO related_content 
                    (primary_evidence_id, related_evidence_id, relationship_type, similarity_score)
                    VALUES (?, ?, ?, ?)
                """, (primary_id[0], related_id[0], relationship_type, similarity_score))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to link related content: {e}")
            return False
    
    def get_evidence_summary(self) -> Dict[str, Any]:
        """Get summary statistics of evidence"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total counts
                cursor.execute("SELECT COUNT(*) FROM evidence_records")
                total_evidence = cursor.fetchone()[0]
                
                # By verification status
                cursor.execute("""
                    SELECT verification_status, COUNT(*) 
                    FROM evidence_records 
                    GROUP BY verification_status
                """)
                verification_stats = dict(cursor.fetchall())
                
                # By detection type
                cursor.execute("""
                    SELECT detection_type, COUNT(*) 
                    FROM evidence_records 
                    GROUP BY detection_type
                """)
                detection_stats = dict(cursor.fetchall())
                
                # By platform
                cursor.execute("""
                    SELECT source_platform, COUNT(*) 
                    FROM evidence_records 
                    GROUP BY source_platform
                """)
                platform_stats = dict(cursor.fetchall())
                
                return {
                    "total_evidence": total_evidence,
                    "verification_status": verification_stats,
                    "detection_types": detection_stats,
                    "platforms": platform_stats,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get evidence summary: {e}")
            return {}

# Global evidence manager
_evidence_manager = None

def get_evidence_manager() -> EvidenceManager:
    """Get global evidence manager instance"""
    global _evidence_manager
    if _evidence_manager is None:
        _evidence_manager = EvidenceManager()
    return _evidence_manager

def store_detection_evidence(detection_result: Dict[str, Any]) -> Optional[str]:
    """
    Convenience function to store evidence
    
    Args:
        detection_result: Complete detection result with evidence
        
    Returns:
        Alert ID if successful
    """
    manager = get_evidence_manager()
    return manager.store_evidence(detection_result)

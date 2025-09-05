#!/usr/bin/env python3
"""
Phase 2: Verification Flow with Human Feedback
Manages human verification workflow and model retraining
"""

import os
import logging
import sqlite3
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    PENDING = "pending"
    CONFIRMED_FAKE = "confirmed_fake"
    DISMISSED = "dismissed"
    NEEDS_REVIEW = "needs_review"
    ESCALATED = "escalated"

class VerificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VerificationFlow:
    """Manages verification workflow and human feedback"""
    
    def __init__(self, db_path: str = "backend/monitoring/verification.db"):
        self.db_path = db_path
        self.verification_callbacks = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize verification database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verification queue table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS verification_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE NOT NULL,
                        evidence_id INTEGER,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'pending',
                        detection_type TEXT,
                        threat_score REAL,
                        confidence_score REAL,
                        auto_flagged_reason TEXT,
                        assigned_to TEXT,
                        assigned_at TEXT,
                        reviewed_by TEXT,
                        reviewed_at TEXT,
                        verification_result TEXT,
                        verification_confidence REAL,
                        verification_notes TEXT,
                        feedback_data TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Verification history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS verification_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        performed_by TEXT,
                        previous_status TEXT,
                        new_status TEXT,
                        notes TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Reviewer performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reviewer_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reviewer_id TEXT NOT NULL,
                        total_reviews INTEGER DEFAULT 0,
                        correct_reviews INTEGER DEFAULT 0,
                        accuracy_rate REAL DEFAULT 0.0,
                        avg_review_time REAL DEFAULT 0.0,
                        specialization TEXT,
                        last_active TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Model feedback table for retraining
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        model_prediction TEXT,
                        model_confidence REAL,
                        human_verdict TEXT,
                        human_confidence REAL,
                        feedback_type TEXT,
                        text_content TEXT,
                        features_used TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON verification_queue (status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_priority ON verification_queue (priority)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_assigned ON verification_queue (assigned_to)")
                
                conn.commit()
                logger.info("Verification database initialized")
                
        except Exception as e:
            logger.error(f"Verification database initialization failed: {e}")
    
    def add_to_verification_queue(self, alert_data: Dict[str, Any]) -> bool:
        """Add alert to verification queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Determine priority based on threat score and detection type
                priority = self._calculate_priority(alert_data)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO verification_queue 
                    (alert_id, evidence_id, priority, detection_type, threat_score, 
                     confidence_score, auto_flagged_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_data.get('alert_id'),
                    alert_data.get('evidence_id'),
                    priority.value,
                    alert_data.get('detection_type'),
                    alert_data.get('threat_score', 0.0),
                    alert_data.get('confidence_score', 0.0),
                    alert_data.get('reason_flagged', '')
                ))
                
                conn.commit()
                
                # Log action
                self._log_verification_action(
                    alert_data.get('alert_id'),
                    "queued",
                    "system",
                    None,
                    VerificationStatus.PENDING.value,
                    f"Added to queue with {priority.value} priority"
                )
                
                logger.info(f"Added alert {alert_data.get('alert_id')} to verification queue")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add to verification queue: {e}")
            return False
    
    def _calculate_priority(self, alert_data: Dict[str, Any]) -> VerificationPriority:
        """Calculate verification priority based on alert data"""
        threat_score = alert_data.get('threat_score', 0.0)
        confidence_score = alert_data.get('confidence_score', 0.0)
        detection_type = alert_data.get('detection_type', '')
        vip_mentioned = alert_data.get('vip_mentioned')
        
        # Critical priority conditions
        if (threat_score > 0.9 or 
            (vip_mentioned and threat_score > 0.7) or
            detection_type == 'fake_profile' and threat_score > 0.8):
            return VerificationPriority.CRITICAL
        
        # High priority conditions
        elif (threat_score > 0.7 or
              (vip_mentioned and threat_score > 0.5) or
              confidence_score > 0.8):
            return VerificationPriority.HIGH
        
        # Medium priority conditions
        elif threat_score > 0.5 or confidence_score > 0.6:
            return VerificationPriority.MEDIUM
        
        # Low priority
        else:
            return VerificationPriority.LOW
    
    def get_verification_queue(self, assigned_to: str = None, 
                             priority: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get items from verification queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM verification_queue 
                    WHERE status IN ('pending', 'needs_review')
                """
                params = []
                
                if assigned_to:
                    query += " AND assigned_to = ?"
                    params.append(assigned_to)
                
                if priority:
                    query += " AND priority = ?"
                    params.append(priority)
                
                # Order by priority and creation time
                query += """
                    ORDER BY 
                        CASE priority 
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        created_at ASC
                    LIMIT ?
                """
                params.append(limit)
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                
                queue_items = []
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    queue_items.append(item)
                
                return queue_items
                
        except Exception as e:
            logger.error(f"Failed to get verification queue: {e}")
            return []
    
    def assign_for_verification(self, alert_id: str, reviewer_id: str) -> bool:
        """Assign alert to reviewer"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE verification_queue 
                    SET assigned_to = ?, assigned_at = ?, updated_at = ?
                    WHERE alert_id = ? AND status = 'pending'
                """, (
                    reviewer_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    alert_id
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    
                    self._log_verification_action(
                        alert_id, "assigned", "system", 
                        VerificationStatus.PENDING.value, 
                        VerificationStatus.PENDING.value,
                        f"Assigned to {reviewer_id}"
                    )
                    
                    logger.info(f"Alert {alert_id} assigned to {reviewer_id}")
                    return True
                else:
                    logger.warning(f"Alert {alert_id} not found or already assigned")
                    return False
                
        except Exception as e:
            logger.error(f"Failed to assign alert: {e}")
            return False
    
    def submit_verification(self, alert_id: str, reviewer_id: str,
                          is_confirmed: bool, confidence: float,
                          notes: str = "", feedback_data: Dict = None) -> bool:
        """Submit verification result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Determine new status
                if is_confirmed:
                    new_status = VerificationStatus.CONFIRMED_FAKE.value
                    result = "confirmed_fake"
                else:
                    new_status = VerificationStatus.DISMISSED.value
                    result = "dismissed"
                
                # Update verification queue
                cursor.execute("""
                    UPDATE verification_queue 
                    SET status = ?, reviewed_by = ?, reviewed_at = ?,
                        verification_result = ?, verification_confidence = ?,
                        verification_notes = ?, feedback_data = ?, updated_at = ?
                    WHERE alert_id = ?
                """, (
                    new_status,
                    reviewer_id,
                    datetime.now().isoformat(),
                    result,
                    confidence,
                    notes,
                    json.dumps(feedback_data or {}),
                    datetime.now().isoformat(),
                    alert_id
                ))
                
                conn.commit()
                
                # Log verification action
                self._log_verification_action(
                    alert_id, "verified", reviewer_id,
                    VerificationStatus.PENDING.value, new_status,
                    f"Verified as {result} with {confidence:.2f} confidence"
                )
                
                # Store model feedback for retraining
                self._store_model_feedback(alert_id, is_confirmed, confidence, feedback_data)
                
                # Update reviewer performance
                self._update_reviewer_performance(reviewer_id)
                
                # Trigger callbacks
                self._trigger_verification_callbacks(alert_id, result, confidence)
                
                logger.info(f"Verification submitted for {alert_id}: {result}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to submit verification: {e}")
            return False
    
    def _store_model_feedback(self, alert_id: str, is_confirmed: bool, 
                            confidence: float, feedback_data: Dict = None):
        """Store feedback for model retraining"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get original prediction data
                cursor.execute("""
                    SELECT detection_type, threat_score, confidence_score, auto_flagged_reason
                    FROM verification_queue WHERE alert_id = ?
                """, (alert_id,))
                
                queue_data = cursor.fetchone()
                if not queue_data:
                    return
                
                human_verdict = "fake" if is_confirmed else "legitimate"
                feedback_type = "correction" if queue_data[1] < 0.5 and is_confirmed else "confirmation"
                
                cursor.execute("""
                    INSERT INTO model_feedback 
                    (alert_id, model_prediction, model_confidence, human_verdict,
                     human_confidence, feedback_type, features_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_id,
                    queue_data[0],  # detection_type
                    queue_data[1],  # threat_score
                    human_verdict,
                    confidence,
                    feedback_type,
                    json.dumps(feedback_data or {})
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store model feedback: {e}")
    
    def _update_reviewer_performance(self, reviewer_id: str):
        """Update reviewer performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get reviewer stats
                cursor.execute("""
                    SELECT COUNT(*) as total_reviews,
                           AVG(verification_confidence) as avg_confidence
                    FROM verification_queue 
                    WHERE reviewed_by = ? AND verification_result IS NOT NULL
                """, (reviewer_id,))
                
                stats = cursor.fetchone()
                if not stats:
                    return
                
                # Update or insert performance record
                cursor.execute("""
                    INSERT OR REPLACE INTO reviewer_performance 
                    (reviewer_id, total_reviews, last_active, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    reviewer_id,
                    stats[0],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update reviewer performance: {e}")
    
    def _log_verification_action(self, alert_id: str, action: str, performed_by: str,
                               previous_status: str, new_status: str, notes: str = ""):
        """Log verification action to history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO verification_history 
                    (alert_id, action, performed_by, previous_status, new_status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (alert_id, action, performed_by, previous_status, new_status, notes))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log verification action: {e}")
    
    def register_verification_callback(self, callback_name: str, callback_func: Callable):
        """Register callback for verification events"""
        self.verification_callbacks[callback_name] = callback_func
    
    def _trigger_verification_callbacks(self, alert_id: str, result: str, confidence: float):
        """Trigger registered callbacks after verification"""
        for name, callback in self.verification_callbacks.items():
            try:
                callback(alert_id, result, confidence)
            except Exception as e:
                logger.error(f"Verification callback {name} failed: {e}")
    
    def get_model_feedback_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get model feedback data for retraining"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM model_feedback 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                feedback_data = []
                
                for row in cursor.fetchall():
                    feedback = dict(zip(columns, row))
                    try:
                        feedback['features_used'] = json.loads(feedback['features_used'] or '{}')
                    except:
                        feedback['features_used'] = {}
                    feedback_data.append(feedback)
                
                return feedback_data
                
        except Exception as e:
            logger.error(f"Failed to get model feedback data: {e}")
            return []
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification workflow statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Queue status counts
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM verification_queue 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Priority distribution
                cursor.execute("""
                    SELECT priority, COUNT(*) 
                    FROM verification_queue 
                    WHERE status = 'pending'
                    GROUP BY priority
                """)
                priority_counts = dict(cursor.fetchall())
                
                # Verification accuracy (confirmed vs dismissed)
                cursor.execute("""
                    SELECT verification_result, COUNT(*) 
                    FROM verification_queue 
                    WHERE verification_result IS NOT NULL
                    GROUP BY verification_result
                """)
                verification_results = dict(cursor.fetchall())
                
                # Average processing time
                cursor.execute("""
                    SELECT AVG(
                        (julianday(reviewed_at) - julianday(created_at)) * 24 * 60
                    ) as avg_minutes
                    FROM verification_queue 
                    WHERE reviewed_at IS NOT NULL
                """)
                avg_processing_time = cursor.fetchone()[0] or 0
                
                return {
                    "queue_status": status_counts,
                    "priority_distribution": priority_counts,
                    "verification_results": verification_results,
                    "avg_processing_time_minutes": round(avg_processing_time, 2),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get verification stats: {e}")
            return {}

# Global verification flow instance
_verification_flow = None

def get_verification_flow() -> VerificationFlow:
    """Get global verification flow instance"""
    global _verification_flow
    if _verification_flow is None:
        _verification_flow = VerificationFlow()
    return _verification_flow

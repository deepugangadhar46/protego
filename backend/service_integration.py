#!/usr/bin/env python3
"""
Service Integration Module
Integrates ML classification into the main Protego service pipeline
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import our ML components
from .ml_classifier import classify_text, is_high_risk_content
from .content_logger import save_alert

logger = logging.getLogger(__name__)

def process_incoming_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming post through ML classification pipeline
    
    Args:
        post_data: Dictionary containing post information with keys:
            - content: Post text content
            - vip_name: VIP name if mentioned (optional)
            - platform: Platform name (twitter, facebook, etc.)
            - user_id: User ID who posted
            - post_id: Unique post identifier
            - url: URL to original post
            
    Returns:
        Dictionary with processing results and actions taken
    """
    try:
        # Extract post content
        text = post_data.get("content", "")
        vip_name = post_data.get("vip_name")
        platform = post_data.get("platform", "unknown")
        
        if not text.strip():
            return {"status": "skipped", "reason": "empty_content"}
        
        # Classify the text
        result = classify_text(text)
        
        # Check if this is high-risk content
        is_high_risk = is_high_risk_content(text)
        
        # Determine if we should flag this content
        should_flag = (
            result.get("is_fake", False) or
            is_high_risk or
            result.get("confidence", 0) > 0.6
        )
        
        processing_result = {
            "status": "processed",
            "classification": result,
            "is_high_risk": is_high_risk,
            "flagged": should_flag,
            "timestamp": datetime.now().isoformat()
        }
        
        # If content should be flagged, save to database
        if should_flag:
            content_id = save_alert(
                text=text,
                result=result,
                vip_name=vip_name,
                platform=platform,
                user_id=post_data.get("user_id"),
                post_id=post_data.get("post_id"),
                url=post_data.get("url")
            )
            
            processing_result["content_id"] = content_id
            processing_result["action"] = "flagged_and_logged"
            
            # Log the flagged content
            logger.warning(f"Flagged content (ID: {content_id}): {text[:100]}...")
            
            # Additional actions for high-risk content
            if is_high_risk:
                processing_result["alert_level"] = "high"
                logger.critical(f"HIGH RISK content detected: {text[:100]}...")
                
                # Here you could add additional actions like:
                # - Send notifications to security team
                # - Trigger automated responses
                # - Escalate to human reviewers
                
        else:
            processing_result["action"] = "monitored"
        
        return processing_result
        
    except Exception as e:
        logger.error(f"Error processing post: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def batch_process_posts(posts: list) -> Dict[str, Any]:
    """
    Process multiple posts in batch
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        Summary of batch processing results
    """
    results = {
        "total_processed": 0,
        "flagged_count": 0,
        "high_risk_count": 0,
        "error_count": 0,
        "processing_time": datetime.now().isoformat()
    }
    
    for post in posts:
        try:
            result = process_incoming_post(post)
            results["total_processed"] += 1
            
            if result.get("flagged"):
                results["flagged_count"] += 1
            
            if result.get("is_high_risk"):
                results["high_risk_count"] += 1
                
        except Exception as e:
            results["error_count"] += 1
            logger.error(f"Batch processing error: {e}")
    
    return results

# Example integration functions for different platforms
def handle_twitter_post(tweet_data: Dict) -> Dict:
    """Handle Twitter post processing"""
    post_data = {
        "content": tweet_data.get("text", ""),
        "platform": "twitter",
        "user_id": tweet_data.get("user", {}).get("id"),
        "post_id": tweet_data.get("id"),
        "url": f"https://twitter.com/user/status/{tweet_data.get('id')}",
        "vip_name": extract_vip_mentions(tweet_data.get("text", ""))
    }
    
    return process_incoming_post(post_data)

def handle_facebook_post(fb_data: Dict) -> Dict:
    """Handle Facebook post processing"""
    post_data = {
        "content": fb_data.get("message", ""),
        "platform": "facebook",
        "user_id": fb_data.get("from", {}).get("id"),
        "post_id": fb_data.get("id"),
        "url": f"https://facebook.com/{fb_data.get('id')}",
        "vip_name": extract_vip_mentions(fb_data.get("message", ""))
    }
    
    return process_incoming_post(post_data)

def extract_vip_mentions(text: str) -> Optional[str]:
    """
    Extract VIP names from text (simplified implementation)
    In production, this would use a more sophisticated NER approach
    """
    # This is a placeholder - in production you'd have a list of VIPs to monitor
    vip_keywords = [
        "president", "senator", "governor", "mayor", "ceo", "celebrity"
    ]
    
    text_lower = text.lower()
    for keyword in vip_keywords:
        if keyword in text_lower:
            return keyword
    
    return None

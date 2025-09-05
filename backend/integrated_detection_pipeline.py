#!/usr/bin/env python3
"""
Integrated Detection Pipeline
Combines all detection modules with evidence storage and alerting
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import detection modules
from detection.misinformation_detector import get_misinformation_detector, analyze_misinformation
from detection.fake_profile_detector import get_fake_profile_detector, analyze_profile_suspicious
from detection.campaign_detector import get_campaign_detector, analyze_campaign_content
from detection.image_detector import get_image_detector, analyze_suspicious_image
from detection.evidence_manager import get_evidence_manager, store_detection_evidence
from detection.verification_flow import get_verification_flow
from alerting.telegram_bot import get_alerting_system, send_threat_alert

logger = logging.getLogger(__name__)

class IntegratedDetectionPipeline:
    """Main detection pipeline coordinating all detection modules"""
    
    def __init__(self):
        self.misinformation_detector = get_misinformation_detector()
        self.fake_profile_detector = get_fake_profile_detector()
        self.campaign_detector = get_campaign_detector()
        self.image_detector = get_image_detector()
        self.evidence_manager = get_evidence_manager()
        self.verification_flow = get_verification_flow()
        self.alerting_system = get_alerting_system()
        
        # Detection thresholds
        self.alert_threshold = 0.6
        self.verification_threshold = 0.4
        
        logger.info("Integrated detection pipeline initialized")
    
    def analyze_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze content through all detection modules
        
        Args:
            content_data: Content to analyze with metadata
            
        Returns:
            Combined analysis results
        """
        try:
            analysis_results = {
                "content_data": content_data,
                "timestamp": datetime.now().isoformat(),
                "detections": {},
                "overall_threat_score": 0.0,
                "max_confidence": 0.0,
                "alert_triggered": False,
                "evidence_stored": False
            }
            
            # 1. Misinformation Detection
            if content_data.get('text'):
                logger.info("Running misinformation detection...")
                misinformation_result = analyze_misinformation(
                    content_data['text'], 
                    content_data
                )
                analysis_results["detections"]["misinformation"] = misinformation_result
                
                # Update overall scores
                threat_score = misinformation_result.get('risk_assessment', {}).get('risk_score', 0.0)
                confidence = misinformation_result.get('risk_assessment', {}).get('confidence', 0.0)
                analysis_results["overall_threat_score"] = max(analysis_results["overall_threat_score"], threat_score)
                analysis_results["max_confidence"] = max(analysis_results["max_confidence"], confidence)
            
            # 2. Fake Profile Detection
            if content_data.get('username'):
                logger.info("Running fake profile detection...")
                profile_result = analyze_profile_suspicious(
                    content_data['username'],
                    content_data
                )
                analysis_results["detections"]["fake_profile"] = profile_result
                
                # Update overall scores
                threat_score = profile_result.get('risk_assessment', {}).get('risk_score', 0.0)
                confidence = profile_result.get('risk_assessment', {}).get('confidence', 0.0)
                analysis_results["overall_threat_score"] = max(analysis_results["overall_threat_score"], threat_score)
                analysis_results["max_confidence"] = max(analysis_results["max_confidence"], confidence)
            
            # 3. Campaign Detection
            if content_data.get('text'):
                logger.info("Running campaign detection...")
                campaign_result = analyze_campaign_content(
                    content_data['text'],
                    content_data
                )
                analysis_results["detections"]["campaign"] = campaign_result
                
                # Update overall scores
                threat_score = campaign_result.get('risk_assessment', {}).get('risk_score', 0.0)
                confidence = campaign_result.get('risk_assessment', {}).get('confidence', 0.0)
                analysis_results["overall_threat_score"] = max(analysis_results["overall_threat_score"], threat_score)
                analysis_results["max_confidence"] = max(analysis_results["max_confidence"], confidence)
            
            # 4. Image Detection
            image_urls = content_data.get('image_urls', [])
            if image_urls:
                logger.info("Running image detection...")
                for img_url in image_urls[:3]:  # Limit to 3 images
                    try:
                        image_result = analyze_suspicious_image(img_url, content_data)
                        if "image_analysis" not in analysis_results["detections"]:
                            analysis_results["detections"]["image_analysis"] = []
                        analysis_results["detections"]["image_analysis"].append(image_result)
                        
                        # Update overall scores
                        threat_score = image_result.get('risk_assessment', {}).get('risk_score', 0.0)
                        analysis_results["overall_threat_score"] = max(analysis_results["overall_threat_score"], threat_score)
                    except Exception as e:
                        logger.error(f"Image analysis failed for {img_url}: {e}")
            
            # 5. Determine primary detection type
            analysis_results["primary_detection_type"] = self._determine_primary_detection(analysis_results["detections"])
            
            # 6. Store evidence if threshold met
            if analysis_results["overall_threat_score"] >= self.verification_threshold:
                evidence_data = self._prepare_evidence_data(analysis_results)
                alert_id = store_detection_evidence(evidence_data)
                
                if alert_id:
                    analysis_results["alert_id"] = alert_id
                    analysis_results["evidence_stored"] = True
                    
                    # Add to verification queue
                    self.verification_flow.add_to_verification_queue({
                        "alert_id": alert_id,
                        "detection_type": analysis_results["primary_detection_type"],
                        "threat_score": analysis_results["overall_threat_score"],
                        "confidence_score": analysis_results["max_confidence"],
                        "reason_flagged": self._generate_reason_flagged(analysis_results),
                        "vip_mentioned": content_data.get('vip_mentioned')
                    })
            
            # 7. Send alert if threshold met
            if analysis_results["overall_threat_score"] >= self.alert_threshold:
                alert_data = self._prepare_alert_data(analysis_results)
                if send_threat_alert(alert_data):
                    analysis_results["alert_triggered"] = True
                    logger.warning(f"Threat alert sent for content: {analysis_results.get('alert_id', 'Unknown')}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "overall_threat_score": 0.0
            }
    
    def _determine_primary_detection(self, detections: Dict[str, Any]) -> str:
        """Determine the primary detection type based on highest threat score"""
        max_score = 0.0
        primary_type = "unknown"
        
        for detection_type, result in detections.items():
            if detection_type == "image_analysis":
                # Handle list of image results
                for img_result in result:
                    score = img_result.get('risk_assessment', {}).get('risk_score', 0.0)
                    if score > max_score:
                        max_score = score
                        primary_type = "image_manipulation"
            else:
                score = result.get('risk_assessment', {}).get('risk_score', 0.0)
                if score > max_score:
                    max_score = score
                    primary_type = detection_type
        
        return primary_type
    
    def _generate_reason_flagged(self, analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable reason for flagging"""
        reasons = []
        detections = analysis_results.get("detections", {})
        
        for detection_type, result in detections.items():
            if detection_type == "image_analysis":
                for img_result in result:
                    risk_factors = img_result.get('risk_assessment', {}).get('risk_factors', [])
                    if risk_factors:
                        reasons.extend([f"Image: {factor}" for factor in risk_factors[:2]])
            else:
                risk_factors = result.get('risk_assessment', {}).get('risk_factors', [])
                reasons.extend(risk_factors[:2])
        
        return "; ".join(reasons[:5]) if reasons else "Automated threat detection"
    
    def _prepare_evidence_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare evidence data for storage"""
        content_data = analysis_results["content_data"]
        
        return {
            "post_url": content_data.get('post_url'),
            "platform": content_data.get('platform', 'unknown'),
            "detection_type": analysis_results["primary_detection_type"],
            "reason_flagged": self._generate_reason_flagged(analysis_results),
            "raw_text": content_data.get('text', ''),
            "metadata": content_data,
            "image_urls": content_data.get('image_urls', []),
            "username": content_data.get('username'),
            "user_id": content_data.get('user_id'),
            "vip_mentioned": content_data.get('vip_mentioned'),
            "threat_score": analysis_results["overall_threat_score"],
            "confidence_score": analysis_results["max_confidence"],
            "detection_details": self._format_detection_details(analysis_results["detections"])
        }
    
    def _format_detection_details(self, detections: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format detection details for evidence storage"""
        details = []
        
        for detection_type, result in detections.items():
            if detection_type == "image_analysis":
                for i, img_result in enumerate(result):
                    details.append({
                        "type": f"image_{i+1}",
                        "data": img_result,
                        "model": "image_detector",
                        "confidence": img_result.get('risk_assessment', {}).get('risk_score', 0.0)
                    })
            else:
                details.append({
                    "type": detection_type,
                    "data": result,
                    "model": f"{detection_type}_detector",
                    "confidence": result.get('risk_assessment', {}).get('confidence', 0.0)
                })
        
        return details
    
    def _prepare_alert_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare alert data for notification"""
        content_data = analysis_results["content_data"]
        
        # Determine priority based on threat score
        threat_score = analysis_results["overall_threat_score"]
        if threat_score >= 0.9:
            priority = "critical"
        elif threat_score >= 0.75:
            priority = "high"
        elif threat_score >= 0.6:
            priority = "medium"
        else:
            priority = "low"
        
        return {
            "alert_id": analysis_results.get("alert_id", "unknown"),
            "detection_type": analysis_results["primary_detection_type"],
            "threat_score": threat_score,
            "priority": priority,
            "platform": content_data.get('platform', 'unknown'),
            "username": content_data.get('username', 'unknown'),
            "vip_mentioned": content_data.get('vip_mentioned'),
            "post_url": content_data.get('post_url'),
            "reason_flagged": self._generate_reason_flagged(analysis_results)
        }
    
    def batch_analyze(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple content items"""
        results = []
        
        for i, content_data in enumerate(content_list):
            logger.info(f"Analyzing content {i+1}/{len(content_list)}")
            try:
                result = self.analyze_content(content_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze content {i+1}: {e}")
                results.append({
                    "error": str(e),
                    "content_data": content_data,
                    "overall_threat_score": 0.0
                })
        
        return results
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        try:
            # Get stats from evidence manager
            evidence_stats = self.evidence_manager.get_evidence_summary()
            
            # Get verification stats
            verification_stats = self.verification_flow.get_verification_stats()
            
            # Get alerting stats
            alert_history = self.alerting_system.get_alert_history(100)
            
            return {
                "evidence_stats": evidence_stats,
                "verification_stats": verification_stats,
                "recent_alerts": len(alert_history),
                "pipeline_status": "active",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline stats: {e}")
            return {"error": str(e)}

# Global pipeline instance
_detection_pipeline = None

def get_detection_pipeline() -> IntegratedDetectionPipeline:
    """Get global detection pipeline instance"""
    global _detection_pipeline
    if _detection_pipeline is None:
        _detection_pipeline = IntegratedDetectionPipeline()
    return _detection_pipeline

def analyze_content_comprehensive(content_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for comprehensive content analysis
    
    Args:
        content_data: Content with metadata to analyze
        
    Returns:
        Complete analysis results
    """
    pipeline = get_detection_pipeline()
    return pipeline.analyze_content(content_data)

#!/usr/bin/env python3
"""
Protego ML Service Wrapper
Production-ready ML integration service
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ProtegoMLService:
    """Production ML service for fake content detection"""
    
    def __init__(self, config_path: str = "ml_config.json"):
        self.config = self._load_config(config_path)
        self.ml_available = False
        self.fact_check_available = False
        self._initialize_components()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Config load failed: {e}, using defaults")
            return {
                "model_settings": {"threat_threshold": 0.7},
                "api_settings": {"fact_check_timeout": 10},
                "logging": {"log_level": "INFO"}
            }
    
    def _initialize_components(self):
        """Initialize ML and fact-checking components"""
        try:
            from ml_classifier import classify_text
            self.ml_available = True
            logger.info("ML classifier initialized")
        except ImportError as e:
            logger.error(f"ML classifier unavailable: {e}")
        
        try:
            from fact_checker import enhanced_fact_check
            self.fact_check_available = True
            logger.info("Fact checker initialized")
        except ImportError as e:
            logger.error(f"Fact checker unavailable: {e}")
    
    def analyze_content(self, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Analyze content for fake news/misinformation
        
        Args:
            content: Text content to analyze
            metadata: Additional metadata (vip_name, platform, etc.)
            
        Returns:
            Analysis results with recommendations
        """
        if not content or not content.strip():
            return {"error": "Empty content", "status": "skipped"}
        
        metadata = metadata or {}
        result = {
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        # ML Classification
        if self.ml_available:
            try:
                from ml_classifier import classify_text, is_high_risk_content
                
                ml_result = classify_text(content)
                high_risk = is_high_risk_content(content)
                
                result["ml_analysis"] = {
                    "prediction": ml_result.get("prediction", "unknown"),
                    "confidence": ml_result.get("confidence", 0.0),
                    "threat_score": ml_result.get("threat_score", 0.0),
                    "is_high_risk": high_risk
                }
            except Exception as e:
                result["ml_analysis"] = {"error": str(e)}
                logger.error(f"ML analysis failed: {e}")
        
        # Fact Checking
        if self.fact_check_available and self.config.get("model_settings", {}).get("fact_check_enabled", True):
            try:
                from fact_checker import enhanced_fact_check
                
                fact_result = enhanced_fact_check(content)
                credibility = fact_result.get("credibility_analysis", {})
                
                result["fact_check"] = {
                    "has_checks": fact_result.get("has_fact_checks", False),
                    "credibility_score": credibility.get("credibility_score", 0.5),
                    "verdict": credibility.get("verdict", "unknown")
                }
            except Exception as e:
                result["fact_check"] = {"error": str(e)}
                logger.error(f"Fact check failed: {e}")
        
        # Generate recommendations
        result["recommendation"] = self._generate_recommendation(result)
        
        return result
    
    def _generate_recommendation(self, analysis: Dict) -> Dict[str, Any]:
        """Generate action recommendation based on analysis"""
        ml = analysis.get("ml_analysis", {})
        fc = analysis.get("fact_check", {})
        
        threat_threshold = self.config.get("model_settings", {}).get("threat_threshold", 0.7)
        
        # Calculate combined risk score
        ml_threat = ml.get("threat_score", 0.0)
        fc_threat = 1.0 - fc.get("credibility_score", 0.5)
        
        if fc.get("has_checks", False):
            combined_risk = (ml_threat * 0.6) + (fc_threat * 0.4)
        else:
            combined_risk = ml_threat
        
        # Determine action
        if combined_risk >= threat_threshold:
            action = "flag_content"
            priority = "high"
        elif ml.get("is_high_risk", False):
            action = "review_content"
            priority = "medium"
        else:
            action = "monitor"
            priority = "low"
        
        return {
            "action": action,
            "priority": priority,
            "risk_score": combined_risk,
            "should_alert": combined_risk >= threat_threshold
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and health check"""
        return {
            "service": "Protego ML Service",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "ml_classifier": self.ml_available,
                "fact_checker": self.fact_check_available
            },
            "config": self.config
        }

# Global service instance
_service = None

def get_ml_service() -> ProtegoMLService:
    """Get global ML service instance"""
    global _service
    if _service is None:
        _service = ProtegoMLService()
    return _service

def analyze_content(content: str, **metadata) -> Dict[str, Any]:
    """Convenience function for content analysis"""
    service = get_ml_service()
    return service.analyze_content(content, metadata)

if __name__ == "__main__":
    # Demo service usage
    service = ProtegoMLService()
    
    print("🚀 Protego ML Service Demo")
    print("=" * 40)
    
    # Test single content
    test_content = "Breaking: VIP politician caught in major scandal"
    result = service.analyze_content(test_content, {"platform": "twitter"})
    
    print(f"Content: {result['content_preview']}")
    print(f"ML Prediction: {result.get('ml_analysis', {}).get('prediction', 'N/A')}")
    print(f"Recommendation: {result.get('recommendation', {}).get('action', 'N/A')}")
    print(f"Risk Score: {result.get('recommendation', {}).get('risk_score', 0):.3f}")
    
    # Service status
    status = service.get_service_status()
    print(f"\nService Status: {status['status']}")
    print(f"Components: {status['components']}")
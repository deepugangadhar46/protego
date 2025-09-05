#!/usr/bin/env python3
"""
ML Classifier Module for Protego System
Provides simple classification functions for service integration
"""

import os
import logging
import joblib
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ThreatClassifier:
    """Simple threat classifier using trained models"""
    
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.is_loaded = False
        self._load_models()
    
    def _load_models(self):
        """Load trained models from backend/monitoring/"""
        try:
            vectorizer_path = "backend/monitoring/tfidf_vectorizer.joblib"
            model_path = "backend/monitoring/threat_model.joblib"
            
            if os.path.exists(vectorizer_path) and os.path.exists(model_path):
                self.vectorizer = joblib.load(vectorizer_path)
                self.model = joblib.load(model_path)
                self.is_loaded = True
                logger.info("ML models loaded successfully")
            else:
                logger.warning("Model files not found. Run demo_ml_pipeline.py first")
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    def classify_text(self, text: str) -> Dict:
        """
        Classify text content for fake news/misinformation
        
        Args:
            text: Content to classify
            
        Returns:
            Dict with prediction results
        """
        if not self.is_loaded:
            return {
                "error": "Models not loaded",
                "prediction": "unknown",
                "confidence": 0.0
            }
        
        try:
            # Transform text using TF-IDF vectorizer
            X = self.vectorizer.transform([text])
            
            # Make prediction
            pred = self.model.predict(X)[0]
            prob = max(self.model.predict_proba(X)[0])
            
            # Convert prediction to readable format
            prediction = "real" if pred == 1 else "fake"
            
            return {
                "prediction": prediction,
                "confidence": float(prob),
                "is_fake": pred == 0,
                "is_real": pred == 1,
                "threat_score": float(1 - pred) * prob,  # Higher if fake and confident
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "error": str(e),
                "prediction": "unknown",
                "confidence": 0.0
            }

# Global classifier instance
_classifier = None

def get_classifier() -> ThreatClassifier:
    """Get global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = ThreatClassifier()
    return _classifier

def classify_text(text: str) -> Dict:
    """
    Convenience function for text classification
    
    Args:
        text: Content to classify
        
    Returns:
        Classification results
    """
    classifier = get_classifier()
    return classifier.classify_text(text)

def is_high_risk_content(text: str, threshold: float = 0.7) -> bool:
    """
    Check if content is high-risk fake news/misinformation
    
    Args:
        text: Content to check
        threshold: Confidence threshold for high-risk classification
        
    Returns:
        True if content is high-risk
    """
    result = classify_text(text)
    
    if "error" in result:
        return False
    
    return result["is_fake"] and result["confidence"] >= threshold

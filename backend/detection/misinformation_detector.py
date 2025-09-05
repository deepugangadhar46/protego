#!/usr/bin/env python3
"""
Phase 1: Misinformation/Fake Content Detection
Enhanced NLP with HuggingFace classifiers and fact-checking
"""

import os
import logging
import spacy
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
from transformers import pipeline

# Import existing components
try:
    from ..fact_checker import enhanced_fact_check
    from ..ml_classifier import classify_text
    FACT_CHECK_AVAILABLE = True
except ImportError:
    FACT_CHECK_AVAILABLE = False

logger = logging.getLogger(__name__)

class MisinformationDetector:
    """Advanced misinformation detection using multiple NLP approaches"""
    
    def __init__(self):
        self.nlp = None
        self.fake_news_classifier = None
        self.misinfo_classifier = None
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models and classifiers"""
        try:
            # Load spaCy for NER
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("SpaCy NER model loaded")
            except OSError:
                logger.warning("SpaCy model not found. Install with: python -m spacy download en_core_web_sm")
            
            # Load HuggingFace fake news classifier
            try:
                self.fake_news_classifier = pipeline(
                    "text-classification",
                    model="mrm8488/bert-tiny-finetuned-fake-news"
                )
                logger.info("Fake news classifier loaded")
            except Exception as e:
                logger.warning(f"Failed to load fake news classifier: {e}")
            
            # Load misinformation classifier
            try:
                self.misinfo_classifier = pipeline(
                    "text-classification",
                    model="jy46604790/Fake-News-Bert-Detect"
                )
                logger.info("Misinformation classifier loaded")
            except Exception as e:
                logger.warning(f"Failed to load misinformation classifier: {e}")
                
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
    
    def extract_entities_and_claims(self, text: str) -> Dict[str, Any]:
        """Extract named entities and identify potential claims"""
        result = {
            "entities": [],
            "vip_mentions": [],
            "claim_indicators": [],
            "news_keywords": []
        }
        
        if not self.nlp:
            return result
        
        try:
            doc = self.nlp(text)
            
            # Extract entities
            for ent in doc.ents:
                entity_info = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
                result["entities"].append(entity_info)
                
                # Identify VIP-related entities
                if ent.label_ in ["PERSON", "ORG"]:
                    result["vip_mentions"].append(entity_info)
            
            # Identify claim indicators
            claim_patterns = [
                "breaking", "exclusive", "confirmed", "revealed", "exposed",
                "according to", "sources say", "leaked", "insider",
                "study shows", "research proves", "scientists discover"
            ]
            
            text_lower = text.lower()
            for pattern in claim_patterns:
                if pattern in text_lower:
                    result["claim_indicators"].append(pattern)
            
            # News-related keywords
            news_keywords = [
                "scandal", "controversy", "investigation", "arrest",
                "resignation", "election", "policy", "statement"
            ]
            
            for keyword in news_keywords:
                if keyword in text_lower:
                    result["news_keywords"].append(keyword)
                    
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
        
        return result
    
    def classify_misinformation(self, text: str) -> Dict[str, Any]:
        """Classify text using multiple misinformation models"""
        results = {
            "fake_news_score": 0.0,
            "misinfo_score": 0.0,
            "baseline_score": 0.0,
            "combined_score": 0.0,
            "verdict": "unknown",
            "confidence": 0.0,
            "model_results": {}
        }
        
        scores = []
        weights = []
        
        # HuggingFace fake news classifier
        if self.fake_news_classifier:
            try:
                result = self.fake_news_classifier(text[:512])
                fake_score = result[0]['score'] if result[0]['label'] == 'FAKE' else 1 - result[0]['score']
                results["fake_news_score"] = fake_score
                results["model_results"]["fake_news"] = result[0]
                scores.append(fake_score)
                weights.append(0.3)
            except Exception as e:
                logger.error(f"Fake news classification failed: {e}")
        
        # Misinformation classifier
        if self.misinfo_classifier:
            try:
                result = self.misinfo_classifier(text[:512])
                # Adjust based on model's label format
                misinfo_score = result[0]['score'] if 'fake' in result[0]['label'].lower() else 1 - result[0]['score']
                results["misinfo_score"] = misinfo_score
                results["model_results"]["misinformation"] = result[0]
                scores.append(misinfo_score)
                weights.append(0.3)
            except Exception as e:
                logger.error(f"Misinformation classification failed: {e}")
        
        # Baseline classifier (if available)
        try:
            baseline_result = classify_text(text)
            if "error" not in baseline_result:
                baseline_score = 1 - baseline_result.get("prediction", 1)  # Convert to fake score
                results["baseline_score"] = baseline_score
                results["model_results"]["baseline"] = baseline_result
                scores.append(baseline_score)
                weights.append(0.4)
        except Exception as e:
            logger.error(f"Baseline classification failed: {e}")
        
        # Calculate combined score
        if scores and weights:
            total_weight = sum(weights)
            combined_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            results["combined_score"] = combined_score
            results["confidence"] = min(len(scores) / 3.0, 1.0)  # Higher confidence with more models
            
            # Determine verdict
            if combined_score > 0.7:
                results["verdict"] = "likely_fake"
            elif combined_score > 0.4:
                results["verdict"] = "suspicious"
            else:
                results["verdict"] = "likely_real"
        
        return results
    
    def cross_check_with_news_api(self, claim: str, vip_name: str = None) -> Dict[str, Any]:
        """Cross-check claims with NewsAPI for verification"""
        if not self.news_api_key:
            return {"error": "NewsAPI key not configured"}
        
        try:
            # Build search query
            query = claim[:100]  # Limit query length
            if vip_name:
                query = f'"{vip_name}" {query}'
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "relevancy",
                "pageSize": 10,
                "apiKey": self.news_api_key,
                "language": "en"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                return {
                    "found_articles": len(articles) > 0,
                    "article_count": len(articles),
                    "articles": articles[:5],  # Return top 5
                    "credible_sources": self._count_credible_sources(articles),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"NewsAPI error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"NewsAPI check failed: {e}")
            return {"error": str(e)}
    
    def _count_credible_sources(self, articles: List[Dict]) -> int:
        """Count articles from credible news sources"""
        credible_domains = [
            "reuters.com", "ap.org", "bbc.com", "cnn.com", "nytimes.com",
            "washingtonpost.com", "theguardian.com", "npr.org", "pbs.org"
        ]
        
        count = 0
        for article in articles:
            source_url = article.get("url", "")
            if any(domain in source_url for domain in credible_domains):
                count += 1
        
        return count
    
    def comprehensive_analysis(self, text: str, vip_name: str = None) -> Dict[str, Any]:
        """Run comprehensive misinformation analysis"""
        analysis = {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "vip_name": vip_name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract entities and claims
        analysis["entities"] = self.extract_entities_and_claims(text)
        
        # Classify misinformation
        analysis["classification"] = self.classify_misinformation(text)
        
        # Fact-check if available
        if FACT_CHECK_AVAILABLE:
            try:
                analysis["fact_check"] = enhanced_fact_check(text)
            except Exception as e:
                analysis["fact_check"] = {"error": str(e)}
        
        # News API cross-check for claims
        if analysis["entities"]["claim_indicators"]:
            analysis["news_verification"] = self.cross_check_with_news_api(text, vip_name)
        
        # Calculate final risk score
        analysis["risk_assessment"] = self._calculate_risk_score(analysis)
        
        return analysis
    
    def _calculate_risk_score(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk score from all analyses"""
        risk_factors = []
        
        # Classification score
        classification = analysis.get("classification", {})
        combined_score = classification.get("combined_score", 0.0)
        risk_factors.append(("classification", combined_score, 0.4))
        
        # Fact-check score
        fact_check = analysis.get("fact_check", {})
        if "credibility_analysis" in fact_check:
            credibility = 1.0 - fact_check["credibility_analysis"].get("credibility_score", 0.5)
            risk_factors.append(("fact_check", credibility, 0.3))
        
        # News verification
        news_check = analysis.get("news_verification", {})
        if "found_articles" in news_check:
            # Lower risk if found in credible sources
            credible_ratio = news_check.get("credible_sources", 0) / max(news_check.get("article_count", 1), 1)
            news_risk = 1.0 - credible_ratio
            risk_factors.append(("news_verification", news_risk, 0.2))
        
        # Entity-based risk
        entities = analysis.get("entities", {})
        claim_risk = min(len(entities.get("claim_indicators", [])) * 0.2, 1.0)
        risk_factors.append(("claims", claim_risk, 0.1))
        
        # Calculate weighted risk score
        total_weight = sum(weight for _, _, weight in risk_factors)
        if total_weight > 0:
            risk_score = sum(score * weight for _, score, weight in risk_factors) / total_weight
        else:
            risk_score = 0.5
        
        # Determine risk level
        if risk_score > 0.8:
            risk_level = "critical"
        elif risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": [{"source": source, "score": score, "weight": weight} 
                           for source, score, weight in risk_factors],
            "requires_action": risk_score > 0.6
        }

# Global detector instance
_detector = None

def get_misinformation_detector() -> MisinformationDetector:
    """Get global misinformation detector instance"""
    global _detector
    if _detector is None:
        _detector = MisinformationDetector()
    return _detector

def analyze_misinformation(text: str, vip_name: str = None) -> Dict[str, Any]:
    """
    Convenience function for misinformation analysis
    
    Args:
        text: Text content to analyze
        vip_name: VIP name if mentioned
        
    Returns:
        Comprehensive misinformation analysis
    """
    detector = get_misinformation_detector()
    return detector.comprehensive_analysis(text, vip_name)

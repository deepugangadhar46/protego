#!/usr/bin/env python3
"""
Fact Checker Integration for Protego System
Integrates Google Fact Check Tools API with ML pipeline
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FactChecker:
    """Google Fact Check Tools API integration"""
    
    def __init__(self):
        self.api_key = os.getenv("FACT_CHECK_API_KEY")
        self.base_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        
        if not self.api_key:
            logger.warning("FACT_CHECK_API_KEY not found in environment variables")
    
    def fact_check_claim(self, claim: str) -> Dict[str, Any]:
        """
        Check a claim against Google Fact Check Tools API
        
        Args:
            claim: Text claim to fact-check
            
        Returns:
            Dictionary with fact-check results
        """
        if not self.api_key:
            return {
                "error": "API key not configured",
                "has_fact_checks": False,
                "claims": []
            }
        
        try:
            params = {
                "query": claim,
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "claims" in data and data["claims"]:
                    return {
                        "has_fact_checks": True,
                        "claims": data["claims"],
                        "total_results": len(data["claims"]),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "has_fact_checks": False,
                        "claims": [],
                        "message": "No fact-check results found",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "error": f"API Error: {response.status_code}",
                    "message": response.text,
                    "has_fact_checks": False,
                    "claims": []
                }
                
        except requests.RequestException as e:
            logger.error(f"Fact-check API request failed: {e}")
            return {
                "error": f"Request failed: {str(e)}",
                "has_fact_checks": False,
                "claims": []
            }
        except Exception as e:
            logger.error(f"Fact-check error: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "has_fact_checks": False,
                "claims": []
            }
    
    def analyze_fact_check_results(self, fact_check_data: Dict) -> Dict[str, Any]:
        """
        Analyze fact-check results to determine credibility
        
        Args:
            fact_check_data: Results from fact_check_claim()
            
        Returns:
            Analysis of fact-check credibility
        """
        if not fact_check_data.get("has_fact_checks"):
            return {
                "credibility_score": 0.5,  # Neutral when no fact-checks available
                "verdict": "unknown",
                "confidence": 0.0,
                "analysis": "No fact-check data available"
            }
        
        claims = fact_check_data.get("claims", [])
        verdicts = []
        
        # Extract verdicts from fact-check results
        for claim in claims:
            claim_review = claim.get("claimReview", [])
            for review in claim_review:
                rating = review.get("textualRating", "").lower()
                verdicts.append(rating)
        
        if not verdicts:
            return {
                "credibility_score": 0.5,
                "verdict": "unknown",
                "confidence": 0.0,
                "analysis": "No ratings found in fact-check results"
            }
        
        # Analyze verdicts
        false_indicators = ["false", "fake", "misleading", "incorrect", "debunked"]
        true_indicators = ["true", "correct", "accurate", "verified"]
        
        false_count = sum(1 for v in verdicts if any(fi in v for fi in false_indicators))
        true_count = sum(1 for v in verdicts if any(ti in v for ti in true_indicators))
        
        total_verdicts = len(verdicts)
        
        if false_count > true_count:
            credibility_score = max(0.1, 1.0 - (false_count / total_verdicts))
            verdict = "likely_false"
        elif true_count > false_count:
            credibility_score = min(0.9, 0.5 + (true_count / total_verdicts) * 0.4)
            verdict = "likely_true"
        else:
            credibility_score = 0.5
            verdict = "mixed"
        
        confidence = min(total_verdicts / 3.0, 1.0)  # Higher confidence with more sources
        
        return {
            "credibility_score": credibility_score,
            "verdict": verdict,
            "confidence": confidence,
            "analysis": f"Based on {total_verdicts} fact-check sources",
            "false_count": false_count,
            "true_count": true_count,
            "verdicts": verdicts[:5]  # Limit to first 5 verdicts
        }
    
    def enhanced_claim_analysis(self, text: str) -> Dict[str, Any]:
        """
        Complete fact-check analysis combining API results with local analysis
        
        Args:
            text: Text to analyze for claims
            
        Returns:
            Comprehensive fact-check analysis
        """
        # Get fact-check results
        fact_check_results = self.fact_check_claim(text)
        
        # Analyze the results
        credibility_analysis = self.analyze_fact_check_results(fact_check_results)
        
        # Combine with basic claim detection
        claim_indicators = self._detect_claim_indicators(text)
        
        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "fact_check_results": fact_check_results,
            "credibility_analysis": credibility_analysis,
            "claim_indicators": claim_indicators,
            "timestamp": datetime.now().isoformat(),
            "requires_verification": (
                credibility_analysis["verdict"] in ["likely_false", "mixed"] or
                claim_indicators["has_strong_claims"]
            )
        }
    
    def _detect_claim_indicators(self, text: str) -> Dict[str, Any]:
        """Detect indicators that suggest factual claims"""
        text_lower = text.lower()
        
        # Strong claim indicators
        strong_indicators = [
            "breaking", "exclusive", "confirmed", "proven", "fact", "study shows",
            "research reveals", "scientists discover", "experts say", "according to"
        ]
        
        # Weak claim indicators
        weak_indicators = [
            "allegedly", "reportedly", "claims", "suggests", "appears", "seems",
            "rumor", "unconfirmed", "speculation"
        ]
        
        # Sensational indicators
        sensational_indicators = [
            "shocking", "incredible", "unbelievable", "amazing", "secret",
            "hidden", "exposed", "revealed", "scandal"
        ]
        
        strong_count = sum(1 for indicator in strong_indicators if indicator in text_lower)
        weak_count = sum(1 for indicator in weak_indicators if indicator in text_lower)
        sensational_count = sum(1 for indicator in sensational_indicators if indicator in text_lower)
        
        has_strong_claims = strong_count > 0 or (sensational_count > 1)
        
        return {
            "has_strong_claims": has_strong_claims,
            "strong_indicators": strong_count,
            "weak_indicators": weak_count,
            "sensational_indicators": sensational_count,
            "claim_strength": "high" if strong_count > 1 else "medium" if strong_count > 0 else "low"
        }

# Global fact checker instance
_fact_checker = None

def get_fact_checker() -> FactChecker:
    """Get global fact checker instance"""
    global _fact_checker
    if _fact_checker is None:
        _fact_checker = FactChecker()
    return _fact_checker

def fact_check_claim(claim: str) -> Dict[str, Any]:
    """
    Convenience function for fact-checking
    
    Args:
        claim: Text claim to fact-check
        
    Returns:
        Fact-check results
    """
    checker = get_fact_checker()
    return checker.fact_check_claim(claim)

def enhanced_fact_check(text: str) -> Dict[str, Any]:
    """
    Enhanced fact-checking with credibility analysis
    
    Args:
        text: Text to analyze
        
    Returns:
        Complete fact-check analysis
    """
    checker = get_fact_checker()
    return checker.enhanced_claim_analysis(text)

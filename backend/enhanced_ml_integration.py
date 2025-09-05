#!/usr/bin/env python3
"""
Enhanced ML Integration with Fact-Checking
Combines ML classification with Google Fact Check Tools API
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ml_classifier import classify_text, is_high_risk_content
    from fact_checker import enhanced_fact_check, get_fact_checker
    from content_logger import save_alert
    ML_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ML components not available: {e}")
    ML_AVAILABLE = False

def enhanced_content_analysis(text: str, vip_name: str = None, platform: str = None) -> Dict[str, Any]:
    """
    Complete content analysis combining ML and fact-checking
    
    Args:
        text: Content to analyze
        vip_name: VIP name if mentioned
        platform: Platform where content was found
        
    Returns:
        Comprehensive analysis results
    """
    analysis_result = {
        "text": text[:200] + "..." if len(text) > 200 else text,
        "timestamp": datetime.now().isoformat(),
        "vip_name": vip_name,
        "platform": platform
    }
    
    # ML Classification
    if ML_AVAILABLE:
        try:
            ml_result = classify_text(text)
            high_risk = is_high_risk_content(text)
            
            analysis_result["ml_classification"] = {
                "prediction": ml_result.get("prediction", "unknown"),
                "confidence": ml_result.get("confidence", 0.0),
                "is_fake": ml_result.get("is_fake", False),
                "is_real": ml_result.get("is_real", False),
                "threat_score": ml_result.get("threat_score", 0.0),
                "high_risk": high_risk
            }
        except Exception as e:
            analysis_result["ml_classification"] = {"error": str(e)}
    
    # Fact-checking
    try:
        fact_check_result = enhanced_fact_check(text)
        credibility = fact_check_result.get("credibility_analysis", {})
        
        analysis_result["fact_check"] = {
            "has_fact_checks": fact_check_result.get("has_fact_checks", False),
            "credibility_score": credibility.get("credibility_score", 0.5),
            "verdict": credibility.get("verdict", "unknown"),
            "confidence": credibility.get("confidence", 0.0),
            "requires_verification": fact_check_result.get("requires_verification", False),
            "claim_indicators": fact_check_result.get("claim_indicators", {})
        }
    except Exception as e:
        analysis_result["fact_check"] = {"error": str(e)}
    
    # Combined assessment
    analysis_result["combined_assessment"] = _create_combined_assessment(analysis_result)
    
    return analysis_result

def _create_combined_assessment(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create combined assessment from ML and fact-check results"""
    ml = analysis.get("ml_classification", {})
    fc = analysis.get("fact_check", {})
    
    # Calculate combined threat score
    ml_threat = ml.get("threat_score", 0.0)
    fc_threat = 1.0 - fc.get("credibility_score", 0.5)  # Lower credibility = higher threat
    
    # Weight ML more heavily if fact-check unavailable
    if fc.get("has_fact_checks", False):
        combined_threat = (ml_threat * 0.6) + (fc_threat * 0.4)
    else:
        combined_threat = ml_threat * 0.8
    
    # Determine overall verdict
    ml_fake = ml.get("is_fake", False)
    fc_suspicious = fc.get("verdict") in ["likely_false", "mixed"]
    
    if ml_fake and fc_suspicious:
        verdict = "high_confidence_fake"
        action = "immediate_flag"
    elif ml_fake or fc_suspicious:
        verdict = "likely_fake"
        action = "flag_for_review"
    elif ml.get("high_risk", False):
        verdict = "high_risk"
        action = "monitor_closely"
    else:
        verdict = "low_risk"
        action = "routine_monitoring"
    
    return {
        "combined_threat_score": combined_threat,
        "verdict": verdict,
        "recommended_action": action,
        "confidence": min(ml.get("confidence", 0.5), fc.get("confidence", 0.5)),
        "should_flag": combined_threat > 0.6 or verdict in ["high_confidence_fake", "likely_fake"]
    }

def process_content_with_fact_check(content_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process content through enhanced pipeline with fact-checking
    
    Args:
        content_data: Content information dictionary
        
    Returns:
        Processing results with actions taken
    """
    text = content_data.get("content", "")
    vip_name = content_data.get("vip_name")
    platform = content_data.get("platform", "unknown")
    
    if not text.strip():
        return {"status": "skipped", "reason": "empty_content"}
    
    # Run enhanced analysis
    analysis = enhanced_content_analysis(text, vip_name, platform)
    
    # Determine actions based on combined assessment
    assessment = analysis.get("combined_assessment", {})
    should_flag = assessment.get("should_flag", False)
    
    result = {
        "status": "processed",
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }
    
    # Take action if content should be flagged
    if should_flag:
        try:
            # Create result for logging
            log_result = {
                "prediction": assessment["verdict"],
                "confidence": assessment["confidence"],
                "threat_score": assessment["combined_threat_score"],
                "is_fake": analysis.get("ml_classification", {}).get("is_fake", False),
                "model_type": "enhanced_ml_factcheck"
            }
            
            # Save to database
            content_id = save_alert(
                text=text,
                result=log_result,
                vip_name=vip_name,
                platform=platform,
                **{k: v for k, v in content_data.items() if k not in ["content", "vip_name", "platform"]}
            )
            
            result["flagged"] = True
            result["content_id"] = content_id
            result["action"] = assessment["recommended_action"]
            
        except Exception as e:
            result["error"] = f"Failed to save alert: {e}"
    else:
        result["flagged"] = False
        result["action"] = "monitored"
    
    return result

def demo_enhanced_integration():
    """Demonstrate enhanced ML + fact-check integration"""
    print("🚀 Enhanced ML + Fact-Check Integration Demo")
    print("=" * 60)
    
    test_cases = [
        {
            "content": "Breaking: VIP politician caught in major corruption scandal",
            "vip_name": "politician",
            "platform": "twitter"
        },
        {
            "content": "Elon Musk bought Google for $500 billion yesterday",
            "platform": "facebook"
        },
        {
            "content": "President announces new healthcare policy in official statement",
            "vip_name": "president",
            "platform": "news"
        },
        {
            "content": "FAKE: Celebrity seen with aliens in secret meeting",
            "vip_name": "celebrity",
            "platform": "twitter"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Processing: {case['content'][:50]}...")
        print("-" * 40)
        
        result = process_content_with_fact_check(case)
        analysis = result.get("analysis", {})
        
        # ML results
        ml = analysis.get("ml_classification", {})
        if "error" not in ml:
            print(f"📊 ML: {ml.get('prediction', 'unknown')} (confidence: {ml.get('confidence', 0):.3f})")
        
        # Fact-check results
        fc = analysis.get("fact_check", {})
        if "error" not in fc:
            print(f"✅ Fact-check: {fc.get('verdict', 'unknown')} (credibility: {fc.get('credibility_score', 0):.3f})")
        
        # Combined assessment
        assessment = analysis.get("combined_assessment", {})
        print(f"🎯 Combined: {assessment.get('verdict', 'unknown')} (threat: {assessment.get('combined_threat_score', 0):.3f})")
        print(f"🚨 Action: {result.get('action', 'none')}")
        
        if result.get("flagged"):
            print(f"💾 Flagged with ID: {result.get('content_id', 'N/A')}")
    
    print(f"\n🎉 Enhanced Integration Demo Complete!")

if __name__ == "__main__":
    demo_enhanced_integration()

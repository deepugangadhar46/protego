#!/usr/bin/env python3
"""
Complete Integration Test for Protego ML System
Tests all components: ML classification, fact-checking, content logging
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ml_classifier():
    """Test ML classifier functionality"""
    print("🧪 Testing ML Classifier...")
    
    try:
        from ml_classifier import classify_text, is_high_risk_content
        
        test_text = "Breaking: VIP politician caught in major corruption scandal"
        result = classify_text(test_text)
        
        print(f"   ✅ Classification result: {result.get('prediction', 'unknown')}")
        print(f"   📊 Confidence: {result.get('confidence', 0):.3f}")
        print(f"   🚨 High risk: {is_high_risk_content(test_text)}")
        
        return True, result
        
    except Exception as e:
        print(f"   ❌ ML Classifier error: {e}")
        return False, None

def test_fact_checker():
    """Test fact-checking functionality"""
    print("\n🔍 Testing Fact Checker...")
    
    try:
        from fact_checker import enhanced_fact_check
        
        test_text = "Elon Musk bought Google for $500 billion yesterday"
        result = enhanced_fact_check(test_text)
        
        credibility = result.get('credibility_analysis', {})
        print(f"   ✅ Has fact checks: {result.get('has_fact_checks', False)}")
        print(f"   📊 Credibility score: {credibility.get('credibility_score', 0.5):.3f}")
        print(f"   🎯 Verdict: {credibility.get('verdict', 'unknown')}")
        
        return True, result
        
    except Exception as e:
        print(f"   ❌ Fact Checker error: {e}")
        return False, None

def test_enhanced_integration():
    """Test enhanced ML + fact-check integration"""
    print("\n🚀 Testing Enhanced Integration...")
    
    try:
        from enhanced_ml_integration import enhanced_content_analysis, process_content_with_fact_check
        
        test_content = {
            "content": "FAKE: Celebrity seen with aliens in secret meeting",
            "vip_name": "celebrity",
            "platform": "twitter"
        }
        
        # Test content analysis
        analysis = enhanced_content_analysis(
            test_content["content"], 
            test_content["vip_name"], 
            test_content["platform"]
        )
        
        # Test full processing
        result = process_content_with_fact_check(test_content)
        
        assessment = analysis.get("combined_assessment", {})
        print(f"   ✅ Combined verdict: {assessment.get('verdict', 'unknown')}")
        print(f"   📊 Threat score: {assessment.get('combined_threat_score', 0):.3f}")
        print(f"   🚨 Should flag: {assessment.get('should_flag', False)}")
        print(f"   🎯 Action: {result.get('action', 'none')}")
        
        return True, result
        
    except Exception as e:
        print(f"   ❌ Enhanced Integration error: {e}")
        return False, None

def test_content_logger():
    """Test content logging functionality"""
    print("\n💾 Testing Content Logger...")
    
    try:
        from content_logger import save_alert
        
        test_result = {
            "prediction": "fake",
            "confidence": 0.85,
            "threat_score": 0.75,
            "is_fake": True,
            "model_type": "test_integration"
        }
        
        content_id = save_alert(
            text="Test content for logging",
            result=test_result,
            vip_name="test_vip",
            platform="test_platform"
        )
        
        print(f"   ✅ Content saved with ID: {content_id}")
        return True, content_id
        
    except Exception as e:
        print(f"   ❌ Content Logger error: {e}")
        return False, None

def run_complete_integration_test():
    """Run complete integration test suite"""
    print("🎯 Protego ML System - Complete Integration Test")
    print("=" * 60)
    
    results = {}
    
    # Test individual components
    ml_success, ml_result = test_ml_classifier()
    results["ml_classifier"] = {"success": ml_success, "result": ml_result}
    
    fact_success, fact_result = test_fact_checker()
    results["fact_checker"] = {"success": fact_success, "result": fact_result}
    
    integration_success, integration_result = test_enhanced_integration()
    results["enhanced_integration"] = {"success": integration_success, "result": integration_result}
    
    logger_success, logger_result = test_content_logger()
    results["content_logger"] = {"success": logger_success, "result": logger_result}
    
    # Summary
    print("\n📊 Integration Test Summary")
    print("=" * 40)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    for component, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {component}: {status}")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n🚀 Ready for production deployment:")
        print("   - ML classification: ✅")
        print("   - Fact-checking: ✅") 
        print("   - Enhanced integration: ✅")
        print("   - Content logging: ✅")
    else:
        print("⚠️ Some components need attention")
        print("\n🔧 Next steps:")
        for component, result in results.items():
            if not result["success"]:
                print(f"   - Fix {component}")
    
    return results

def run_end_to_end_demo():
    """Run end-to-end demo with real content"""
    print("\n🎬 End-to-End Demo")
    print("=" * 30)
    
    demo_contents = [
        {
            "content": "Breaking: VIP politician announces resignation amid scandal",
            "vip_name": "politician",
            "platform": "twitter",
            "description": "Political news"
        },
        {
            "content": "URGENT: Government plans to ban all social media platforms tomorrow",
            "platform": "facebook", 
            "description": "Suspicious claim"
        },
        {
            "content": "Scientists publish new research on renewable energy efficiency",
            "platform": "news",
            "description": "Legitimate news"
        }
    ]
    
    try:
        from enhanced_ml_integration import process_content_with_fact_check
        
        for i, content in enumerate(demo_contents, 1):
            print(f"\n{i}. {content['description']}")
            print(f"   Content: {content['content'][:50]}...")
            print("-" * 30)
            
            result = process_content_with_fact_check(content)
            analysis = result.get("analysis", {})
            assessment = analysis.get("combined_assessment", {})
            
            print(f"   🎯 Verdict: {assessment.get('verdict', 'unknown')}")
            print(f"   📊 Threat: {assessment.get('combined_threat_score', 0):.3f}")
            print(f"   🚨 Flagged: {result.get('flagged', False)}")
            print(f"   🎬 Action: {result.get('action', 'none')}")
            
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Complete Integration Test...")
    print("This will test all Protego ML components:")
    print("1. ML Classifier")
    print("2. Fact Checker") 
    print("3. Enhanced Integration")
    print("4. Content Logger")
    print("5. End-to-End Demo")
    print()
    
    # Run integration tests
    results = run_complete_integration_test()
    
    # Run end-to-end demo
    run_end_to_end_demo()
    
    print(f"\n🎉 Complete Integration Test Finished!")
    print("=" * 50)

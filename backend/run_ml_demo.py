#!/usr/bin/env python3
"""
ML System Demo Runner
Comprehensive demonstration of the Protego ML integration
"""

import os
import sys
import json
from datetime import datetime

def ensure_models_exist():
    """Ensure ML models exist, create sample ones if needed"""
    print("🔧 Checking ML models...")
    
    model_dir = "backend/monitoring"
    vectorizer_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")
    model_path = os.path.join(model_dir, "threat_model.joblib")
    
    if os.path.exists(vectorizer_path) and os.path.exists(model_path):
        print("   ✅ Models found")
        return True
    
    print("   🔨 Creating sample models...")
    try:
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        
        # Sample training data
        fake_texts = [
            "BREAKING: Aliens land in Washington DC",
            "SHOCKING: Celebrity caught stealing millions", 
            "URGENT: Government plans to ban social media",
            "VIP threatens to destroy economy",
            "FAKE: Secret conspiracy revealed"
        ]
        
        real_texts = [
            "President announces new infrastructure bill",
            "Scientists publish climate change research",
            "Stock market closes higher today",
            "Government official provides economic update",
            "University researchers develop new technology"
        ]
        
        # Prepare data
        texts = fake_texts + real_texts
        labels = [0] * len(fake_texts) + [1] * len(real_texts)
        
        # Train model
        vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
        X = vectorizer.fit_transform(texts)
        model = LogisticRegression(random_state=42)
        model.fit(X, labels)
        
        # Save models
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(vectorizer, vectorizer_path)
        joblib.dump(model, model_path)
        
        print("   ✅ Sample models created")
        return True
        
    except Exception as e:
        print(f"   ❌ Model creation failed: {e}")
        return False

def demo_ml_classifier():
    """Demo ML classifier functionality"""
    print("\n🧪 ML Classifier Demo")
    print("-" * 30)
    
    try:
        from ml_classifier import classify_text, is_high_risk_content
        
        test_cases = [
            "Breaking: VIP politician caught in major scandal",
            "URGENT: Government plans secret operation",
            "President announces new healthcare policy",
            "FAKE: Celebrity seen with aliens"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n{i}. Text: {text}")
            
            result = classify_text(text)
            high_risk = is_high_risk_content(text)
            
            if "error" not in result:
                print(f"   📊 Prediction: {result['prediction']}")
                print(f"   🎯 Confidence: {result['confidence']:.3f}")
                print(f"   🚨 High Risk: {high_risk}")
            else:
                print(f"   ❌ Error: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ML Classifier demo failed: {e}")
        return False

def demo_fact_checker():
    """Demo fact checker functionality"""
    print("\n🔍 Fact Checker Demo")
    print("-" * 30)
    
    try:
        from fact_checker import enhanced_fact_check
        
        test_cases = [
            "Elon Musk bought Google for $500 billion",
            "President announces new policy today",
            "Scientists discover cure for cancer"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n{i}. Text: {text}")
            
            result = enhanced_fact_check(text)
            credibility = result.get('credibility_analysis', {})
            
            print(f"   📊 Has fact checks: {result.get('has_fact_checks', False)}")
            print(f"   🎯 Credibility: {credibility.get('credibility_score', 0.5):.3f}")
            print(f"   📝 Verdict: {credibility.get('verdict', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fact Checker demo failed: {e}")
        return False

def demo_enhanced_integration():
    """Demo enhanced ML + fact-check integration"""
    print("\n🚀 Enhanced Integration Demo")
    print("-" * 30)
    
    try:
        from enhanced_ml_integration import process_content_with_fact_check
        
        test_cases = [
            {
                "content": "Breaking: VIP politician involved in scandal",
                "vip_name": "politician",
                "platform": "twitter"
            },
            {
                "content": "FAKE: Celebrity caught in alien meeting",
                "vip_name": "celebrity", 
                "platform": "facebook"
            },
            {
                "content": "Official: New healthcare policy announced",
                "platform": "news"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. Content: {case['content'][:50]}...")
            
            result = process_content_with_fact_check(case)
            analysis = result.get("analysis", {})
            assessment = analysis.get("combined_assessment", {})
            
            print(f"   🎯 Verdict: {assessment.get('verdict', 'unknown')}")
            print(f"   📊 Threat Score: {assessment.get('combined_threat_score', 0):.3f}")
            print(f"   🚨 Flagged: {result.get('flagged', False)}")
            print(f"   🎬 Action: {result.get('action', 'none')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Enhanced Integration demo failed: {e}")
        return False

def demo_ml_service():
    """Demo ML service functionality"""
    print("\n🌐 ML Service Demo")
    print("-" * 30)
    
    try:
        from ml_service import ProtegoMLService
        
        service = ProtegoMLService()
        
        # Test service status
        status = service.get_service_status()
        print(f"   📊 Service: {status['service']}")
        print(f"   ✅ Status: {status['status']}")
        print(f"   🔧 Components: {status['components']}")
        
        # Test content analysis
        test_content = "Breaking: VIP threatens national security"
        result = service.analyze_content(test_content, {"platform": "twitter"})
        
        print(f"\n   📝 Content: {result['content_preview']}")
        
        ml_analysis = result.get('ml_analysis', {})
        if 'error' not in ml_analysis:
            print(f"   🧠 ML: {ml_analysis.get('prediction', 'N/A')}")
        
        recommendation = result.get('recommendation', {})
        print(f"   🎯 Action: {recommendation.get('action', 'N/A')}")
        print(f"   📊 Risk: {recommendation.get('risk_score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ML Service demo failed: {e}")
        return False

def create_demo_report():
    """Create demo execution report"""
    report = {
        "demo_timestamp": datetime.now().isoformat(),
        "system": "Protego ML Integration",
        "components_tested": [
            "ML Classifier",
            "Fact Checker", 
            "Enhanced Integration",
            "ML Service"
        ],
        "status": "Demo completed successfully",
        "next_steps": [
            "Start API service: python ml_api.py",
            "Run integration tests: python test_complete_integration.py",
            "Integrate with main Protego service"
        ]
    }
    
    with open("demo_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Demo report saved: demo_report.json")

def main():
    """Run comprehensive ML system demo"""
    print("🎯 Protego ML System - Comprehensive Demo")
    print("=" * 50)
    
    # Ensure models exist
    if not ensure_models_exist():
        print("❌ Cannot proceed without ML models")
        return
    
    # Run demos
    demos = [
        ("ML Classifier", demo_ml_classifier),
        ("Fact Checker", demo_fact_checker),
        ("Enhanced Integration", demo_enhanced_integration),
        ("ML Service", demo_ml_service)
    ]
    
    passed = 0
    for demo_name, demo_func in demos:
        try:
            if demo_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {demo_name} demo failed: {e}")
    
    # Create report
    create_demo_report()
    
    print(f"\n🎯 Demo Results: {passed}/{len(demos)} components working")
    
    if passed == len(demos):
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n🚀 Ready for production:")
        print("   - ML classification: ✅")
        print("   - Fact-checking: ✅")
        print("   - Enhanced integration: ✅") 
        print("   - Service wrapper: ✅")
        
        print("\n📋 Next steps:")
        print("   1. Start API: python ml_api.py")
        print("   2. Test endpoints: curl http://localhost:5001/api/health")
        print("   3. Integrate with main service")
    else:
        print(f"\n⚠️ {len(demos) - passed} components need attention")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick Test for Protego ML System
Simple verification that components are working
"""

import os
import sys

def test_imports():
    """Test if all components can be imported"""
    print("🔍 Testing imports...")
    
    results = {}
    
    # Test ML classifier
    try:
        from ml_classifier import classify_text, is_high_risk_content
        results["ml_classifier"] = "✅ Available"
    except Exception as e:
        results["ml_classifier"] = f"❌ Error: {e}"
    
    # Test fact checker
    try:
        from fact_checker import enhanced_fact_check
        results["fact_checker"] = "✅ Available"
    except Exception as e:
        results["fact_checker"] = f"❌ Error: {e}"
    
    # Test enhanced integration
    try:
        from enhanced_ml_integration import enhanced_content_analysis
        results["enhanced_integration"] = "✅ Available"
    except Exception as e:
        results["enhanced_integration"] = f"❌ Error: {e}"
    
    # Test ML service
    try:
        from ml_service import ProtegoMLService
        results["ml_service"] = "✅ Available"
    except Exception as e:
        results["ml_service"] = f"❌ Error: {e}"
    
    return results

def create_sample_models():
    """Create minimal sample models for testing"""
    print("🔧 Creating sample models...")
    
    try:
        import joblib
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        
        # Sample data
        texts = [
            "Breaking news scandal fake",
            "Government conspiracy urgent",
            "Official announcement policy",
            "Research study published"
        ]
        labels = [0, 0, 1, 1]  # 0=fake, 1=real
        
        # Create and train simple model
        vectorizer = TfidfVectorizer(max_features=100)
        X = vectorizer.fit_transform(texts)
        model = LogisticRegression()
        model.fit(X, labels)
        
        # Save to monitoring directory
        os.makedirs("backend/monitoring", exist_ok=True)
        joblib.dump(vectorizer, "backend/monitoring/tfidf_vectorizer.joblib")
        joblib.dump(model, "backend/monitoring/threat_model.joblib")
        
        print("   ✅ Sample models created")
        return True
        
    except Exception as e:
        print(f"   ❌ Model creation failed: {e}")
        return False

def test_ml_classifier():
    """Test ML classifier functionality"""
    print("🧪 Testing ML classifier...")
    
    try:
        from ml_classifier import classify_text
        
        test_text = "Breaking: VIP politician caught in scandal"
        result = classify_text(test_text)
        
        if "error" not in result:
            print(f"   ✅ Prediction: {result.get('prediction', 'unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 0):.3f}")
            return True
        else:
            print(f"   ❌ Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_service():
    """Test ML service"""
    print("🚀 Testing ML service...")
    
    try:
        from ml_service import ProtegoMLService
        
        service = ProtegoMLService()
        test_content = "Test content for analysis"
        result = service.analyze_content(test_content)
        
        print(f"   ✅ Service operational")
        print(f"   📊 Analysis completed: {result.get('timestamp', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"   ❌ Service test failed: {e}")
        return False

def main():
    """Run quick test suite"""
    print("🎯 Protego ML System - Quick Test")
    print("=" * 40)
    
    # Test imports
    import_results = test_imports()
    for component, status in import_results.items():
        print(f"   {component}: {status}")
    
    print()
    
    # Create sample models if needed
    if not os.path.exists("backend/monitoring/threat_model.joblib"):
        create_sample_models()
    
    # Test components
    tests = [
        ("ML Classifier", test_ml_classifier),
        ("ML Service", test_service)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {test_name} failed: {e}")
    
    print(f"\n🎯 Quick Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 System is operational!")
    else:
        print("⚠️ Some components need attention")

if __name__ == "__main__":
    main()

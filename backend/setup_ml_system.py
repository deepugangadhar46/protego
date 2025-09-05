#!/usr/bin/env python3
"""
Setup Script for Protego ML System
Ensures all components are properly initialized and ready
"""

import os
import sys
import json
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'sklearn', 'pandas', 'numpy', 'joblib', 
        'requests', 'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def create_sample_models():
    """Create sample ML models for testing"""
    print("\n🔧 Creating sample ML models...")
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        import joblib
        import pandas as pd
        
        # Sample training data
        fake_texts = [
            "BREAKING: Aliens land in Washington DC",
            "SHOCKING: Celebrity caught stealing millions",
            "URGENT: Government plans to ban social media",
            "EXCLUSIVE: Secret documents reveal conspiracy",
            "VIP threatens to destroy economy",
        ]
        
        real_texts = [
            "President announces new infrastructure bill",
            "Scientists publish climate change research",
            "Stock market closes higher today",
            "New healthcare policy reduces costs",
            "Government official provides economic update"
        ]
        
        # Create training data
        texts = fake_texts + real_texts
        labels = [0] * len(fake_texts) + [1] * len(real_texts)
        
        # Train simple model
        vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
        X = vectorizer.fit_transform(texts)
        
        model = LogisticRegression(random_state=42)
        model.fit(X, labels)
        
        # Save models
        monitoring_dir = "backend/monitoring"
        os.makedirs(monitoring_dir, exist_ok=True)
        
        vectorizer_path = os.path.join(monitoring_dir, "tfidf_vectorizer.joblib")
        model_path = os.path.join(monitoring_dir, "threat_model.joblib")
        
        joblib.dump(vectorizer, vectorizer_path)
        joblib.dump(model, model_path)
        
        print(f"   ✅ Vectorizer saved: {vectorizer_path}")
        print(f"   ✅ Model saved: {model_path}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model creation failed: {e}")
        return False

def test_ml_classifier():
    """Test ML classifier with sample data"""
    print("\n🧪 Testing ML classifier...")
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from ml_classifier import classify_text
        
        test_text = "Breaking: VIP politician caught in scandal"
        result = classify_text(test_text)
        
        if "error" not in result:
            print(f"   ✅ Classification: {result['prediction']}")
            print(f"   📊 Confidence: {result['confidence']:.3f}")
            return True
        else:
            print(f"   ❌ Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_fact_checker():
    """Test fact checker functionality"""
    print("\n🔍 Testing fact checker...")
    
    try:
        from fact_checker import enhanced_fact_check
        
        # Simple test without API key
        test_text = "Test content for fact checking"
        result = enhanced_fact_check(test_text)
        
        print(f"   ✅ Fact checker functional")
        print(f"   📊 Has checks: {result.get('has_fact_checks', False)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Fact checker error: {e}")
        return False

def create_status_report():
    """Create system status report"""
    print("\n📊 System Status Report")
    print("=" * 40)
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "files_created": [],
        "next_steps": []
    }
    
    # Check file existence
    files_to_check = [
        "enhanced_ml_integration.py",
        "ml_classifier.py", 
        "fact_checker.py",
        "content_logger.py",
        "demo_ml_pipeline.py",
        "test_complete_integration.py",
        "backend/monitoring/tfidf_vectorizer.joblib",
        "backend/monitoring/threat_model.joblib"
    ]
    
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        status["components"][file_path] = exists
        print(f"   {'✅' if exists else '❌'} {file_path}")
    
    # Save status report
    with open("ml_system_status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    print(f"\n💾 Status saved to: ml_system_status.json")
    return status

def main():
    """Main setup function"""
    print("🚀 Protego ML System Setup")
    print("=" * 40)
    
    success_count = 0
    total_steps = 4
    
    # Step 1: Check dependencies
    if check_dependencies():
        success_count += 1
    
    # Step 2: Create sample models
    if create_sample_models():
        success_count += 1
    
    # Step 3: Test ML classifier
    if test_ml_classifier():
        success_count += 1
    
    # Step 4: Test fact checker
    if test_fact_checker():
        success_count += 1
    
    # Create status report
    status = create_status_report()
    
    print(f"\n🎯 Setup Complete: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("🎉 ALL SYSTEMS READY!")
        print("\n🚀 Next steps:")
        print("   - Run: python test_complete_integration.py")
        print("   - Run: python enhanced_ml_integration.py")
        print("   - Integrate with main service")
    else:
        print("⚠️ Some components need attention")
        print("Check the status report for details")

if __name__ == "__main__":
    main()

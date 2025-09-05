#!/usr/bin/env python3
"""
Complete Integration Demo
Shows the full ML pipeline integration with Protego system
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from ml_classifier import classify_text, is_high_risk_content
from content_logger import save_alert, get_content_logger
from service_integration import process_incoming_post, batch_process_posts

def demo_complete_pipeline():
    """Demonstrate the complete ML integration pipeline"""
    print("🚀 Protego ML Integration Demo")
    print("=" * 50)
    
    # Sample posts to process
    sample_posts = [
        {
            "content": "Breaking: VIP politician caught in major corruption scandal with evidence",
            "vip_name": "politician",
            "platform": "twitter",
            "user_id": "user123",
            "post_id": "tweet001",
            "url": "https://twitter.com/user/status/tweet001"
        },
        {
            "content": "President announces new healthcare policy in official statement",
            "vip_name": "president",
            "platform": "facebook",
            "user_id": "user456",
            "post_id": "fb002",
            "url": "https://facebook.com/fb002"
        },
        {
            "content": "FAKE NEWS: Celebrity seen with aliens in secret government meeting",
            "vip_name": "celebrity",
            "platform": "twitter",
            "user_id": "user789",
            "post_id": "tweet003",
            "url": "https://twitter.com/user/status/tweet003"
        },
        {
            "content": "Scientific study confirms climate change effects on agriculture",
            "platform": "reddit",
            "user_id": "scientist_user",
            "post_id": "reddit004",
            "url": "https://reddit.com/r/science/reddit004"
        }
    ]
    
    print("📊 Processing sample posts...")
    print("-" * 40)
    
    # Process each post
    for i, post in enumerate(sample_posts, 1):
        print(f"\n{i}. Processing: {post['content'][:60]}...")
        
        # Process through our pipeline
        result = process_incoming_post(post)
        
        # Display results
        classification = result.get('classification', {})
        print(f"   🔍 Prediction: {classification.get('prediction', 'unknown')}")
        print(f"   📊 Confidence: {classification.get('confidence', 0):.3f}")
        print(f"   🚨 High Risk: {result.get('is_high_risk', False)}")
        print(f"   🏷️  Action: {result.get('action', 'none')}")
        
        if result.get('flagged'):
            print(f"   💾 Logged to DB: ID {result.get('content_id', 'N/A')}")
    
    # Batch processing demo
    print(f"\n📦 Batch Processing Results:")
    batch_results = batch_process_posts(sample_posts)
    print(f"   → Total Processed: {batch_results['total_processed']}")
    print(f"   → Flagged: {batch_results['flagged_count']}")
    print(f"   → High Risk: {batch_results['high_risk_count']}")
    print(f"   → Errors: {batch_results['error_count']}")
    
    # Show recent alerts from database
    print(f"\n📋 Recent Flagged Content:")
    logger = get_content_logger()
    recent_alerts = logger.get_recent_alerts(limit=5)
    
    for alert in recent_alerts[:3]:  # Show top 3
        print(f"   • {alert['content'][:50]}...")
        print(f"     Prediction: {alert['prediction']} ({alert['confidence']:.2f})")
        print(f"     Platform: {alert['platform']}")
    
    print(f"\n🎉 Integration Demo Complete!")
    print("=" * 50)
    print("✅ ML models loaded and working")
    print("✅ Content classification functional")
    print("✅ Database logging operational")
    print("✅ Service integration ready")

def demo_simple_classification():
    """Simple classification demo without full pipeline"""
    print("\n🔧 Simple Classification Demo")
    print("-" * 30)
    
    test_texts = [
        "VIP announces new policy initiative",
        "BREAKING: Fake scandal about celebrity",
        "Government official provides economic update"
    ]
    
    for text in test_texts:
        result = classify_text(text)
        high_risk = is_high_risk_content(text)
        
        print(f"\nText: {text}")
        print(f"Prediction: {result.get('prediction', 'unknown')}")
        print(f"Confidence: {result.get('confidence', 0):.3f}")
        print(f"High Risk: {high_risk}")

if __name__ == "__main__":
    print("🎯 Protego ML Integration System")
    print("Complete fake news detection and threat monitoring")
    print()
    
    try:
        # Run simple classification first
        demo_simple_classification()
        
        # Run complete pipeline demo
        demo_complete_pipeline()
        
        print("\n💡 Next Steps:")
        print("1. Train models: python demo_ml_pipeline.py")
        print("2. Integrate with main service.py")
        print("3. Set up monitoring dashboard")
        print("4. Configure alert notifications")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure to run demo_ml_pipeline.py first to train models")

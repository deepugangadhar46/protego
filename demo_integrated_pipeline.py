#!/usr/bin/env python3
"""
Demo script for the integrated VIP threat detection pipeline
Tests all detection modules with sample data
"""

import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append('backend')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_misinformation_detection():
    """Demo misinformation detection"""
    print("\n" + "="*60)
    print("🔍 MISINFORMATION DETECTION DEMO")
    print("="*60)
    
    try:
        from backend.integrated_detection_pipeline import analyze_content_comprehensive
        
        # Sample misinformation content
        sample_content = {
            "text": "BREAKING: Scientists confirm that vaccines contain microchips for government tracking. This has been covered up by mainstream media but leaked documents prove it's true.",
            "username": "truth_seeker_2024",
            "platform": "twitter",
            "post_url": "https://twitter.com/truth_seeker_2024/status/123456789",
            "vip_mentioned": "Dr. Anthony Fauci",
            "user_id": "12345",
            "image_urls": []
        }
        
        print(f"📝 Analyzing text: {sample_content['text'][:100]}...")
        result = analyze_content_comprehensive(sample_content)
        
        print(f"🎯 Overall Threat Score: {result.get('overall_threat_score', 0):.3f}")
        print(f"📊 Max Confidence: {result.get('max_confidence', 0):.3f}")
        print(f"🚨 Alert Triggered: {result.get('alert_triggered', False)}")
        print(f"💾 Evidence Stored: {result.get('evidence_stored', False)}")
        
        if result.get('alert_id'):
            print(f"🆔 Alert ID: {result['alert_id']}")
        
        # Show detection details
        detections = result.get('detections', {})
        if 'misinformation' in detections:
            mis_result = detections['misinformation']
            risk_assessment = mis_result.get('risk_assessment', {})
            print(f"📰 Misinformation Risk: {risk_assessment.get('risk_score', 0):.3f}")
            print(f"🔍 Risk Factors: {', '.join(risk_assessment.get('risk_factors', [])[:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Misinformation detection failed: {e}")
        return False

def demo_fake_profile_detection():
    """Demo fake profile detection"""
    print("\n" + "="*60)
    print("👤 FAKE PROFILE DETECTION DEMO")
    print("="*60)
    
    try:
        from backend.integrated_detection_pipeline import analyze_content_comprehensive
        
        # Sample fake profile content
        sample_content = {
            "text": "Hello everyone! I'm the real Elon Musk. Follow me for exclusive Tesla updates!",
            "username": "elonmusk_official",  # Similar to real @elonmusk
            "platform": "twitter",
            "post_url": "https://twitter.com/elonmusk_official/status/987654321",
            "vip_mentioned": "Elon Musk",
            "user_id": "67890",
            "followers_count": 150,
            "verified": False,
            "account_created": "2024-01-15",
            "image_urls": []
        }
        
        print(f"👤 Analyzing profile: @{sample_content['username']}")
        result = analyze_content_comprehensive(sample_content)
        
        print(f"🎯 Overall Threat Score: {result.get('overall_threat_score', 0):.3f}")
        print(f"🚨 Alert Triggered: {result.get('alert_triggered', False)}")
        
        # Show fake profile detection details
        detections = result.get('detections', {})
        if 'fake_profile' in detections:
            profile_result = detections['fake_profile']
            risk_assessment = profile_result.get('risk_assessment', {})
            print(f"🎭 Profile Risk: {risk_assessment.get('risk_score', 0):.3f}")
            print(f"⚠️ Risk Factors: {', '.join(risk_assessment.get('risk_factors', [])[:3])}")
            
            similarity_check = profile_result.get('similarity_check', {})
            if similarity_check.get('matches'):
                print(f"🔍 Similar to VIP: {similarity_check['matches'][0]['vip_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fake profile detection failed: {e}")
        return False

def demo_campaign_detection():
    """Demo campaign detection"""
    print("\n" + "="*60)
    print("📢 CAMPAIGN DETECTION DEMO")
    print("="*60)
    
    try:
        from backend.integrated_detection_pipeline import analyze_content_comprehensive
        
        # Sample campaign content (coordinated messaging)
        sample_content = {
            "text": "Everyone needs to know the truth about the recent election fraud. Share this message to spread awareness! #StopTheSteal #TruthMatters",
            "username": "patriot_warrior_1",
            "platform": "twitter",
            "post_url": "https://twitter.com/patriot_warrior_1/status/555666777",
            "vip_mentioned": "Donald Trump",
            "user_id": "11111",
            "hashtags": ["#StopTheSteal", "#TruthMatters"],
            "image_urls": []
        }
        
        print(f"📢 Analyzing campaign content: {sample_content['text'][:80]}...")
        result = analyze_content_comprehensive(sample_content)
        
        print(f"🎯 Overall Threat Score: {result.get('overall_threat_score', 0):.3f}")
        print(f"🚨 Alert Triggered: {result.get('alert_triggered', False)}")
        
        # Show campaign detection details
        detections = result.get('detections', {})
        if 'campaign' in detections:
            campaign_result = detections['campaign']
            risk_assessment = campaign_result.get('risk_assessment', {})
            print(f"📊 Campaign Risk: {risk_assessment.get('risk_score', 0):.3f}")
            print(f"🔗 Risk Factors: {', '.join(risk_assessment.get('risk_factors', [])[:3])}")
            
            clustering_result = campaign_result.get('clustering_analysis', {})
            if clustering_result.get('similar_posts'):
                print(f"🎯 Similar posts found: {len(clustering_result['similar_posts'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Campaign detection failed: {e}")
        return False

def demo_pipeline_stats():
    """Demo pipeline statistics"""
    print("\n" + "="*60)
    print("📊 PIPELINE STATISTICS")
    print("="*60)
    
    try:
        from backend.integrated_detection_pipeline import get_detection_pipeline
        
        pipeline = get_detection_pipeline()
        stats = pipeline.get_pipeline_stats()
        
        print("📈 Evidence Statistics:")
        evidence_stats = stats.get('evidence_stats', {})
        print(f"   Total Evidence: {evidence_stats.get('total_evidence', 0)}")
        
        verification_status = evidence_stats.get('verification_status', {})
        for status, count in verification_status.items():
            print(f"   {status.title()}: {count}")
        
        print("\n🔍 Detection Types:")
        detection_types = evidence_stats.get('detection_types', {})
        for det_type, count in detection_types.items():
            print(f"   {det_type.title()}: {count}")
        
        print("\n📱 Platforms:")
        platforms = evidence_stats.get('platforms', {})
        for platform, count in platforms.items():
            print(f"   {platform.title()}: {count}")
        
        print(f"\n🚨 Recent Alerts: {stats.get('recent_alerts', 0)}")
        print(f"⚡ Pipeline Status: {stats.get('pipeline_status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline stats failed: {e}")
        return False

def demo_alerting_system():
    """Demo alerting system"""
    print("\n" + "="*60)
    print("📱 ALERTING SYSTEM DEMO")
    print("="*60)
    
    try:
        from backend.alerting.telegram_bot import get_alerting_system
        
        alerting = get_alerting_system()
        
        # Test connection
        print("🔗 Testing alerting channels...")
        test_results = alerting.test_all_channels()
        
        for channel, success in test_results.items():
            status = "✅ Connected" if success else "❌ Failed"
            print(f"   {channel.title()}: {status}")
        
        # Show recent alert history
        history = alerting.get_alert_history(5)
        print(f"\n📋 Recent Alerts: {len(history)}")
        
        for i, alert in enumerate(history[-3:], 1):
            print(f"   {i}. {alert.get('detection_type', 'unknown')} - Score: {alert.get('threat_score', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alerting system demo failed: {e}")
        return False

def main():
    """Run complete integrated pipeline demo"""
    print("🚀 VIP THREAT DETECTION - INTEGRATED PIPELINE DEMO")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    print("\n🔧 Environment Check:")
    required_vars = [
        "FACT_CHECK_API_KEY",
        "TELEGRAM_BOT_TOKEN", 
        "BING_SEARCH_API_KEY",
        "GOOGLE_SEARCH_API_KEY"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "⚠️ Missing"
        print(f"   {var}: {status}")
    
    # Run demos
    demos = [
        ("Misinformation Detection", demo_misinformation_detection),
        ("Fake Profile Detection", demo_fake_profile_detection),
        ("Campaign Detection", demo_campaign_detection),
        ("Pipeline Statistics", demo_pipeline_stats),
        ("Alerting System", demo_alerting_system)
    ]
    
    results = {}
    for demo_name, demo_func in demos:
        try:
            print(f"\n🎯 Running {demo_name}...")
            success = demo_func()
            results[demo_name] = success
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results[demo_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("📋 DEMO SUMMARY")
    print("="*80)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for demo_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {demo_name}: {status}")
    
    print(f"\n🎯 Overall: {successful}/{total} demos successful")
    
    if successful == total:
        print("🎉 All systems operational! VIP threat detection pipeline ready.")
    else:
        print("⚠️ Some components need attention. Check logs for details.")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

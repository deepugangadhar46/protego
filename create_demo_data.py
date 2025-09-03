#!/usr/bin/env python3
"""
Create demo data for Protego VIP Monitoring System
"""
import asyncio
import sys
import os
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import uuid
import random

async def create_demo_data():
    """Create comprehensive demo data"""
    print("🚀 Creating demo data for Protego VIP Monitoring System...")
    
    # Connect to database
    mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017/protego")
    database = mongodb_client.protego
    
    # Clear existing data
    await database.vip_profiles.delete_many({})
    await database.threat_alerts.delete_many({})
    print("✅ Cleared existing data")
    
    # Create demo VIP profiles based on real public figure types
    demo_vips = [
        {
            "id": str(uuid.uuid4()),
            "name": "Sarah Chen",
            "title": "Tech CEO & Entrepreneur",
            "platforms": ["twitter", "linkedin", "instagram", "reddit", "youtube"],
            "keywords": ["Sarah Chen", "TechFlow Inc", "CEO", "startup", "innovation"],
            "risk_level": "high",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Marcus Rodriguez",
            "title": "Political Activist & Author",
            "platforms": ["twitter", "facebook", "telegram", "youtube", "reddit"],
            "keywords": ["Marcus Rodriguez", "civil rights", "author", "activist", "social justice"],
            "risk_level": "high",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=25),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Dr. Emily Watson",
            "title": "Medical Researcher & Public Health Expert",
            "platforms": ["twitter", "linkedin", "youtube", "instagram"],
            "keywords": ["Dr Emily Watson", "medical research", "public health", "scientist", "vaccine"],
            "risk_level": "medium",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=20),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "James Mitchell",
            "title": "Investigative Journalist",
            "platforms": ["twitter", "reddit", "telegram", "youtube"],
            "keywords": ["James Mitchell", "journalist", "investigation", "corruption", "news"],
            "risk_level": "high",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=15),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Lisa Park",
            "title": "Environmental Activist & Influencer",
            "platforms": ["instagram", "twitter", "youtube", "tiktok"],
            "keywords": ["Lisa Park", "environment", "climate change", "activism", "green"],
            "risk_level": "medium",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=10),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Insert VIP profiles
    await database.vip_profiles.insert_many(demo_vips)
    print(f"✅ Created {len(demo_vips)} VIP profiles")
    
    # Create realistic threat scenarios based on historical patterns
    threat_scenarios = []
    platforms = ["twitter", "reddit", "instagram", "telegram", "youtube", "facebook", "discord"]
    
    for vip in demo_vips:
        vip_threats = []
        
        # Generate threats over the past 7 days
        for days_ago in range(7):
            threat_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Number of threats per day (higher risk VIPs get more threats)
            threat_count = random.randint(1, 4) if vip["risk_level"] == "high" else random.randint(0, 2)
            
            for _ in range(threat_count):
                platform = random.choice(vip["platforms"])
                
                # Realistic threat scenarios based on VIP type
                if "CEO" in vip["title"]:
                    threat_examples = [
                        f"Fake account impersonating {vip['name']} trying to scam investors",
                        f"False allegations about {vip['name']}'s company financial practices",
                        f"Coordinated harassment campaign targeting {vip['name']} after product announcement",
                        f"Leaked fake internal documents attributed to {vip['name']}'s company",
                        f"Deepfake video of {vip['name']} making controversial statements"
                    ]
                    threat_types = ["impersonation", "misinformation", "harassment", "data_leak", "deepfake"]
                    
                elif "Political" in vip["title"] or "Activist" in vip["title"]:
                    threat_examples = [
                        f"Death threats against {vip['name']} over recent political stance",
                        f"Doxxing attempt revealing {vip['name']}'s home address and family info",
                        f"Fake news article claiming {vip['name']} has extreme political views",
                        f"Coordinated bot campaign spreading false information about {vip['name']}",
                        f"Harassment of {vip['name']}'s family members on social media"
                    ]
                    threat_types = ["physical_threat", "doxxing", "misinformation", "coordinated_campaign", "harassment"]
                    
                elif "Medical" in vip["title"] or "Dr." in vip["name"]:
                    threat_examples = [
                        f"Conspiracy theorists targeting {vip['name']} over vaccine research",
                        f"False credentials claim - fake post saying {vip['name']} isn't really a doctor",
                        f"Harassment campaign against {vip['name']} for public health recommendations",
                        f"Fake research paper attributed to {vip['name']} with dangerous medical advice",
                        f"Personal threats against {vip['name']} at medical conferences"
                    ]
                    threat_types = ["harassment", "misinformation", "impersonation", "physical_threat", "reputation_damage"]
                    
                elif "Journalist" in vip["title"]:
                    threat_examples = [
                        f"Intimidation threats against {vip['name']} over corruption investigation",
                        f"Fake social media accounts spreading false stories about {vip['name']}",
                        f"Legal threats attempting to silence {vip['name']}'s reporting",
                        f"Personal information leak - {vip['name']}'s sources and contacts exposed",
                        f"Coordinated campaign to discredit {vip['name']}'s investigative work"
                    ]
                    threat_types = ["intimidation", "misinformation", "legal_threat", "data_leak", "reputation_damage"]
                    
                else:  # Environmental/General Activist
                    threat_examples = [
                        f"Corporate-backed trolls targeting {vip['name']} over environmental activism",
                        f"Climate change deniers spreading false information about {vip['name']}",
                        f"Harassment at public events where {vip['name']} is speaking",
                        f"Fake endorsements attributed to {vip['name']} for harmful products",
                        f"Attempts to discredit {vip['name']}'s environmental research"
                    ]
                    threat_types = ["harassment", "misinformation", "physical_threat", "impersonation", "reputation_damage"]
                
                # Select random scenario
                content = random.choice(threat_examples)
                threat_type = random.choice(threat_types)
                
                # Determine severity based on threat type
                severity_mapping = {
                    "physical_threat": random.choice(["high", "critical"]),
                    "doxxing": random.choice(["high", "critical"]),
                    "death_threat": "critical",
                    "harassment": random.choice(["low", "medium", "high"]),
                    "misinformation": random.choice(["medium", "high"]),
                    "impersonation": random.choice(["medium", "high"]),
                    "reputation_damage": random.choice(["medium", "high"]),
                    "data_leak": random.choice(["high", "critical"]),
                    "coordinated_campaign": "high",
                    "deepfake": "critical"
                }
                
                severity = severity_mapping.get(threat_type, "medium")
                
                # Create realistic evidence
                evidence = {
                    "detection_method": "AI Analysis + Pattern Recognition",
                    "platform_specific": {
                        "post_id": f"{platform}_{random.randint(100000, 999999)}",
                        "account_age": f"{random.randint(1, 365)} days",
                        "follower_count": random.randint(10, 10000),
                        "verified": random.choice([True, False])
                    },
                    "ai_confidence": random.uniform(0.7, 0.95),
                    "pattern_indicators": random.choice([
                        ["coordinated_timing", "similar_language"],
                        ["new_account", "suspicious_activity"],
                        ["keyword_targeting", "hashtag_abuse"],
                        ["image_manipulation", "deepfake_markers"]
                    ]),
                    "screenshot_url": f"https://protego-evidence.s3.amazonaws.com/screenshots/{uuid.uuid4()}.png",
                    "archived_url": f"https://archive.today/{random.randint(100000, 999999)}"
                }
                
                threat = {
                    "id": str(uuid.uuid4()),
                    "vip_id": vip["id"],
                    "vip_name": vip["name"],
                    "platform": platform,
                    "threat_type": threat_type,
                    "severity": severity,
                    "confidence_score": random.uniform(0.7, 0.95),
                    "content": content,
                    "source_url": f"https://{platform}.com/post/{random.randint(100000, 999999)}",
                    "evidence": evidence,
                    "status": random.choice(["new", "investigating", "resolved"]),
                    "created_at": threat_date,
                    "analyzed_at": threat_date + timedelta(minutes=random.randint(1, 30))
                }
                
                vip_threats.append(threat)
        
        threat_scenarios.extend(vip_threats)
    
    # Insert threats
    if threat_scenarios:
        await database.threat_alerts.insert_many(threat_scenarios)
        print(f"✅ Created {len(threat_scenarios)} realistic threat scenarios")
    
    # Create some additional high-impact scenarios for demonstration
    critical_scenarios = [
        {
            "id": str(uuid.uuid4()),
            "vip_id": demo_vips[0]["id"],  # Sarah Chen (CEO)
            "vip_name": demo_vips[0]["name"],
            "platform": "twitter",
            "threat_type": "coordinated_campaign",
            "severity": "critical",
            "confidence_score": 0.94,
            "content": "BREAKING: Coordinated bot network (500+ accounts) spreading false bankruptcy rumors about TechFlow Inc and CEO Sarah Chen. Accounts created within 48 hours, using identical language patterns and hashtags #TechFlowScam #SarahChenFraud. Market manipulation suspected.",
            "source_url": "https://twitter.com/analysis/coordinated_attack_001",
            "evidence": {
                "bot_network_size": 500,
                "coordination_score": 0.94,
                "market_impact": "Stock down 12% in 2 hours",
                "similar_content_percentage": 87,
                "geographic_clustering": "Primarily from 3 locations",
                "temporal_pattern": "All posted within 15-minute window"
            },
            "status": "new",
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "analyzed_at": datetime.utcnow() - timedelta(hours=1, minutes=30)
        },
        {
            "id": str(uuid.uuid4()),
            "vip_id": demo_vips[1]["id"],  # Marcus Rodriguez (Activist)
            "vip_name": demo_vips[1]["name"],
            "platform": "telegram",
            "threat_type": "doxxing",
            "severity": "critical",
            "confidence_score": 0.98,
            "content": "URGENT: Private Telegram channel (2,000+ members) sharing Marcus Rodriguez's home address, family photos, children's school location, and daily routine. Multiple members discussing 'taking action' and 'making him pay for his activism.' Screenshots of his private social media and financial information also shared.",
            "source_url": "https://t.me/private_channel_exposed",
            "evidence": {
                "channel_members": 2000,
                "personal_info_shared": ["home_address", "family_photos", "school_location", "financial_data"],
                "threat_level_indicators": ["taking_action", "making_pay", "visit_him"],
                "screenshots_count": 15,
                "private_info_accuracy": "Verified as accurate",
                "law_enforcement_contacted": True
            },
            "status": "investigating",
            "created_at": datetime.utcnow() - timedelta(hours=6),
            "analyzed_at": datetime.utcnow() - timedelta(hours=5, minutes=45)
        }
    ]
    
    await database.threat_alerts.insert_many(critical_scenarios)
    print(f"✅ Added {len(critical_scenarios)} critical demonstration scenarios")
    
    # Print summary
    total_vips = await database.vip_profiles.count_documents({"status": "active"})
    total_threats = await database.threat_alerts.count_documents({})
    recent_threats = await database.threat_alerts.count_documents({
        "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
    })
    critical_threats = await database.threat_alerts.count_documents({"severity": "critical"})
    
    print(f"""
🎯 PROTEGO DEMO DATA SUMMARY
================================
✅ VIP Profiles: {total_vips}
✅ Total Threats: {total_threats}
✅ Recent (24h): {recent_threats}
✅ Critical Severity: {critical_threats}

💡 Demo Features:
- Realistic threat scenarios based on actual public figure risks
- Multiple platform coverage (Twitter, Reddit, Telegram, YouTube, etc.)
- AI-powered threat classification and severity assessment
- Evidence collection with screenshots and archived content
- Real-time monitoring simulation
- Historical trend analysis

🚀 Ready to demonstrate comprehensive VIP threat monitoring!
""")
    
    mongodb_client.close()

if __name__ == "__main__":
    asyncio.run(create_demo_data())
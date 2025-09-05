#!/usr/bin/env python3
"""
Enhanced VIP Dashboard Backend
Real-time comprehensive VIP monitoring with evidence collection
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import hashlib
import aiohttp

app = FastAPI(title="Enhanced VIP Monitoring Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class VIPProfile(BaseModel):
    name: str
    aliases: List[str]
    official_accounts: Dict[str, str]
    keywords: List[str]
    protection_level: str

class ThreatAlert(BaseModel):
    id: str
    vip_name: str
    threat_type: str
    platform: str
    source_url: str
    content: str
    confidence_score: float
    severity: str
    evidence: Dict[str, Any]
    timestamp: datetime
    cluster_id: Optional[str] = None

class MonitoringStats(BaseModel):
    total_vips: int
    threats_today: int
    high_severity_threats: int
    platforms_monitored: int
    last_scan: datetime

# In-memory storage (replace with database in production)
vip_profiles: Dict[str, VIPProfile] = {}
threat_alerts: List[ThreatAlert] = []
active_connections: List[WebSocket] = []

# Mock data for demonstration
def initialize_demo_data():
    """Initialize with demo VIP profiles and threats"""
    global vip_profiles, threat_alerts
    
    # Demo VIP profiles
    demo_vips = [
        VIPProfile(
            name="John Politician",
            aliases=["JP", "Senator John", "John P"],
            official_accounts={
                "twitter": "@john_politician_official",
                "facebook": "john.politician.page",
                "instagram": "@johnpolitician"
            },
            keywords=["john politician", "senator john", "jp politics"],
            protection_level="high"
        ),
        VIPProfile(
            name="Jane Celebrity",
            aliases=["JC", "Jane C", "Celebrity Jane"],
            official_accounts={
                "instagram": "@jane_celebrity_real",
                "twitter": "@jane_celebrity",
                "tiktok": "@janecelebrity"
            },
            keywords=["jane celebrity", "jane c", "celebrity jane"],
            protection_level="medium"
        ),
        VIPProfile(
            name="Tech CEO Mike",
            aliases=["Mike Tech", "CEO Mike", "Michael"],
            official_accounts={
                "linkedin": "mike-tech-ceo",
                "twitter": "@mike_tech_ceo"
            },
            keywords=["tech ceo mike", "mike tech", "ceo michael"],
            protection_level="high"
        )
    ]
    
    for vip in demo_vips:
        vip_profiles[vip.name] = vip
    
    # Demo threat alerts
    demo_threats = [
        ThreatAlert(
            id=str(uuid.uuid4()),
            vip_name="John Politician",
            threat_type="impersonation",
            platform="twitter",
            source_url="https://twitter.com/fake_john_pol/status/123456",
            content="I am the real John Politician! Follow my official account for exclusive updates.",
            confidence_score=0.87,
            severity="high",
            evidence={
                "screenshot_url": "https://screenshots.protego.com/fake_account_1.png",
                "user_verified": False,
                "account_created": "2024-01-15",
                "followers_count": 1250,
                "is_impersonation": True,
                "similarity_score": 0.89
            },
            timestamp=datetime.now() - timedelta(minutes=15)
        ),
        ThreatAlert(
            id=str(uuid.uuid4()),
            vip_name="Jane Celebrity",
            threat_type="misinformation",
            platform="facebook",
            source_url="https://facebook.com/fake_news_page/posts/789012",
            content="BREAKING: Jane Celebrity caught in major scandal! Leaked photos reveal shocking truth about her private life.",
            confidence_score=0.92,
            severity="critical",
            evidence={
                "screenshot_url": "https://screenshots.protego.com/misinformation_1.png",
                "shares_count": 2847,
                "reactions_count": 5632,
                "is_misinformation": True,
                "fact_check_verdict": "false",
                "image_manipulation_detected": True
            },
            timestamp=datetime.now() - timedelta(minutes=8),
            cluster_id="campaign_001"
        ),
        ThreatAlert(
            id=str(uuid.uuid4()),
            vip_name="Tech CEO Mike",
            threat_type="data_leak",
            platform="pastebin",
            source_url="https://pastebin.com/xyz789abc",
            content="Tech CEO Mike private data dump:\nEmail: mike@techcorp.com\nPassword: leaked_password_123\nPrivate documents attached...",
            confidence_score=0.95,
            severity="critical",
            evidence={
                "screenshot_url": "https://screenshots.protego.com/data_leak_1.png",
                "data_types": ["email", "password", "documents"],
                "leak_source": "unknown",
                "verification_status": "confirmed",
                "affected_accounts": 3
            },
            timestamp=datetime.now() - timedelta(minutes=3)
        ),
        ThreatAlert(
            id=str(uuid.uuid4()),
            vip_name="John Politician",
            threat_type="fake_campaign",
            platform="telegram",
            source_url="https://t.me/political_leaks/12345",
            content="Coordinated attack against John Politician begins now! Share this message to expose his corruption.",
            confidence_score=0.78,
            severity="high",
            evidence={
                "screenshot_url": "https://screenshots.protego.com/campaign_1.png",
                "channel_subscribers": 15420,
                "message_forwards": 892,
                "coordination_detected": True,
                "bot_activity": 0.65
            },
            timestamp=datetime.now() - timedelta(minutes=25),
            cluster_id="campaign_002"
        ),
        ThreatAlert(
            id=str(uuid.uuid4()),
            vip_name="Jane Celebrity",
            threat_type="deepfake",
            platform="youtube",
            source_url="https://youtube.com/watch?v=fake_video_123",
            content="Deepfake video showing Jane Celebrity in compromising situation goes viral",
            confidence_score=0.91,
            severity="critical",
            evidence={
                "screenshot_url": "https://screenshots.protego.com/deepfake_1.png",
                "video_duration": "2:34",
                "views_count": 45678,
                "deepfake_confidence": 0.94,
                "face_swap_detected": True,
                "audio_synthesis_detected": True
            },
            timestamp=datetime.now() - timedelta(minutes=45)
        )
    ]
    
    threat_alerts.extend(demo_threats)

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize demo data on startup"""
    initialize_demo_data()
    # Start background monitoring
    asyncio.create_task(continuous_monitoring())

@app.get("/api/stats")
async def get_stats() -> MonitoringStats:
    """Get monitoring statistics"""
    today = datetime.now().date()
    threats_today = len([t for t in threat_alerts if t.timestamp.date() == today])
    high_severity = len([t for t in threat_alerts if t.severity in ["critical", "high"]])
    
    return MonitoringStats(
        total_vips=len(vip_profiles),
        threats_today=threats_today,
        high_severity_threats=high_severity,
        platforms_monitored=8,  # Twitter, Facebook, Instagram, LinkedIn, Telegram, Pastebin, GitHub, YouTube
        last_scan=datetime.now()
    )

@app.get("/api/vips")
async def get_vips() -> List[VIPProfile]:
    """Get all VIP profiles"""
    return list(vip_profiles.values())

@app.post("/api/vips")
async def add_vip(vip: VIPProfile):
    """Add new VIP profile"""
    vip_profiles[vip.name] = vip
    await broadcast_update({"type": "vip_added", "data": vip.dict()})
    return {"status": "success", "message": f"VIP {vip.name} added"}

@app.get("/api/threats")
async def get_threats(
    hours: int = 24,
    limit: int = 50,
    severity: Optional[str] = None,
    vip_name: Optional[str] = None
) -> List[ThreatAlert]:
    """Get threat alerts with filters"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    filtered_threats = [
        t for t in threat_alerts 
        if t.timestamp >= cutoff_time
    ]
    
    if severity:
        filtered_threats = [t for t in filtered_threats if t.severity == severity]
    
    if vip_name:
        filtered_threats = [t for t in filtered_threats if t.vip_name == vip_name]
    
    # Sort by timestamp (newest first) and limit
    filtered_threats.sort(key=lambda x: x.timestamp, reverse=True)
    return filtered_threats[:limit]

@app.get("/api/threats/by-platform")
async def get_threats_by_platform():
    """Get threat distribution by platform"""
    platform_counts = {}
    for threat in threat_alerts:
        platform = threat.platform
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    return [{"platform": k, "count": v} for k, v in platform_counts.items()]

@app.get("/api/threats/by-severity")
async def get_threats_by_severity():
    """Get threat distribution by severity"""
    severity_counts = {}
    for threat in threat_alerts:
        severity = threat.severity
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    return [{"severity": k, "count": v} for k, v in severity_counts.items()]

@app.get("/api/threats/timeline")
async def get_threat_timeline(days: int = 7):
    """Get threat timeline for the last N days"""
    timeline = {}
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).date()
        timeline[str(date)] = 0
    
    for threat in threat_alerts:
        date_str = str(threat.timestamp.date())
        if date_str in timeline:
            timeline[date_str] += 1
    
    return [{"date": k, "count": v} for k, v in timeline.items()]

@app.get("/api/campaigns")
async def get_campaigns():
    """Get detected coordinated campaigns"""
    campaigns = {}
    
    for threat in threat_alerts:
        if threat.cluster_id:
            if threat.cluster_id not in campaigns:
                campaigns[threat.cluster_id] = []
            campaigns[threat.cluster_id].append(threat)
    
    return {
        "total_campaigns": len(campaigns),
        "campaigns": campaigns
    }

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_update(message: dict):
    """Broadcast update to all connected clients"""
    if active_connections:
        disconnected = []
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            active_connections.remove(conn)

async def continuous_monitoring():
    """Continuous monitoring simulation"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        # Simulate new threat detection
        if len(threat_alerts) < 20:  # Keep demo data manageable
            new_threat = await simulate_threat_detection()
            if new_threat:
                threat_alerts.append(new_threat)
                await broadcast_update({
                    "type": "new_threat",
                    "data": new_threat.dict()
                })

async def simulate_threat_detection() -> Optional[ThreatAlert]:
    """Simulate detection of new threats"""
    import random
    
    if random.random() < 0.3:  # 30% chance of new threat
        vip_names = list(vip_profiles.keys())
        if not vip_names:
            return None
            
        threat_types = ["impersonation", "misinformation", "data_leak", "fake_campaign"]
        platforms = ["twitter", "facebook", "instagram", "telegram", "youtube"]
        severities = ["low", "medium", "high", "critical"]
        
        selected_vip = random.choice(vip_names)
        threat_type = random.choice(threat_types)
        platform = random.choice(platforms)
        severity = random.choice(severities)
        
        return ThreatAlert(
            id=str(uuid.uuid4()),
            vip_name=selected_vip,
            threat_type=threat_type,
            platform=platform,
            source_url=f"https://{platform}.com/simulated_threat_{uuid.uuid4().hex[:8]}",
            content=f"Simulated {threat_type} content targeting {selected_vip}",
            confidence_score=random.uniform(0.6, 0.95),
            severity=severity,
            evidence={
                "screenshot_url": f"https://screenshots.protego.com/sim_{uuid.uuid4().hex[:8]}.png",
                "detection_method": "automated_scan",
                "platform_specific": True
            },
            timestamp=datetime.now()
        )
    
    return None

# Serve frontend static files
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced VIP Monitoring Dashboard...")
    print("📊 Dashboard: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/api/ws")
    print("📡 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

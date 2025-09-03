from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import asyncio
import logging
import os
from dotenv import load_dotenv
import json
import uuid
import sys

# Ensure project root is on sys.path when running as a script (python backend/server.py)
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Protego - VIP Threat Monitoring API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongodb_client = None
database = None

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class VIPProfile(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    title: str
    platforms: List[str]
    keywords: List[str]
    risk_level: str = "medium"
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ThreatAlert(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    vip_id: str
    vip_name: str
    platform: str
    threat_type: str
    severity: str
    confidence_score: float
    content: str
    source_url: str
    evidence: Dict[str, Any] = {}
    status: str = "new"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    analyzed_at: Optional[datetime] = None

class MonitoringStats(BaseModel):
    total_vips: int
    active_monitors: int
    threats_today: int
    high_severity_threats: int
    platforms_monitored: int
    last_scan: Optional[datetime]

# Database connection
@app.on_event("startup")
async def startup_event():
    global mongodb_client, database
    try:
        mongo_url = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
        mongodb_client = AsyncIOMotorClient(mongo_url)
        database = mongodb_client.protego
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await database.vip_profiles.create_index("name")
        await database.threat_alerts.create_index([("vip_id", 1), ("created_at", -1)])
        await database.threat_alerts.create_index("severity")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if mongodb_client:
        mongodb_client.close()

# API Routes

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Protego VIP Monitoring API",
        "version": "1.0.0"
    }

class AnalyzeRequest(BaseModel):
    content: str
    vip_name: str
    platform: str = "unknown"

@app.post("/api/analyze")
async def analyze_endpoint(req: AnalyzeRequest):
    try:
        result = await analyze_content_for_threats(req.content, req.vip_name, req.platform)
        return result
    except Exception as e:
        logger.error(f"Error in /api/analyze: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")

class AnalyzeRequest(BaseModel):
    content: str
    vip_name: str
    platform: str = "unknown"

@app.get("/api/stats", response_model=MonitoringStats) 
async def get_monitoring_stats():
    try:
        total_vips = await database.vip_profiles.count_documents({"status": "active"})
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        threats_today = await database.threat_alerts.count_documents({
            "created_at": {"$gte": today}
        })
        
        high_severity_threats = await database.threat_alerts.count_documents({
            "severity": "high",
            "status": {"$ne": "resolved"}
        })
        
        return MonitoringStats(
            total_vips=total_vips,
            active_monitors=5,  # Number of active monitoring services
            threats_today=threats_today,
            high_severity_threats=high_severity_threats,
            platforms_monitored=8,
            last_scan=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring stats")

@app.post("/api/vips", response_model=VIPProfile)
async def create_vip_profile(vip: VIPProfile):
    try:
        vip_dict = vip.dict()
        result = await database.vip_profiles.insert_one(vip_dict)
        
        # Broadcast new VIP added (convert datetime to string and remove ObjectId for JSON serialization)
        broadcast_data = vip_dict.copy()
        # Remove MongoDB ObjectId if present
        broadcast_data.pop('_id', None)
        for key, value in broadcast_data.items():
            if isinstance(value, datetime):
                broadcast_data[key] = value.isoformat()
        
        await manager.broadcast(json.dumps({
            "type": "vip_added",
            "data": broadcast_data
        }))
        
        return vip
    except Exception as e:
        logger.error(f"Error creating VIP profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create VIP profile")

@app.get("/api/vips", response_model=List[VIPProfile])
async def get_vip_profiles():
    try:
        profiles = []
        async for profile in database.vip_profiles.find({"status": "active"}):
            profiles.append(VIPProfile(**profile))
        return profiles
    except Exception as e:
        logger.error(f"Error getting VIP profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get VIP profiles")

@app.get("/api/vips/{vip_id}", response_model=VIPProfile)
async def get_vip_profile(vip_id: str):
    try:
        profile = await database.vip_profiles.find_one({"id": vip_id})
        if not profile:
            raise HTTPException(status_code=404, detail="VIP profile not found")
        return VIPProfile(**profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting VIP profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get VIP profile")

@app.put("/api/vips/{vip_id}", response_model=VIPProfile)
async def update_vip_profile(vip_id: str, vip: VIPProfile):
    try:
        vip.updated_at = datetime.utcnow()
        result = await database.vip_profiles.update_one(
            {"id": vip_id},
            {"$set": vip.dict()}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="VIP profile not found")
        return vip
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating VIP profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update VIP profile")

@app.delete("/api/vips/{vip_id}")
async def delete_vip_profile(vip_id: str):
    try:
        result = await database.vip_profiles.update_one(
            {"id": vip_id},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="VIP profile not found")
        return {"message": "VIP profile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting VIP profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete VIP profile")

@app.get("/api/threats", response_model=List[ThreatAlert])
async def get_threat_alerts(
    vip_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    try:
        filter_query = {}
        if vip_id:
            filter_query["vip_id"] = vip_id
        if severity:
            filter_query["severity"] = severity
        if status:
            filter_query["status"] = status
            
        threats = []
        async for threat in database.threat_alerts.find(filter_query).sort("created_at", -1).limit(limit):
            threats.append(ThreatAlert(**threat))
        return threats
    except Exception as e:
        logger.error(f"Error getting threat alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat alerts")

@app.post("/api/threats", response_model=ThreatAlert)
async def create_threat_alert(threat: ThreatAlert):
    try:
        threat_dict = threat.dict()
        result = await database.threat_alerts.insert_one(threat_dict)
        
        # Broadcast new threat alert (convert datetime to string and remove ObjectId for JSON serialization)
        broadcast_data = threat_dict.copy()
        # Remove MongoDB ObjectId if present
        broadcast_data.pop('_id', None)
        for key, value in broadcast_data.items():
            if isinstance(value, datetime):
                broadcast_data[key] = value.isoformat()
        
        await manager.broadcast(json.dumps({
            "type": "new_threat",
            "data": broadcast_data
        }))
        
        return threat
    except Exception as e:
        logger.error(f"Error creating threat alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create threat alert")

@app.put("/api/threats/{threat_id}/status")
async def update_threat_status(threat_id: str, status: str):
    try:
        result = await database.threat_alerts.update_one(
            {"id": threat_id},
            {"$set": {"status": status, "analyzed_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Threat alert not found")
        return {"message": "Threat status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threat status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update threat status")

@app.get("/api/analytics/threats-by-platform")
async def get_threats_by_platform():
    try:
        pipeline = [
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = []
        async for doc in database.threat_alerts.aggregate(pipeline):
            result.append({"platform": doc["_id"], "count": doc["count"]})
        return result
    except Exception as e:
        logger.error(f"Error getting threats by platform: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze threats by platform")

@app.get("/api/analytics/severity-distribution")
async def get_severity_distribution():
    try:
        pipeline = [
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = []
        async for doc in database.threat_alerts.aggregate(pipeline):
            result.append({"severity": doc["_id"], "count": doc["count"]})
        return result
    except Exception as e:
        logger.error(f"Error getting severity distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze severity distribution")

@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get current monitoring service status"""
    try:
        if monitoring_service:
            status = await monitoring_service.get_monitoring_status()
            return status
        else:
            return {
                "is_running": False,
                "active_monitors": [],
                "total_vips": await database.vip_profiles.count_documents({"status": "active"}),
                "threats_24h": await database.threat_alerts.count_documents({
                    "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
                }),
                "error": "Monitoring service not initialized"
            }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")

@app.post("/api/monitoring/scan/{vip_id}")
async def manual_scan_vip(vip_id: str):
    """Manually trigger a scan for a specific VIP"""
    try:
        if monitoring_service:
            result = await monitoring_service.manual_scan_vip(vip_id)
            return result
        else:
            return {"error": "Monitoring service not available"}
    except Exception as e:
        logger.error(f"Error in manual VIP scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan VIP")

@app.get("/api/threats/recent")
async def get_recent_threats(hours: int = 24, limit: int = 50):
    """Get recent threats within specified time window"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        threats = []
        async for threat in database.threat_alerts.find({
            "created_at": {"$gte": cutoff_time}
        }).sort("created_at", -1).limit(limit):
            threats.append(ThreatAlert(**threat))
        return threats
    except Exception as e:
        logger.error(f"Error getting recent threats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent threats")

@app.delete("/api/admin/threats")
async def clear_threats(confirm: bool = False):
    """Dangerous: clears all stored threats. Call with ?confirm=true"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to proceed")
    try:
        result = await database.threat_alerts.delete_many({})
        return {"deleted": result.deleted_count}
    except Exception as e:
        logger.error(f"Error clearing threats: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear threats")

@app.get("/api/analytics/threat-timeline")
async def get_threat_timeline(days: int = 7):
    """Get threat count timeline for the past N days"""
    try:
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        result = []
        async for doc in database.threat_alerts.aggregate(pipeline):
            date_str = f"{doc['_id']['year']}-{doc['_id']['month']:02d}-{doc['_id']['day']:02d}"
            result.append({"date": date_str, "count": doc["count"]})
        
        return result
    except Exception as e:
        logger.error(f"Error getting threat timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat timeline")

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(f"Connected: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Import monitoring service
from backend.monitoring.service import get_monitoring_service
from backend.monitoring.ai_analyzer import analyze_content_for_threats

# Global monitoring service
monitoring_service = None

# Start real monitoring service
@app.on_event("startup")
async def start_monitoring():
    global monitoring_service
    try:
        monitoring_service = get_monitoring_service(database)
        await monitoring_service.start_monitoring()
        logger.info("Real-time VIP monitoring service started")
    except Exception as e:
        logger.error(f"Failed to start monitoring service: {e}")
        # Fallback to simulation if real monitoring fails and enabled
        if os.getenv('USE_SIMULATOR', 'false').lower() == 'true':
            asyncio.create_task(simulate_monitoring())
        else:
            logger.info("Simulator disabled by USE_SIMULATOR env; skipping fallback simulation")

@app.on_event("shutdown")
async def stop_monitoring():
    global monitoring_service
    if monitoring_service:
        await monitoring_service.stop_monitoring()

# Background task to simulate monitoring (fallback)
async def simulate_monitoring():
    """Simulate threat detection for demo purposes"""
    if os.getenv('USE_SIMULATOR', 'false').lower() != 'true':
        logger.info("Simulator disabled by USE_SIMULATOR env; simulate_monitoring will not run")
        return
    import random
    
    platforms = ["twitter", "reddit", "instagram", "telegram", "youtube"]
    threat_types = ["impersonation", "misinformation", "harassment", "data_leak", "fake_profile"]
    severities = ["low", "medium", "high", "critical"]
    
    while True:
        try:
            # Get active VIPs
            vips = []
            async for vip in database.vip_profiles.find({"status": "active"}):
                vips.append(vip)
            
            if vips and random.random() < 0.1:  # 10% chance of generating a threat (reduced for demo)
                vip = random.choice(vips)
                platform = random.choice(platforms)
                threat_type = random.choice(threat_types)
                severity = random.choice(severities)
                
                threat = ThreatAlert(
                    vip_id=vip["id"],
                    vip_name=vip["name"],
                    platform=platform,
                    threat_type=threat_type,
                    severity=severity,
                    confidence_score=random.uniform(0.6, 0.95),
                    content=f"Demo: {threat_type} threat detected for {vip['name']} on {platform}. This is simulated data for demonstration.",
                    source_url=f"https://{platform}.com/demo_threat_{random.randint(1000, 9999)}",
                    evidence={"type": "demo", "screenshot": "base64_demo_data", "metadata": {"detected_at": datetime.utcnow().isoformat()}}
                )
                
                await database.threat_alerts.insert_one(threat.dict())
                
                # Broadcast new threat
                await manager.broadcast(json.dumps({
                    "type": "new_threat",
                    "data": threat.dict()
                }))
                
                logger.info(f"Demo threat generated: {threat_type} for {vip['name']}")
                
        except Exception as e:
            logger.error(f"Error in monitoring simulation: {e}")
            
        await asyncio.sleep(45)  # Check every 45 seconds

# --- Serve built frontend (production) ---
# If frontend has been built with `yarn build`, serve `frontend/dist` at '/'
try:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
    INDEX_HTML = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.isdir(FRONTEND_DIST) and os.path.isfile(INDEX_HTML):
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
except Exception as _e:
    # Non-fatal if frontend isn't built yet
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""
Main monitoring service that coordinates all platform monitors
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
from motor.motor_asyncio import AsyncIOMotorClient

from .platforms import get_active_monitors
from .ai_analyzer import analyze_content_for_threats

logger = logging.getLogger(__name__)

class VIPMonitoringService:
    """Main service for coordinating VIP monitoring across platforms"""
    
    def __init__(self, database):
        self.database = database
        self.monitors = get_active_monitors()
        self.is_running = False
        self.monitoring_tasks = []
        
    async def start_monitoring(self):
        """Start the monitoring service"""
        if self.is_running:
            logger.warning("Monitoring service is already running")
            return
            
        self.is_running = True
        logger.info(f"Starting VIP monitoring service with {len(self.monitors)} active monitors")
        
        # Start monitoring task for each platform
        for monitor in self.monitors:
            task = asyncio.create_task(self._platform_monitoring_loop(monitor))
            self.monitoring_tasks.append(task)
        
        # Start periodic cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_old_threats())
        self.monitoring_tasks.append(cleanup_task)
        
        logger.info("VIP monitoring service started successfully")
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        logger.info("VIP monitoring service stopped")
    
    async def _platform_monitoring_loop(self, monitor):
        """Main monitoring loop for a specific platform"""
        platform_name = monitor.platform_name
        interval = int(os.getenv('MONITORING_INTERVAL_SECONDS', '300'))  # 5 minutes default
        
        logger.info(f"Starting monitoring loop for {platform_name} (interval: {interval}s)")
        
        while self.is_running:
            try:
                await self._monitor_platform(monitor)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info(f"Monitoring loop for {platform_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {platform_name} monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _monitor_platform(self, monitor):
        """Monitor all VIPs on a specific platform"""
        platform_name = monitor.platform_name
        
        try:
            # Get all active VIPs
            vips = []
            async for vip in self.database.vip_profiles.find({"status": "active"}):
                # Check if this platform is enabled for the VIP
                if not vip.get('platforms') or platform_name in vip.get('platforms', []):
                    vips.append(vip)
            
            logger.info(f"Monitoring {len(vips)} VIPs on {platform_name}")
            
            # Monitor each VIP
            for vip in vips:
                try:
                    await self._monitor_vip_on_platform(monitor, vip)
                except Exception as e:
                    logger.error(f"Error monitoring VIP {vip.get('name')} on {platform_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in platform monitoring for {platform_name}: {e}")
    
    async def _monitor_vip_on_platform(self, monitor, vip_profile):
        """Monitor a specific VIP on a platform"""
        vip_name = vip_profile.get('name', 'Unknown')
        platform_name = monitor.platform_name
        
        try:
            # Get threats from platform monitor
            threats = await monitor.monitor_vip(vip_profile)
            
            if threats:
                logger.info(f"Found {len(threats)} potential threats for {vip_name} on {platform_name}")
                
                # Analyze each threat with AI
                for threat_data in threats:
                    await self._process_threat(threat_data, vip_profile)
                    
        except Exception as e:
            logger.error(f"Error monitoring {vip_name} on {platform_name}: {e}")
    
    async def _process_threat(self, threat_data: Dict[str, Any], vip_profile: Dict[str, Any]):
        """Process and analyze a potential threat"""
        try:
            content = threat_data.get('content', '')
            vip_name = vip_profile.get('name', '')
            platform = threat_data.get('platform', 'unknown')
            
            # Skip if we've already processed this exact content recently
            existing_threat = await self.database.threat_alerts.find_one({
                "content": content,
                "vip_id": threat_data.get('vip_id'),
                "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            })
            
            if existing_threat:
                return
            
            # Analyze threat with AI
            ai_analysis = await analyze_content_for_threats(content, vip_name, platform)

            # Add misinformation/impersonation heuristics and evidence scaffold
            from .ai_analyzer import ai_analyzer as _analyzer_instance
            flags = _analyzer_instance._detect_misinfo_impersonation(content, vip_name)  # internal heuristic
            
            # Update threat data with AI analysis
            threat_data.update({
                'threat_type': ai_analysis.get('threat_type', threat_data.get('threat_type', 'unknown')),
                'severity': ai_analysis.get('severity', threat_data.get('severity', 'low')),
                'confidence_score': ai_analysis.get('confidence', threat_data.get('confidence_score', 0.5)),
                'ai_analysis': ai_analysis.get('analysis_details', {}),
                'recommendations': ai_analysis.get('recommendations', []),
                'analyzed_at': datetime.utcnow()
            })

            # Attach misinformation/impersonation evidence
            threat_data.setdefault('evidence', {})
            threat_data['evidence'].update({
                'is_misinformation': flags.get('is_misinformation', False),
                'is_impersonation': flags.get('is_impersonation', False),
                'misinformation_reasons': flags.get('misinformation_reasons', []),
                'impersonation_reasons': flags.get('impersonation_reasons', []),
                'source_url': threat_data.get('source_url'),
                'platform': platform,
            })
            
            # Only save if threat score is above threshold
            # Enrich with basic NLP (NER, sentiment) for context
            try:
                from .ai_analyzer import ai_analyzer as _analyzer_instance
                sentiment = await _analyzer_instance._analyze_sentiment(content)
                entities = _analyzer_instance._extract_entities(content)
                threat_data.setdefault('evidence', {})
                threat_data['evidence'].update({
                    'sentiment': sentiment,
                    'entities': entities[:10]
                })
            except Exception:
                pass

            threat_threshold = float(os.getenv('THREAT_CONFIDENCE_THRESHOLD', '0.7'))
            if ai_analysis.get('threat_score', 0) >= threat_threshold:
                
                # Save to database
                await self.database.threat_alerts.insert_one(threat_data)
                
                logger.info(f"New threat detected: {threat_data['threat_type']} ({threat_data['severity']}) for {vip_name}")
                
                # Send real-time notification if needed
                await self._send_threat_notification(threat_data)
                
        except Exception as e:
            logger.error(f"Error processing threat: {e}")
    
    async def _send_threat_notification(self, threat_data: Dict[str, Any]):
        """Send real-time threat notification"""
        try:
            # This would integrate with WebSocket manager or notification service
            # For now, just log high-severity threats
            if threat_data.get('severity') in ['high', 'critical']:
                logger.warning(f"HIGH SEVERITY THREAT: {threat_data['threat_type']} for {threat_data['vip_name']} on {threat_data['platform']}")
                
                # Here you could add:
                # - Email notifications
                # - SMS alerts
                # - Webhook calls
                # - Push notifications
                
        except Exception as e:
            logger.error(f"Error sending threat notification: {e}")
    
    async def _cleanup_old_threats(self):
        """Periodically clean up old threat data"""
        while self.is_running:
            try:
                # Clean up threats older than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                result = await self.database.threat_alerts.delete_many({
                    "created_at": {"$lt": cutoff_date},
                    "status": "resolved"
                })
                
                if result.deleted_count > 0:
                    logger.info(f"Cleaned up {result.deleted_count} old resolved threats")
                
                # Sleep for 24 hours before next cleanup
                await asyncio.sleep(86400)
                
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        active_monitors = []
        for monitor in self.monitors:
            active_monitors.append({
                'platform': monitor.platform_name,
                'enabled': monitor.is_enabled,
                'api_configured': monitor.is_api_configured()
            })
        
        # Get VIP count
        vip_count = await self.database.vip_profiles.count_documents({"status": "active"})
        
        # Get recent threat count
        recent_threats = await self.database.threat_alerts.count_documents({
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        })
        
        return {
            'is_running': self.is_running,
            'active_monitors': active_monitors,
            'total_vips': vip_count,
            'threats_24h': recent_threats,
            'last_check': datetime.utcnow().isoformat()
        }
    
    async def manual_scan_vip(self, vip_id: str) -> Dict[str, Any]:
        """Manually trigger a scan for a specific VIP"""
        try:
            # Get VIP profile
            vip = await self.database.vip_profiles.find_one({"id": vip_id, "status": "active"})
            if not vip:
                return {"error": "VIP not found or inactive"}
            
            all_threats = []
            
            # Scan across all active monitors
            for monitor in self.monitors:
                try:
                    threats = await monitor.monitor_vip(vip)
                    for threat_data in threats:
                        await self._process_threat(threat_data, vip)
                        all_threats.append(threat_data)
                except Exception as e:
                    logger.error(f"Error in manual scan on {monitor.platform_name}: {e}")
            
            return {
                "vip_name": vip.get('name'),
                "platforms_scanned": len(self.monitors),
                "threats_found": len(all_threats),
                "scan_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual VIP scan: {e}")
            return {"error": str(e)}

# Global monitoring service instance
monitoring_service = None

def get_monitoring_service(database) -> VIPMonitoringService:
    """Get or create the global monitoring service instance"""
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = VIPMonitoringService(database)
    return monitoring_service
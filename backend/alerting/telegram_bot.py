#!/usr/bin/env python3
"""
Phase 3: Telegram Bot Alerting System
Real-time notifications for VIP threat detection
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TelegramAlerter:
    """Telegram bot for sending threat alerts"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_ids = self._load_chat_ids()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.enabled = bool(self.bot_token)
        
        if not self.enabled:
            logger.warning("Telegram bot disabled - TELEGRAM_BOT_TOKEN not configured")
    
    def _load_chat_ids(self) -> Dict[str, List[str]]:
        """Load chat IDs for different alert types"""
        try:
            # Priority-based chat routing
            return {
                "critical": os.getenv("TELEGRAM_CRITICAL_CHATS", "").split(","),
                "high": os.getenv("TELEGRAM_HIGH_CHATS", "").split(","),
                "medium": os.getenv("TELEGRAM_MEDIUM_CHATS", "").split(","),
                "general": os.getenv("TELEGRAM_GENERAL_CHAT", "").split(",")
            }
        except:
            return {"general": []}
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send threat alert via Telegram"""
        if not self.enabled:
            logger.warning("Telegram alerting disabled")
            return False
        
        try:
            # Format alert message
            message = self._format_alert_message(alert_data)
            
            # Determine chat IDs based on priority
            priority = alert_data.get('priority', 'medium').lower()
            chat_ids = self.chat_ids.get(priority, self.chat_ids.get('general', []))
            
            # Send to all relevant chats
            success = True
            for chat_id in chat_ids:
                if chat_id.strip():
                    if not self._send_message(chat_id.strip(), message):
                        success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def _format_alert_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert data into Telegram message"""
        try:
            # Extract key information
            alert_id = alert_data.get('alert_id', 'Unknown')
            detection_type = alert_data.get('detection_type', 'Unknown')
            threat_score = alert_data.get('threat_score', 0.0)
            platform = alert_data.get('platform', 'Unknown')
            username = alert_data.get('username', 'Unknown')
            vip_mentioned = alert_data.get('vip_mentioned', 'None')
            post_url = alert_data.get('post_url', '')
            
            # Priority emoji
            priority = alert_data.get('priority', 'medium').lower()
            priority_emoji = {
                'critical': '🚨',
                'high': '⚠️',
                'medium': '⚡',
                'low': 'ℹ️'
            }.get(priority, '⚡')
            
            # Detection type emoji
            type_emoji = {
                'misinformation': '📰',
                'fake_profile': '👤',
                'campaign': '📢',
                'image_manipulation': '🖼️'
            }.get(detection_type.lower(), '🔍')
            
            # Build message
            message = f"{priority_emoji} *VIP THREAT ALERT*\n\n"
            message += f"{type_emoji} *Type:* {detection_type.title()}\n"
            message += f"🎯 *Threat Score:* {threat_score:.2f}\n"
            message += f"📱 *Platform:* {platform}\n"
            message += f"👤 *User:* @{username}\n"
            
            if vip_mentioned and vip_mentioned != 'None':
                message += f"🎭 *VIP Mentioned:* {vip_mentioned}\n"
            
            message += f"🆔 *Alert ID:* `{alert_id}`\n"
            message += f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Add reason if available
            reason = alert_data.get('reason_flagged', '')
            if reason:
                message += f"\n📋 *Reason:* {reason[:200]}{'...' if len(reason) > 200 else ''}\n"
            
            # Add post URL if available
            if post_url:
                message += f"\n🔗 [View Post]({post_url})\n"
            
            # Add verification link
            verification_url = f"http://localhost:3000/verify/{alert_id}"  # Adjust URL as needed
            message += f"✅ [Verify Alert]({verification_url})"
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to format alert message: {e}")
            return f"🚨 VIP Threat Alert\nAlert ID: {alert_data.get('alert_id', 'Unknown')}\nError formatting message."
    
    def _send_message(self, chat_id: str, message: str) -> bool:
        """Send message to specific chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_summary_report(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily/weekly summary report"""
        if not self.enabled:
            return False
        
        try:
            message = self._format_summary_message(summary_data)
            
            # Send to general chat
            general_chats = self.chat_ids.get('general', [])
            success = True
            
            for chat_id in general_chats:
                if chat_id.strip():
                    if not self._send_message(chat_id.strip(), message):
                        success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send summary report: {e}")
            return False
    
    def _format_summary_message(self, summary_data: Dict[str, Any]) -> str:
        """Format summary report message"""
        try:
            period = summary_data.get('period', 'Daily')
            total_alerts = summary_data.get('total_alerts', 0)
            confirmed_threats = summary_data.get('confirmed_threats', 0)
            dismissed_alerts = summary_data.get('dismissed_alerts', 0)
            pending_verification = summary_data.get('pending_verification', 0)
            
            detection_breakdown = summary_data.get('detection_breakdown', {})
            platform_breakdown = summary_data.get('platform_breakdown', {})
            
            message = f"📊 *{period} VIP Threat Summary*\n\n"
            message += f"🎯 *Total Alerts:* {total_alerts}\n"
            message += f"✅ *Confirmed Threats:* {confirmed_threats}\n"
            message += f"❌ *Dismissed:* {dismissed_alerts}\n"
            message += f"⏳ *Pending Review:* {pending_verification}\n\n"
            
            if detection_breakdown:
                message += "*Detection Types:*\n"
                for det_type, count in detection_breakdown.items():
                    emoji = {
                        'misinformation': '📰',
                        'fake_profile': '👤',
                        'campaign': '📢',
                        'image_manipulation': '🖼️'
                    }.get(det_type.lower(), '🔍')
                    message += f"{emoji} {det_type.title()}: {count}\n"
                message += "\n"
            
            if platform_breakdown:
                message += "*Platforms:*\n"
                for platform, count in platform_breakdown.items():
                    message += f"📱 {platform}: {count}\n"
            
            message += f"\n⏰ *Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to format summary message: {e}")
            return f"📊 {summary_data.get('period', 'Daily')} Summary\nError formatting report."
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.enabled:
            logger.error("Telegram bot not configured")
            return False
        
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Telegram bot connected: {bot_info.get('result', {}).get('username', 'Unknown')}")
                return True
            else:
                logger.error(f"Telegram bot test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False

class AlertingSystem:
    """Main alerting system coordinator"""
    
    def __init__(self):
        self.telegram = TelegramAlerter()
        self.alert_history = []
        self.max_history = 1000
    
    def send_threat_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send threat alert through all configured channels"""
        success = True
        
        # Add to history
        self._add_to_history(alert_data)
        
        # Send via Telegram
        if not self.telegram.send_alert(alert_data):
            success = False
        
        # TODO: Add other alerting channels (email, webhook, etc.)
        
        return success
    
    def _add_to_history(self, alert_data: Dict[str, Any]):
        """Add alert to history"""
        alert_data['sent_at'] = datetime.now().isoformat()
        self.alert_history.append(alert_data)
        
        # Trim history if too long
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return self.alert_history[-limit:]
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily summary report"""
        return self.telegram.send_summary_report(summary_data)
    
    def test_all_channels(self) -> Dict[str, bool]:
        """Test all alerting channels"""
        return {
            "telegram": self.telegram.test_connection()
        }

# Global alerting system
_alerting_system = None

def get_alerting_system() -> AlertingSystem:
    """Get global alerting system instance"""
    global _alerting_system
    if _alerting_system is None:
        _alerting_system = AlertingSystem()
    return _alerting_system

def send_threat_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Convenience function to send threat alert
    
    Args:
        alert_data: Alert information including threat details
        
    Returns:
        True if alert sent successfully
    """
    alerting = get_alerting_system()
    return alerting.send_threat_alert(alert_data)

#!/usr/bin/env python3
"""
Simple Demo Server for VIP Dashboard - Guaranteed to Work
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from datetime import datetime
import threading
import webbrowser

class DemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            stats = {
                "total_vips": 3,
                "threats_today": 12,
                "high_severity_threats": 4,
                "platforms_monitored": 8,
                "last_scan": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(stats).encode())
            return
            
        elif self.path.startswith('/api/threats'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            threats = [
                {
                    "id": "threat_1",
                    "vip_name": "John Politician",
                    "threat_type": "impersonation",
                    "platform": "twitter",
                    "source_url": "https://twitter.com/fake_account/status/123456",
                    "content": "I am the real John Politician! Follow my official account for exclusive updates.",
                    "confidence_score": 0.87,
                    "severity": "high",
                    "created_at": datetime.now().isoformat(),
                    "evidence": {
                        "screenshot_url": "https://screenshots.protego.com/fake_1.png",
                        "is_impersonation": True,
                        "is_misinformation": False
                    }
                },
                {
                    "id": "threat_2", 
                    "vip_name": "Jane Celebrity",
                    "threat_type": "misinformation",
                    "platform": "facebook",
                    "source_url": "https://facebook.com/fake_news/posts/789012",
                    "content": "BREAKING: Jane Celebrity caught in major scandal! Leaked photos reveal shocking truth.",
                    "confidence_score": 0.92,
                    "severity": "critical",
                    "created_at": datetime.now().isoformat(),
                    "evidence": {
                        "screenshot_url": "https://screenshots.protego.com/misinformation_1.png",
                        "is_misinformation": True,
                        "is_impersonation": False,
                        "cluster_id": "campaign_001"
                    }
                },
                {
                    "id": "threat_3",
                    "vip_name": "Tech CEO Mike", 
                    "threat_type": "data_leak",
                    "platform": "pastebin",
                    "source_url": "https://pastebin.com/xyz789abc",
                    "content": "Tech CEO Mike private data dump: Email: mike@techcorp.com Password: leaked_password_123",
                    "confidence_score": 0.95,
                    "severity": "critical",
                    "created_at": datetime.now().isoformat(),
                    "evidence": {
                        "screenshot_url": "https://screenshots.protego.com/data_leak_1.png",
                        "data_types": ["email", "password", "documents"]
                    }
                }
            ]
            self.wfile.write(json.dumps(threats).encode())
            return
            
        elif self.path == '/api/threats/by-platform':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = [
                {"platform": "twitter", "count": 5},
                {"platform": "facebook", "count": 3},
                {"platform": "telegram", "count": 2},
                {"platform": "pastebin", "count": 2}
            ]
            self.wfile.write(json.dumps(data).encode())
            return
            
        elif self.path == '/api/threats/by-severity':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = [
                {"severity": "critical", "count": 4},
                {"severity": "high", "count": 5},
                {"severity": "medium", "count": 2},
                {"severity": "low", "count": 1}
            ]
            self.wfile.write(json.dumps(data).encode())
            return
            
        elif self.path == '/api/threats/timeline':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = [
                {"date": "2024-01-01", "count": 2},
                {"date": "2024-01-02", "count": 3},
                {"date": "2024-01-03", "count": 1},
                {"date": "2024-01-04", "count": 4},
                {"date": "2024-01-05", "count": 2}
            ]
            self.wfile.write(json.dumps(data).encode())
            return
            
        # Serve frontend files
        if self.path == '/' or self.path == '/index.html':
            try:
                # Try to serve from frontend/dist
                frontend_path = '../frontend/dist/index.html'
                if os.path.exists(frontend_path):
                    with open(frontend_path, 'r') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(content.encode())
                    return
                else:
                    # Fallback: serve a simple HTML page
                    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>VIP Threat Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .kpi { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e9ecef; }
        .kpi-value { font-size: 24px; font-weight: bold; color: #495057; }
        .kpi-label { font-size: 12px; color: #6c757d; margin-top: 5px; }
        .threat-list { background: white; border: 1px solid #e9ecef; border-radius: 8px; }
        .threat-item { padding: 15px; border-bottom: 1px solid #e9ecef; }
        .threat-item:last-child { border-bottom: none; }
        .severity-critical { border-left: 4px solid #dc3545; }
        .severity-high { border-left: 4px solid #fd7e14; }
        .severity-medium { border-left: 4px solid #ffc107; }
        .severity-low { border-left: 4px solid #28a745; }
        .badge { padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
        .badge-critical { background: #dc3545; color: white; }
        .badge-high { background: #fd7e14; color: white; }
        .badge-medium { background: #ffc107; color: black; }
        .badge-low { background: #28a745; color: white; }
        .platform-badge { background: #6c757d; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 VIP Threat & Misinformation Dashboard</h1>
            <p>Real-time monitoring across multiple platforms</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi">
                <div class="kpi-value">3</div>
                <div class="kpi-label">Active VIPs</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">12</div>
                <div class="kpi-label">Threats Today</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">4</div>
                <div class="kpi-label">High Severity</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">8</div>
                <div class="kpi-label">Platforms</div>
            </div>
        </div>
        
        <h2>🚨 Recent Threats</h2>
        <div class="threat-list">
            <div class="threat-item severity-high">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong>John Politician</strong>
                        <span class="platform-badge">twitter</span>
                        <span class="badge badge-high">HIGH</span>
                        <span style="font-size: 12px; color: #6c757d;">87% confidence</span>
                    </div>
                    <span style="font-size: 12px; color: #6c757d;">15 minutes ago</span>
                </div>
                <div style="font-size: 12px; color: #495057; margin-bottom: 8px;">impersonation</div>
                <div>I am the real John Politician! Follow my official account for exclusive updates.</div>
                <div style="margin-top: 10px;">
                    <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px;">impersonation</span>
                    <a href="#" style="margin-left: 10px; font-size: 12px;">View Source</a>
                    <a href="#" style="margin-left: 10px; font-size: 12px;">Screenshot</a>
                </div>
            </div>
            
            <div class="threat-item severity-critical">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong>Jane Celebrity</strong>
                        <span class="platform-badge">facebook</span>
                        <span class="badge badge-critical">CRITICAL</span>
                        <span style="font-size: 12px; color: #6c757d;">92% confidence</span>
                    </div>
                    <span style="font-size: 12px; color: #6c757d;">8 minutes ago</span>
                </div>
                <div style="font-size: 12px; color: #495057; margin-bottom: 8px;">misinformation</div>
                <div>BREAKING: Jane Celebrity caught in major scandal! Leaked photos reveal shocking truth.</div>
                <div style="margin-top: 10px;">
                    <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px;">misinformation</span>
                    <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px;">cluster:campaign_001</span>
                    <a href="#" style="margin-left: 10px; font-size: 12px;">View Source</a>
                    <a href="#" style="margin-left: 10px; font-size: 12px;">Screenshot</a>
                </div>
            </div>
            
            <div class="threat-item severity-critical">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong>Tech CEO Mike</strong>
                        <span class="platform-badge">pastebin</span>
                        <span class="badge badge-critical">CRITICAL</span>
                        <span style="font-size: 12px; color: #6c757d;">95% confidence</span>
                    </div>
                    <span style="font-size: 12px; color: #6c757d;">3 minutes ago</span>
                </div>
                <div style="font-size: 12px; color: #495057; margin-bottom: 8px;">data_leak</div>
                <div>Tech CEO Mike private data dump: Email: mike@techcorp.com Password: leaked_password_123</div>
                <div style="margin-top: 10px;">
                    <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px;">data_leak</span>
                    <a href="#" style="margin-left: 10px; font-size: 12px;">View Source</a>
                    <a href="#" style="margin-left: 10px; font-size: 12px;">Screenshot</a>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 30px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div style="background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px;">
                <h3>📊 By Platform</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>Twitter: 5 threats</li>
                    <li>Facebook: 3 threats</li>
                    <li>Telegram: 2 threats</li>
                    <li>Pastebin: 2 threats</li>
                </ul>
            </div>
            <div style="background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px;">
                <h3>⚠️ By Severity</h3>
                <ul style="list-style: none; padding: 0;">
                    <li><span class="badge badge-critical">CRITICAL</span> 4 threats</li>
                    <li><span class="badge badge-high">HIGH</span> 5 threats</li>
                    <li><span class="badge badge-medium">MEDIUM</span> 2 threats</li>
                    <li><span class="badge badge-low">LOW</span> 1 threat</li>
                </ul>
            </div>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px;">
            <h4>🎯 System Status: OPERATIONAL</h4>
            <p><strong>Multi-Source Monitoring:</strong> Twitter, Facebook, Instagram, LinkedIn, Telegram, Pastebin, GitHub, YouTube</p>
            <p><strong>Detection Capabilities:</strong> Impersonation, Misinformation, Data Leaks, Deepfakes, Coordinated Campaigns</p>
            <p><strong>Evidence Collection:</strong> Screenshots, Source URLs, Metadata, Confidence Scoring</p>
        </div>
    </div>
</body>
</html>
                    """
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(html_content.encode())
                    return
            except Exception as e:
                print(f"Error serving frontend: {e}")
        
        # Default handler
        super().do_GET()

def start_demo_server():
    """Start the demo server"""
    port = 8003
    server_address = ('', port)
    httpd = HTTPServer(server_address, DemoHandler)
    
    print(f"🚀 VIP Dashboard Demo Server Starting...")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🎬 Perfect for video demo!")
    print(f"Press Ctrl+C to stop")
    
    # Open browser automatically
    threading.Timer(2, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    start_demo_server()

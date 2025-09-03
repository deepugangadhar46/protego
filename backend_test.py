#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Protego VIP Threat Monitoring System
Tests all API endpoints, CRUD operations, and data integrity
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

class ProtegoAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_vip_id = None
        self.test_threat_id = None
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {details}")
        else:
            print(f"❌ {name}: FAILED {details}")
        return success

    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}
            
            return response.status_code < 400, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        success, response = self.make_request('GET', '/api/health')
        
        if success and isinstance(response, dict):
            required_fields = ['status', 'timestamp', 'service', 'version']
            has_all_fields = all(field in response for field in required_fields)
            is_healthy = response.get('status') == 'healthy'
            
            return self.log_test(
                "Health Check", 
                success and has_all_fields and is_healthy,
                f"Status: {response.get('status', 'unknown')}"
            )
        
        return self.log_test("Health Check", False, f"Response: {response}")

    def test_stats_endpoint(self):
        """Test /api/stats endpoint"""
        success, response = self.make_request('GET', '/api/stats')
        
        if success and isinstance(response, dict):
            required_fields = ['total_vips', 'active_monitors', 'threats_today', 'high_severity_threats', 'platforms_monitored']
            has_all_fields = all(field in response for field in required_fields)
            
            return self.log_test(
                "Stats Endpoint", 
                success and has_all_fields,
                f"VIPs: {response.get('total_vips', 0)}, Threats Today: {response.get('threats_today', 0)}"
            )
        
        return self.log_test("Stats Endpoint", False, f"Response: {response}")

    def test_vip_crud_operations(self):
        """Test VIP CRUD operations"""
        # Test GET VIPs (should work even if empty)
        success, vips = self.make_request('GET', '/api/vips')
        get_success = self.log_test("Get VIPs", success, f"Found {len(vips) if isinstance(vips, list) else 0} VIPs")
        
        # Test CREATE VIP
        test_vip = {
            "name": "Test VIP User",
            "title": "Test CEO",
            "platforms": ["twitter", "instagram"],
            "keywords": ["test", "demo"],
            "risk_level": "medium"
        }
        
        success, response = self.make_request('POST', '/api/vips', test_vip)
        if success and isinstance(response, dict) and 'id' in response:
            self.test_vip_id = response['id']
            create_success = self.log_test("Create VIP", True, f"Created VIP with ID: {self.test_vip_id}")
        else:
            create_success = self.log_test("Create VIP", False, f"Response: {response}")
        
        # Test GET specific VIP
        if self.test_vip_id:
            success, response = self.make_request('GET', f'/api/vips/{self.test_vip_id}')
            get_one_success = self.log_test(
                "Get Specific VIP", 
                success and response.get('name') == test_vip['name'],
                f"Retrieved VIP: {response.get('name', 'unknown')}"
            )
        else:
            get_one_success = self.log_test("Get Specific VIP", False, "No VIP ID to test")
        
        # Test UPDATE VIP
        if self.test_vip_id:
            updated_vip = test_vip.copy()
            updated_vip['title'] = "Updated Test CEO"
            
            success, response = self.make_request('PUT', f'/api/vips/{self.test_vip_id}', updated_vip)
            update_success = self.log_test(
                "Update VIP", 
                success and response.get('title') == updated_vip['title'],
                f"Updated title to: {response.get('title', 'unknown')}"
            )
        else:
            update_success = self.log_test("Update VIP", False, "No VIP ID to test")
        
        return get_success and create_success and get_one_success and update_success

    def test_threat_operations(self):
        """Test threat-related operations"""
        # Test GET threats
        success, threats = self.make_request('GET', '/api/threats')
        get_success = self.log_test("Get Threats", success, f"Found {len(threats) if isinstance(threats, list) else 0} threats")
        
        # Test GET threats with filters
        success, filtered_threats = self.make_request('GET', '/api/threats', params={'limit': 10})
        filter_success = self.log_test("Get Threats with Limit", success, f"Limited to {len(filtered_threats) if isinstance(filtered_threats, list) else 0} threats")
        
        # Test CREATE threat (if we have a VIP)
        if self.test_vip_id:
            test_threat = {
                "vip_id": self.test_vip_id,
                "vip_name": "Test VIP User",
                "platform": "twitter",
                "threat_type": "test_threat",
                "severity": "medium",
                "confidence_score": 0.85,
                "content": "This is a test threat for API testing",
                "source_url": "https://twitter.com/test_threat_123",
                "evidence": {"type": "test", "automated": True}
            }
            
            success, response = self.make_request('POST', '/api/threats', test_threat)
            if success and isinstance(response, dict) and 'id' in response:
                self.test_threat_id = response['id']
                create_success = self.log_test("Create Threat", True, f"Created threat with ID: {self.test_threat_id}")
            else:
                create_success = self.log_test("Create Threat", False, f"Response: {response}")
        else:
            create_success = self.log_test("Create Threat", False, "No VIP ID available")
        
        # Test UPDATE threat status
        if self.test_threat_id:
            success, response = self.make_request('PUT', f'/api/threats/{self.test_threat_id}/status', params={'status': 'investigating'})
            update_success = self.log_test("Update Threat Status", success, f"Status update response: {response}")
        else:
            update_success = self.log_test("Update Threat Status", False, "No threat ID to test")
        
        return get_success and filter_success and create_success and update_success

    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        # Test threats by platform
        success, platforms = self.make_request('GET', '/api/analytics/threats-by-platform')
        platform_success = self.log_test(
            "Threats by Platform Analytics", 
            success,
            f"Platform data: {len(platforms) if isinstance(platforms, list) else 0} platforms"
        )
        
        # Test severity distribution
        success, severity = self.make_request('GET', '/api/analytics/severity-distribution')
        severity_success = self.log_test(
            "Severity Distribution Analytics", 
            success,
            f"Severity data: {len(severity) if isinstance(severity, list) else 0} levels"
        )
        
        # Test threat timeline
        success, timeline = self.make_request('GET', '/api/analytics/threat-timeline')
        timeline_success = self.log_test(
            "Threat Timeline Analytics", 
            success,
            f"Timeline data: {len(timeline) if isinstance(timeline, list) else 0} data points"
        )
        
        return platform_success and severity_success and timeline_success

    def test_monitoring_endpoints(self):
        """Test monitoring-specific endpoints"""
        # Test monitoring status
        success, status = self.make_request('GET', '/api/monitoring/status')
        status_success = self.log_test(
            "Monitoring Status", 
            success,
            f"Monitoring active: {status.get('is_running', False) if isinstance(status, dict) else 'unknown'}"
        )
        
        # Test manual VIP scan (if we have a VIP)
        if self.test_vip_id:
            success, scan_result = self.make_request('POST', f'/api/monitoring/scan/{self.test_vip_id}')
            scan_success = self.log_test("Manual VIP Scan", success, f"Scan result: {scan_result}")
        else:
            scan_success = self.log_test("Manual VIP Scan", False, "No VIP ID to test")
        
        # Test recent threats
        success, recent = self.make_request('GET', '/api/threats/recent')
        recent_success = self.log_test(
            "Recent Threats", 
            success,
            f"Recent threats: {len(recent) if isinstance(recent, list) else 0}"
        )
        
        return status_success and scan_success and recent_success

    def test_data_integrity(self):
        """Test data integrity and relationships"""
        # Get all VIPs and threats to check relationships
        vip_success, vips = self.make_request('GET', '/api/vips')
        threat_success, threats = self.make_request('GET', '/api/threats')
        
        if not (vip_success and threat_success):
            return self.log_test("Data Integrity", False, "Could not fetch data for integrity check")
        
        # Check if threats reference valid VIPs
        vip_ids = {vip['id'] for vip in vips} if isinstance(vips, list) else set()
        threat_vip_ids = {threat['vip_id'] for threat in threats} if isinstance(threats, list) else set()
        
        # Check for orphaned threats (threats without valid VIP references)
        orphaned_threats = threat_vip_ids - vip_ids
        
        integrity_success = len(orphaned_threats) == 0
        return self.log_test(
            "Data Integrity", 
            integrity_success,
            f"VIPs: {len(vip_ids)}, Threats: {len(threat_vip_ids)}, Orphaned: {len(orphaned_threats)}"
        )

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        cleanup_success = True
        
        # Delete test VIP (this should also handle related threats)
        if self.test_vip_id:
            success, response = self.make_request('DELETE', f'/api/vips/{self.test_vip_id}')
            cleanup_success &= self.log_test("Cleanup Test VIP", success, f"Deleted VIP: {self.test_vip_id}")
        
        return cleanup_success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Protego Backend API Tests")
        print("=" * 50)
        
        # Basic connectivity tests
        print("\n📡 Testing Basic Connectivity...")
        self.test_health_endpoint()
        self.test_stats_endpoint()
        
        # CRUD operations
        print("\n👥 Testing VIP Management...")
        self.test_vip_crud_operations()
        
        print("\n🚨 Testing Threat Operations...")
        self.test_threat_operations()
        
        # Analytics
        print("\n📊 Testing Analytics...")
        self.test_analytics_endpoints()
        
        # Monitoring features
        print("\n🔍 Testing Monitoring Features...")
        self.test_monitoring_endpoints()
        
        # Data integrity
        print("\n🔒 Testing Data Integrity...")
        self.test_data_integrity()
        
        # Cleanup
        print("\n🧹 Cleaning Up Test Data...")
        self.cleanup_test_data()
        
        # Final results
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Please check the issues above.")
            return 1

def main():
    """Main test execution"""
    tester = ProtegoAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
API Examples for QEMU SQLite Simulation System

This script demonstrates various ways to interact with the simulation system
using Python requests library.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class SimulationClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def submit_request(self, vm_name: str, commands: str, timeout: int = 300) -> Dict[str, Any]:
        """Submit a new simulation request"""
        payload = {
            "vm_name": vm_name,
            "commands": commands,
            "timeout": timeout
        }
        
        response = self.session.post(f"{self.base_url}/requests", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_request(self, request_uuid: str) -> Dict[str, Any]:
        """Get details of a specific request"""
        response = self.session.get(f"{self.base_url}/requests/{request_uuid}")
        response.raise_for_status()
        return response.json()
    
    def get_all_requests(self, status: Optional[str] = None) -> list:
        """Get all requests, optionally filtered by status"""
        url = f"{self.base_url}/requests"
        params = {"status": status} if status else {}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_logs(self, request_uuid: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get work logs for a request"""
        params = {"limit": limit, "offset": offset}
        response = self.session.get(f"{self.base_url}/requests/{request_uuid}/logs", params=params)
        response.raise_for_status()
        return response.json()
    
    def cancel_request(self, request_uuid: str) -> Dict[str, Any]:
        """Cancel a request"""
        response = self.session.delete(f"{self.base_url}/requests/{request_uuid}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, request_uuid: str, poll_interval: int = 5, max_wait: int = 600) -> str:
        """Wait for a request to complete and return final status"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            request_data = self.get_request(request_uuid)
            status = request_data["status"]
            
            if status in ["done", "cancelled"]:
                return status
            
            print(f"Request {request_uuid[:8]}... status: {status}")
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Request did not complete within {max_wait} seconds")

def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    client = SimulationClient()
    
    # Submit a simple request
    print("Submitting request...")
    result = client.submit_request(
        vm_name="ubuntu-server",
        commands="echo 'Hello from VM' && uname -a && date",
        timeout=300
    )
    
    request_uuid = result["uuid"]
    print(f"Request submitted: {request_uuid}")
    
    # Wait for completion
    print("Waiting for completion...")
    final_status = client.wait_for_completion(request_uuid)
    print(f"Final status: {final_status}")
    
    # Get logs
    print("Retrieving logs...")
    logs = client.get_logs(request_uuid)
    print(f"Retrieved {len(logs['logs'])} log entries")
    
    for log in logs["logs"][-5:]:  # Show last 5 entries
        print(f"[{log['timestamp']}] {log['log_type']}: {log['output']}")

def example_batch_processing():
    """Example of processing multiple VMs"""
    print("\n=== Batch Processing Example ===")
    
    client = SimulationClient()
    
    # Define multiple test scenarios
    test_scenarios = [
        {
            "name": "System Info Test",
            "vm": "ubuntu-server",
            "commands": "hostname && whoami && df -h && free -m",
            "timeout": 180
        },
        {
            "name": "Package Test",
            "vm": "ubuntu-server", 
            "commands": "apt list --installed | head -10",
            "timeout": 120
        },
        {
            "name": "Network Test",
            "vm": "ubuntu-server",
            "commands": "ip addr show && ping -c 3 8.8.8.8",
            "timeout": 300
        }
    ]
    
    # Submit all requests
    submitted_requests = []
    for scenario in test_scenarios:
        print(f"Submitting: {scenario['name']}")
        result = client.submit_request(
            vm_name=scenario["vm"],
            commands=scenario["commands"],
            timeout=scenario["timeout"]
        )
        submitted_requests.append({
            "uuid": result["uuid"],
            "name": scenario["name"]
        })
    
    # Monitor all requests
    print(f"\nMonitoring {len(submitted_requests)} requests...")
    completed = {}
    
    while len(completed) < len(submitted_requests):
        for req in submitted_requests:
            if req["uuid"] not in completed:
                request_data = client.get_request(req["uuid"])
                status = request_data["status"]
                
                if status in ["done", "cancelled"]:
                    completed[req["uuid"]] = status
                    print(f"✅ {req['name']}: {status}")
        
        if len(completed) < len(submitted_requests):
            time.sleep(5)
    
    print("All requests completed!")

def example_error_handling():
    """Example with error handling"""
    print("\n=== Error Handling Example ===")
    
    client = SimulationClient()
    
    try:
        # Submit request with non-existent VM
        print("Testing with invalid VM name...")
        result = client.submit_request(
            vm_name="nonexistent-vm",
            commands="echo 'This will fail'",
            timeout=60
        )
        
        request_uuid = result["uuid"]
        final_status = client.wait_for_completion(request_uuid, max_wait=120)
        
        if final_status == "cancelled":
            print("Request failed as expected")
            
            # Get error logs
            logs = client.get_logs(request_uuid)
            error_logs = [log for log in logs["logs"] if log["log_type"] == "stderr"]
            
            if error_logs:
                print("Error details:")
                for log in error_logs[-3:]:
                    print(f"  {log['output']}")
    
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def example_monitoring_dashboard():
    """Example of building a simple monitoring dashboard"""
    print("\n=== Monitoring Dashboard Example ===")
    
    client = SimulationClient()
    
    # Get system overview
    all_requests = client.get_all_requests()
    
    # Analyze status distribution
    status_counts = {}
    for request in all_requests:
        status = request["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("System Status Overview:")
    print(f"Total Requests: {len(all_requests)}")
    for status, count in status_counts.items():
        print(f"  {status.capitalize()}: {count}")
    
    # Show recent activity
    print("\nRecent Requests:")
    for request in all_requests[:5]:
        print(f"  {request['uuid'][:8]}... | {request['vm_name']} | {request['status']} | {request['created_at']}")
    
    # Show running requests
    running_requests = client.get_all_requests(status="running")
    if running_requests:
        print(f"\nCurrently Running ({len(running_requests)}):")
        for request in running_requests:
            print(f"  {request['uuid'][:8]}... | {request['vm_name']} | Started: {request['created_at']}")

def example_advanced_vm_testing():
    """Advanced example testing different VM configurations"""
    print("\n=== Advanced VM Testing Example ===")
    
    client = SimulationClient()
    
    # Test different VM configurations
    vm_tests = [
        {
            "vm": "ubuntu-server",
            "name": "Ubuntu Server Test",
            "commands": "lsb_release -a && docker --version || echo 'Docker not installed'",
            "timeout": 240
        },
        {
            "vm": "alpine-docker",
            "name": "Alpine Docker Test", 
            "commands": "cat /etc/alpine-release && apk info docker",
            "timeout": 180
        },
        {
            "vm": "centos-minimal",
            "name": "CentOS Minimal Test",
            "commands": "cat /etc/centos-release && rpm -qa | wc -l",
            "timeout": 200
        }
    ]
    
    results = {}
    
    for test in vm_tests:
        try:
            print(f"Starting {test['name']}...")
            result = client.submit_request(
                vm_name=test["vm"],
                commands=test["commands"],
                timeout=test["timeout"]
            )
            
            request_uuid = result["uuid"]
            final_status = client.wait_for_completion(request_uuid, max_wait=test["timeout"] + 60)
            
            # Get output
            logs = client.get_logs(request_uuid)
            stdout_logs = [log["output"] for log in logs["logs"] if log["log_type"] == "stdout"]
            
            results[test["name"]] = {
                "status": final_status,
                "output": stdout_logs[-5:] if stdout_logs else []
            }
            
        except Exception as e:
            results[test["name"]] = {
                "status": "error",
                "error": str(e)
            }
    
    # Print results summary
    print("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status = result["status"]
        print(f"\n{test_name}: {status.upper()}")
        
        if status == "done" and result.get("output"):
            print("  Output preview:")
            for line in result["output"]:
                print(f"    {line}")
        elif status == "error":
            print(f"  Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    print("QEMU SQLite Simulation System - API Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_basic_usage()
        example_batch_processing()
        example_error_handling()
        example_monitoring_dashboard()
        example_advanced_vm_testing()
        
        print("\n🎉 All examples completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to simulation system.")
        print("Please ensure the API server is running:")
        print("  python main.py api")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
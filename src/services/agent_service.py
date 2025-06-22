import asyncio
import sqlite3
import threading
import time
from datetime import datetime
from typing import List

from ..database.connection import DatabaseConnection
from ..database.models import Request, RequestStatus
from ..qemu.vm_manager import QEMUVMManager

class AgentService:
    def __init__(self, poll_interval: int = 5):
        self.db = DatabaseConnection()
        self.vm_manager = QEMUVMManager()
        self.poll_interval = poll_interval
        self.running = False
        self.agent_thread = None
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.agent_thread = threading.Thread(target=self._run_agent_loop)
        self.agent_thread.daemon = True
        self.agent_thread.start()
        print(f"Agent service started with {self.poll_interval}s poll interval")
    
    def stop(self):
        self.running = False
        if self.agent_thread:
            self.agent_thread.join(timeout=10)
        print("Agent service stopped")
    
    def _run_agent_loop(self):
        while self.running:
            try:
                self._process_pending_requests()
                self._monitor_running_requests()
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"Error in agent loop: {e}")
                time.sleep(self.poll_interval)
    
    def _process_pending_requests(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT uuid, vm_name, commands, timeout 
                    FROM requests 
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                """)
                
                pending_requests = cursor.fetchall()
                
                for row in pending_requests:
                    request_uuid = row['uuid']
                    vm_name = row['vm_name']
                    commands = row['commands']
                    timeout = row['timeout']
                    
                    try:
                        cursor.execute("""
                            UPDATE requests 
                            SET status = 'acknowledged', updated_at = CURRENT_TIMESTAMP
                            WHERE uuid = ?
                        """, (request_uuid,))
                        conn.commit()
                        
                        print(f"Processing request {request_uuid}: VM={vm_name}")
                        
                        self.vm_manager.start_vm(request_uuid, vm_name, commands, timeout)
                        
                        cursor.execute("""
                            UPDATE requests 
                            SET status = 'running', updated_at = CURRENT_TIMESTAMP
                            WHERE uuid = ?
                        """, (request_uuid,))
                        conn.commit()
                        
                        print(f"Started VM for request {request_uuid}")
                        
                    except Exception as e:
                        print(f"Failed to start VM for request {request_uuid}: {e}")
                        cursor.execute("""
                            UPDATE requests 
                            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                            WHERE uuid = ?
                        """, (request_uuid,))
                        conn.commit()
        
        except sqlite3.Error as e:
            print(f"Database error while processing pending requests: {e}")
    
    def _monitor_running_requests(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT uuid FROM requests WHERE status = 'running'
                """)
                
                running_requests = [row['uuid'] for row in cursor.fetchall()]
                
                for request_uuid in running_requests:
                    if not self.vm_manager.is_running(request_uuid):
                        cursor.execute("""
                            UPDATE requests 
                            SET status = 'done', updated_at = CURRENT_TIMESTAMP
                            WHERE uuid = ?
                        """, (request_uuid,))
                        conn.commit()
                        print(f"Request {request_uuid} completed")
        
        except sqlite3.Error as e:
            print(f"Database error while monitoring running requests: {e}")
    
    def cancel_request(self, request_uuid: str) -> bool:
        try:
            stopped = self.vm_manager.stop_vm(request_uuid)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE requests 
                    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE uuid = ?
                """, (request_uuid,))
                conn.commit()
            
            print(f"Request {request_uuid} cancelled")
            return True
        
        except Exception as e:
            print(f"Error cancelling request {request_uuid}: {e}")
            return False
    
    def get_status(self) -> dict:
        running_vms = self.vm_manager.get_running_vms()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT status, COUNT(*) as count FROM requests GROUP BY status")
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                
                cursor.execute("""
                    SELECT COUNT(*) as total FROM requests 
                    WHERE DATE(created_at) = DATE('now')
                """)
                today_requests = cursor.fetchone()['total']
        
        except sqlite3.Error as e:
            print(f"Database error getting status: {e}")
            status_counts = {}
            today_requests = 0
        
        return {
            'agent_running': self.running,
            'poll_interval': self.poll_interval,
            'running_vms': len(running_vms),
            'vm_details': running_vms,
            'request_counts': status_counts,
            'today_requests': today_requests,
            'uptime': time.time() if self.running else 0
        }

class MultiAgentManager:
    def __init__(self, num_agents: int = 1, poll_interval: int = 5):
        self.num_agents = num_agents
        self.poll_interval = poll_interval
        self.agents = []
    
    def start_all(self):
        for i in range(self.num_agents):
            agent = AgentService(poll_interval=self.poll_interval)
            agent.start()
            self.agents.append(agent)
            print(f"Started agent {i+1}/{self.num_agents}")
    
    def stop_all(self):
        for i, agent in enumerate(self.agents):
            agent.stop()
            print(f"Stopped agent {i+1}/{len(self.agents)}")
        self.agents.clear()
    
    def get_combined_status(self) -> dict:
        if not self.agents:
            return {'error': 'No agents running'}
        
        combined_status = self.agents[0].get_status()
        
        for i, agent in enumerate(self.agents[1:], 1):
            agent_status = agent.get_status()
            combined_status['running_vms'] += agent_status['running_vms']
            combined_status['vm_details'].update(agent_status['vm_details'])
        
        combined_status['active_agents'] = len([a for a in self.agents if a.running])
        combined_status['total_agents'] = len(self.agents)
        
        return combined_status
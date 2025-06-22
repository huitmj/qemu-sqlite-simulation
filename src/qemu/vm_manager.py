import subprocess
import threading
import time
import os
from datetime import datetime
from typing import Optional, Callable
from ..database.connection import DatabaseConnection
from ..database.models import LogType

class QEMUVMManager:
    def __init__(self):
        self.db = DatabaseConnection()
        self.running_processes = {}
        self.script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'qemu_runner.sh')
    
    def start_vm(self, request_uuid: str, vm_name: str, commands: str, timeout: int = 5):
        if request_uuid in self.running_processes:
            raise RuntimeError(f"VM for request {request_uuid} is already running")
        
        work_log_table = self.db.get_work_log_table_name(request_uuid)
        
        def log_output(output: str, log_type: LogType):
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO {work_log_table} (timestamp, output, log_type)
                    VALUES (CURRENT_TIMESTAMP, ?, ?)
                """, (output, log_type.value))
                conn.commit()
        
        thread = threading.Thread(
            target=self._run_vm_process,
            args=(request_uuid, vm_name, commands, timeout, log_output)
        )
        thread.daemon = True
        thread.start()
        
        self.running_processes[request_uuid] = {
            'thread': thread,
            'start_time': datetime.now(),
            'vm_name': vm_name
        }
    
    def _run_vm_process(self, request_uuid: str, vm_name: str, commands: str, timeout: int, log_callback: Callable):
        try:
            log_callback(f"Starting VM: {vm_name}", LogType.BOOT)
            
            process = subprocess.Popen(
                [self.script_path, vm_name, str(timeout)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.running_processes[request_uuid]['process'] = process
            
            boot_detected = False
            last_output_time = time.time()
            
            def read_output(stream, log_type):
                nonlocal last_output_time, boot_detected
                
                while True:
                    line = stream.readline()
                    if not line:
                        break
                    
                    line = line.strip()
                    if line:
                        current_time = time.time()
                        last_output_time = current_time
                        
                        log_callback(line, log_type)
                        
                        if not boot_detected and self._is_boot_complete(line):
                            boot_detected = True
                            log_callback("Boot process completed", LogType.BOOT)
                            
                            time.sleep(1)
                            self._send_commands(process, commands, log_callback)
            
            stdout_thread = threading.Thread(target=read_output, args=(process.stdout, LogType.STDOUT))
            stderr_thread = threading.Thread(target=read_output, args=(process.stderr, LogType.STDERR))
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            
            stdout_thread.start()
            stderr_thread.start()
            
            timeout_monitor = threading.Thread(
                target=self._monitor_timeout,
                args=(process, timeout, last_output_time, log_callback)
            )
            timeout_monitor.daemon = True
            timeout_monitor.start()
            
            process.wait()
            
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            
            if process.returncode == 0:
                log_callback("VM execution completed successfully", LogType.STDOUT)
            elif process.returncode == 124:
                log_callback(f"VM execution timed out after {timeout} seconds", LogType.STDERR)
            else:
                log_callback(f"VM execution failed with exit code: {process.returncode}", LogType.STDERR)
        
        except Exception as e:
            log_callback(f"Error running VM: {str(e)}", LogType.STDERR)
        
        finally:
            if request_uuid in self.running_processes:
                del self.running_processes[request_uuid]
    
    def _is_boot_complete(self, line: str) -> bool:
        boot_indicators = [
            "login:",
            "Welcome to",
            "$ ",
            "# ",
            "root@",
            "user@",
            "Ubuntu",
            "Debian",
            "CentOS",
            "Started"
        ]
        
        line_lower = line.lower()
        return any(indicator.lower() in line_lower for indicator in boot_indicators)
    
    def _send_commands(self, process: subprocess.Popen, commands: str, log_callback: Callable):
        try:
            log_callback(f"Sending commands: {commands}", LogType.COMMAND)
            
            if process.stdin:
                process.stdin.write(commands + '\n')
                process.stdin.flush()
                
                time.sleep(0.5)
                
                process.stdin.write('exit\n')
                process.stdin.flush()
                process.stdin.close()
        
        except Exception as e:
            log_callback(f"Error sending commands: {str(e)}", LogType.STDERR)
    
    def _monitor_timeout(self, process: subprocess.Popen, timeout: int, last_output_time: float, log_callback: Callable):
        while process.poll() is None:
            current_time = time.time()
            
            if current_time - last_output_time > timeout:
                log_callback(f"No output detected for {timeout} seconds, terminating VM", LogType.STDERR)
                process.terminate()
                
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                break
            
            time.sleep(1)
    
    def stop_vm(self, request_uuid: str) -> bool:
        if request_uuid not in self.running_processes:
            return False
        
        process_info = self.running_processes[request_uuid]
        
        if 'process' in process_info:
            process = process_info['process']
            if process.poll() is None:
                process.terminate()
                
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
        
        if request_uuid in self.running_processes:
            del self.running_processes[request_uuid]
        
        return True
    
    def is_running(self, request_uuid: str) -> bool:
        return request_uuid in self.running_processes
    
    def get_running_vms(self) -> dict:
        return {
            req_id: {
                'vm_name': info['vm_name'],
                'start_time': info['start_time'],
                'running_time': (datetime.now() - info['start_time']).total_seconds()
            }
            for req_id, info in self.running_processes.items()
        }
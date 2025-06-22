import os
from typing import Optional

class Config:
    # Database configuration
    DATABASE_PATH: str = os.getenv('SQLITE_SIM_DB_PATH', 'simulation.db')
    
    # FastAPI configuration
    API_HOST: str = os.getenv('SQLITE_SIM_API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('SQLITE_SIM_API_PORT', '8000'))
    API_WORKERS: int = int(os.getenv('SQLITE_SIM_API_WORKERS', '1'))
    
    # Agent configuration
    AGENT_POLL_INTERVAL: int = int(os.getenv('SQLITE_SIM_AGENT_POLL_INTERVAL', '5'))
    AGENT_COUNT: int = int(os.getenv('SQLITE_SIM_AGENT_COUNT', '1'))
    
    # QEMU configuration
    QEMU_SCRIPT_PATH: str = os.getenv('SQLITE_SIM_QEMU_SCRIPT', './scripts/qemu_runner.sh')
    VM_IMAGES_DIR: str = os.getenv('SQLITE_SIM_VM_IMAGES_DIR', './vm_images')
    VM_CONFIG_DIR: str = os.getenv('SQLITE_SIM_VM_CONFIG_DIR', './vm_configs')
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv('SQLITE_SIM_LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('SQLITE_SIM_LOG_FILE', None)
    
    # System limits
    MAX_CONCURRENT_VMS: int = int(os.getenv('SQLITE_SIM_MAX_CONCURRENT_VMS', '10'))
    DEFAULT_TIMEOUT: int = int(os.getenv('SQLITE_SIM_DEFAULT_TIMEOUT', '300'))
    MAX_TIMEOUT: int = int(os.getenv('SQLITE_SIM_MAX_TIMEOUT', '3600'))
    
    # Security
    ENABLE_CORS: bool = os.getenv('SQLITE_SIM_ENABLE_CORS', 'false').lower() == 'true'
    ALLOWED_ORIGINS: list = os.getenv('SQLITE_SIM_ALLOWED_ORIGINS', '').split(',') if os.getenv('SQLITE_SIM_ALLOWED_ORIGINS') else ['*']
    
    @classmethod
    def validate(cls):
        """Validate configuration values"""
        errors = []
        
        # Check required directories exist or can be created
        dirs_to_check = [cls.VM_IMAGES_DIR, cls.VM_CONFIG_DIR]
        for directory in dirs_to_check:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {directory}: {e}")
        
        # Validate QEMU script exists
        if not os.path.exists(cls.QEMU_SCRIPT_PATH):
            errors.append(f"QEMU script not found: {cls.QEMU_SCRIPT_PATH}")
        
        # Validate numeric ranges
        if cls.AGENT_POLL_INTERVAL < 1:
            errors.append("AGENT_POLL_INTERVAL must be at least 1 second")
        
        if cls.AGENT_COUNT < 1:
            errors.append("AGENT_COUNT must be at least 1")
        
        if cls.MAX_CONCURRENT_VMS < 1:
            errors.append("MAX_CONCURRENT_VMS must be at least 1")
        
        if cls.DEFAULT_TIMEOUT < 1:
            errors.append("DEFAULT_TIMEOUT must be at least 1 second")
        
        if cls.MAX_TIMEOUT < cls.DEFAULT_TIMEOUT:
            errors.append("MAX_TIMEOUT must be greater than or equal to DEFAULT_TIMEOUT")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("=== SQLite Simulation Configuration ===")
        print(f"Database Path: {cls.DATABASE_PATH}")
        print(f"API Host: {cls.API_HOST}")
        print(f"API Port: {cls.API_PORT}")
        print(f"API Workers: {cls.API_WORKERS}")
        print(f"Agent Poll Interval: {cls.AGENT_POLL_INTERVAL}s")
        print(f"Agent Count: {cls.AGENT_COUNT}")
        print(f"QEMU Script: {cls.QEMU_SCRIPT_PATH}")
        print(f"VM Images Directory: {cls.VM_IMAGES_DIR}")
        print(f"VM Config Directory: {cls.VM_CONFIG_DIR}")
        print(f"Max Concurrent VMs: {cls.MAX_CONCURRENT_VMS}")
        print(f"Default Timeout: {cls.DEFAULT_TIMEOUT}s")
        print(f"Max Timeout: {cls.MAX_TIMEOUT}s")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"Log File: {cls.LOG_FILE or 'Console only'}")
        print(f"CORS Enabled: {cls.ENABLE_CORS}")
        print(f"Allowed Origins: {cls.ALLOWED_ORIGINS}")
        print("========================================")

# Global config instance
config = Config()
#!/usr/bin/env python3

import sys
import signal
import argparse
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from config import config
from src.services.agent_service import MultiAgentManager
from src.services.request_service import app

def setup_signal_handlers(agent_manager):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        agent_manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def start_api_server():
    """Start the FastAPI server"""
    print(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    
    if config.ENABLE_CORS:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        workers=config.API_WORKERS,
        log_level=config.LOG_LEVEL.lower()
    )

def start_agents():
    """Start the agent services"""
    print(f"Starting {config.AGENT_COUNT} agent(s) with {config.AGENT_POLL_INTERVAL}s poll interval")
    
    agent_manager = MultiAgentManager(
        num_agents=config.AGENT_COUNT,
        poll_interval=config.AGENT_POLL_INTERVAL
    )
    
    setup_signal_handlers(agent_manager)
    
    try:
        agent_manager.start_all()
        
        # Keep the main thread alive
        import time
        while True:
            status = agent_manager.get_combined_status()
            print(f"Agents running: {status['active_agents']}/{status['total_agents']}, "
                  f"VMs: {status['running_vms']}, "
                  f"Requests today: {status.get('today_requests', 0)}")
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\nShutting down agents...")
        agent_manager.stop_all()

def start_all():
    """Start both API server and agents (not recommended for production)"""
    import threading
    
    print("Starting all services (API + Agents)")
    print("WARNING: This mode is not recommended for production use")
    print("Consider running API and agents separately")
    
    agent_manager = MultiAgentManager(
        num_agents=config.AGENT_COUNT,
        poll_interval=config.AGENT_POLL_INTERVAL
    )
    
    setup_signal_handlers(agent_manager)
    
    # Start agents in background thread
    agent_thread = threading.Thread(target=agent_manager.start_all)
    agent_thread.daemon = True
    agent_thread.start()
    
    # Start API server in main thread
    start_api_server()

def show_config():
    """Show current configuration"""
    config.print_config()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\nConfiguration is valid!")

def show_status():
    """Show system status"""
    from src.database.connection import DatabaseConnection
    import sqlite3
    
    try:
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT status, COUNT(*) as count FROM requests GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) as total FROM requests")
            total_requests = cursor.fetchone()['total']
            
            print("=== System Status ===")
            print(f"Database: {config.DATABASE_PATH}")
            print(f"Total Requests: {total_requests}")
            print("\nRequest Status Distribution:")
            for status in ['pending', 'acknowledged', 'running', 'cancelled', 'hold', 'done']:
                count = status_counts.get(status, 0)
                print(f"  {status.capitalize()}: {count}")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='QEMU SQLite Simulation System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # API server command
    api_parser = subparsers.add_parser('api', help='Start API server')
    
    # Agent command
    agent_parser = subparsers.add_parser('agents', help='Start agent services')
    
    # All services command
    all_parser = subparsers.add_parser('all', help='Start all services (API + Agents)')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # CLI tools command
    cli_parser = subparsers.add_parser('cli', help='Run CLI query tools')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'api':
        start_api_server()
    elif args.command == 'agents':
        start_agents()
    elif args.command == 'all':
        start_all()
    elif args.command == 'config':
        show_config()
    elif args.command == 'status':
        show_status()
    elif args.command == 'cli':
        from src.cli.query_tools import cli
        sys.argv = ['query_tools'] + sys.argv[2:]  # Pass remaining args to CLI
        cli()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
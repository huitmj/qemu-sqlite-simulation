# QEMU SQLite Simulation System

> **A cloud-native database-driven simulation tool using QEMU and SQLite for automated virtual machine execution and monitoring.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![QEMU Compatible](https://img.shields.io/badge/QEMU-4.0+-green.svg)](https://www.qemu.org/)

## 🚀 Features

- **🔄 REST API** - Submit and monitor simulation requests programmatically
- **🤖 Background Agents** - Automated VM execution with multi-agent support
- **📊 Real-time Logging** - 1-second granularity output capture and storage
- **⚡ CLI Tools** - Comprehensive command-line interface for management
- **⚙️ Configurable** - Flexible VM parameters and system settings
- **📈 Status Tracking** - Complete request lifecycle visibility
- **🔧 Scalable** - Horizontal scaling with multiple agent instances

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [API Reference](#-api-reference)
- [CLI Commands](#-cli-commands)
- [VM Setup Guide](#-vm-setup-guide)
- [System Architecture](#-system-architecture)
- [Production Deployment](#-production-deployment)
- [Troubleshooting](#-troubleshooting)

## 🏁 Quick Start

### Prerequisites
- Python 3.8 or higher
- QEMU installed and accessible in PATH
- VM images in qcow2 format

### 1-Minute Setup

```bash
# Clone and setup
git clone <repository-url>
cd sqlite_sim

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p vm_images vm_configs

# Add your VM image (example)
# cp /path/to/your/vm.qcow2 vm_images/ubuntu-server.qcow2

# Start the system
python main.py all
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📦 Installation

### Development Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py config
```

### Production Installation

```bash
# Install system-wide
pip install -r requirements.txt

# Create service user
sudo useradd -r -s /bin/false qemu-sim

# Setup directories
sudo mkdir -p /opt/qemu-sim/{vm_images,vm_configs,logs}
sudo chown -R qemu-sim:qemu-sim /opt/qemu-sim
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Database Configuration
SQLITE_SIM_DB_PATH="./simulation.db"

# API Server Settings
SQLITE_SIM_API_HOST="0.0.0.0"
SQLITE_SIM_API_PORT="8000"
SQLITE_SIM_API_WORKERS="1"

# Agent Configuration
SQLITE_SIM_AGENT_COUNT="2"
SQLITE_SIM_AGENT_POLL_INTERVAL="5"

# QEMU Settings
SQLITE_SIM_VM_IMAGES_DIR="./vm_images"
SQLITE_SIM_VM_CONFIG_DIR="./vm_configs"
SQLITE_SIM_MAX_CONCURRENT_VMS="10"
SQLITE_SIM_DEFAULT_TIMEOUT="300"
SQLITE_SIM_MAX_TIMEOUT="3600"

# Security & CORS
SQLITE_SIM_ENABLE_CORS="false"
SQLITE_SIM_ALLOWED_ORIGINS="*"

# Logging
SQLITE_SIM_LOG_LEVEL="INFO"
SQLITE_SIM_LOG_FILE="./logs/qemu-sim.log"
```

### View Current Configuration

```bash
python main.py config
```

## 📚 Usage Examples

### Starting the System

```bash
# Development: Start all services
python main.py all

# Production: Start services separately
# Terminal 1: API Server
python main.py api

# Terminal 2: Agent Services
python main.py agents
```

### Basic API Usage

```bash
# Submit a simulation request
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "ubuntu-server",
    "commands": "echo Hello World && uname -a",
    "timeout": 300
  }'

# Response:
# {
#   "uuid": "123e4567-e89b-12d3-a456-426614174000",
#   "status": "pending",
#   "message": "Request created successfully"
# }
```

### Monitor Request Progress

```bash
# Check specific request
REQUEST_ID="123e4567-e89b-12d3-a456-426614174000"
curl "http://localhost:8000/requests/$REQUEST_ID"

# View logs
curl "http://localhost:8000/requests/$REQUEST_ID/logs"

# Cancel request
curl -X DELETE "http://localhost:8000/requests/$REQUEST_ID"
```

### CLI Management

```bash
# List all requests
python main.py cli list-requests

# Filter by status
python main.py cli list-requests --status running

# Show request details
python main.py cli show-request 123e4567

# Follow logs in real-time
python main.py cli show-logs 123e4567 --follow

# System statistics
python main.py cli stats
```

## 🔌 API Reference

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/requests` | Submit new simulation request |
| `GET` | `/requests` | List all requests (with filtering) |
| `GET` | `/requests/{uuid}` | Get specific request details |
| `GET` | `/requests/{uuid}/logs` | Retrieve work logs |
| `PUT` | `/requests/{uuid}/status` | Update request status |
| `DELETE` | `/requests/{uuid}` | Cancel/delete request |

### Request Schema

```json
{
  "vm_name": "ubuntu-server",
  "commands": "echo 'Hello World'",
  "timeout": 300
}
```

### Response Schema

```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "vm_name": "ubuntu-server",
  "commands": "echo 'Hello World'",
  "timeout": 300,
  "status": "pending",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Status Values

- `pending` - Request submitted, waiting for agent
- `acknowledged` - Agent picked up the request
- `running` - QEMU VM is executing
- `done` - Execution completed successfully
- `cancelled` - Request was cancelled or failed
- `hold` - Request paused (manual intervention required)

## 🖥️ CLI Commands

### Request Management

```bash
# List requests with various filters
python main.py cli list-requests
python main.py cli list-requests --status running --limit 50

# Show detailed request information
python main.py cli show-request <uuid>
python main.py cli show-request 123e4567  # Partial UUID works

# Delete request and logs
python main.py cli delete-request <uuid>
```

### Log Viewing

```bash
# View recent logs
python main.py cli show-logs <uuid>
python main.py cli show-logs <uuid> --limit 100

# Filter by log type
python main.py cli show-logs <uuid> --log-type stdout
python main.py cli show-logs <uuid> --log-type stderr

# Follow logs in real-time (like tail -f)
python main.py cli show-logs <uuid> --follow
```

### System Information

```bash
# System statistics
python main.py cli stats

# System status
python main.py status

# Configuration details
python main.py config
```

## 🖼️ VM Setup Guide

### Creating VM Images

```bash
# Create Ubuntu VM image
qemu-img create -f qcow2 vm_images/ubuntu-server.qcow2 10G

# Install from ISO (example)
qemu-system-x86_64 \
  -m 2G \
  -cdrom ubuntu-20.04-server.iso \
  -drive format=qcow2,file=vm_images/ubuntu-server.qcow2 \
  -boot d \
  -netdev user,id=net0 \
  -device e1000,netdev=net0
```

### VM Configuration Files

Create VM-specific configs in `vm_configs/`:

```bash
# vm_configs/ubuntu-server.conf
MEMORY="2G"
CPU="2"
ADDITIONAL_ARGS="-netdev user,id=net0 -device e1000,netdev=net0"
```

```bash
# vm_configs/test-vm.conf
MEMORY="512M"
CPU="1"
ADDITIONAL_ARGS="-nographic"
```

### VM Image Requirements

- **Format**: qcow2 (recommended) or raw
- **Size**: Minimum 1GB, recommended 5GB+
- **OS**: Any Linux distribution with SSH/console access
- **Network**: Configure for console or SSH access
- **Auto-login**: Optional but recommended for automation

### Example VM Setup (Ubuntu)

```bash
# Inside VM during setup:
# 1. Enable auto-login (optional)
sudo systemctl edit getty@tty1
# Add:
# [Service]
# ExecStart=
# ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM

# 2. Disable password for sudo (optional)
echo "root ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 3. Install required packages
apt-get update
apt-get install -y curl wget git python3

# 4. Shutdown cleanly
shutdown -h now
```

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   CLI Client    │    │  External API   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │        FastAPI Server      │
                    │      (Request Service)     │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │       SQLite Database      │
                    │    (Requests + Work Logs)  │
                    └─────────────┬──────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
        ┌────────▼──────┐ ┌──────▼────┐ ┌──────▼────┐
        │   Agent 1     │ │  Agent 2  │ │  Agent N  │
        │   Service     │ │  Service  │ │  Service  │
        └────────┬──────┘ └──────┬────┘ └──────┬────┘
                 │               │             │
        ┌────────▼──────┐ ┌──────▼────┐ ┌──────▼────┐
        │   QEMU VM     │ │  QEMU VM  │ │  QEMU VM  │
        │   Instance    │ │  Instance │ │  Instance │
        └───────────────┘ └───────────┘ └───────────┘
```

### Data Flow

1. **Request Submission**: Client submits VM execution request via API
2. **Database Storage**: Request stored with unique UUID and 'pending' status
3. **Agent Processing**: Background agents poll for pending requests
4. **VM Execution**: Agent launches QEMU VM with specified parameters
5. **Output Logging**: VM output captured and stored in work log tables
6. **Status Updates**: Request status updated throughout execution
7. **Completion**: Final status and logs available via API/CLI

### Database Schema

```sql
-- Requests table
CREATE TABLE requests (
    uuid TEXT PRIMARY KEY,
    vm_name TEXT NOT NULL,
    commands TEXT NOT NULL,
    timeout INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- Work log tables (one per request)
CREATE TABLE work_log_<uuid> (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    output TEXT,
    log_type TEXT -- 'boot', 'command', 'stdout', 'stderr'
);
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

RUN apt-get update && apt-get install -y qemu-system-x86_64
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py", "api"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./vm_images:/app/vm_images
      - ./data:/app/data
    environment:
      - SQLITE_SIM_DB_PATH=/app/data/simulation.db
  
  agents:
    build: .
    command: python main.py agents
    volumes:
      - ./vm_images:/app/vm_images
      - ./data:/app/data
    environment:
      - SQLITE_SIM_DB_PATH=/app/data/simulation.db
      - SQLITE_SIM_AGENT_COUNT=3
```

### Systemd Service

```ini
# /etc/systemd/system/qemu-sim-api.service
[Unit]
Description=QEMU Simulation API Server
After=network.target

[Service]
Type=simple
User=qemu-sim
WorkingDirectory=/opt/qemu-sim
ExecStart=/usr/bin/python3 main.py api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/qemu-sim-agents.service
[Unit]
Description=QEMU Simulation Agents
After=network.target

[Service]
Type=simple
User=qemu-sim
WorkingDirectory=/opt/qemu-sim
ExecStart=/usr/bin/python3 main.py agents
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/qemu-sim
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring & Logging

```bash
# Log rotation configuration
# /etc/logrotate.d/qemu-sim
/opt/qemu-sim/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 qemu-sim qemu-sim
}
```

## 🔍 Troubleshooting

### Common Issues

#### QEMU Not Found
```bash
# Error: QEMU not accessible
# Solution: Install QEMU
sudo apt-get install qemu-system-x86_64  # Ubuntu/Debian
brew install qemu                        # macOS
```

#### VM Image Not Found
```bash
# Error: VM image not found
# Solution: Check image path and format
ls -la vm_images/
python main.py config  # Verify paths
```

#### Permission Denied
```bash
# Error: Permission denied accessing VM images
# Solution: Fix permissions
sudo chown -R $USER:$USER vm_images/
chmod 644 vm_images/*.qcow2
```

#### Port Already in Use
```bash
# Error: Port 8000 already in use
# Solution: Change port or kill process
export SQLITE_SIM_API_PORT="8080"
# or
lsof -ti:8000 | xargs kill -9
```

### Debugging Tips

```bash
# Enable debug logging
export SQLITE_SIM_LOG_LEVEL="DEBUG"

# Check system status
python main.py status

# Test VM manually
./scripts/qemu_runner.sh ubuntu-server 300

# Verify database
sqlite3 simulation.db ".tables"
sqlite3 simulation.db "SELECT * FROM requests LIMIT 5;"

# Check API health
curl http://localhost:8000/requests
```

### Performance Tuning

```bash
# Increase agent count for high load
export SQLITE_SIM_AGENT_COUNT="5"

# Reduce polling interval for faster response
export SQLITE_SIM_AGENT_POLL_INTERVAL="2"

# Limit concurrent VMs to prevent resource exhaustion
export SQLITE_SIM_MAX_CONCURRENT_VMS="20"

# Optimize VM memory allocation
# vm_configs/your-vm.conf
MEMORY="512M"  # Reduce for more concurrent VMs
```

### Log Analysis

```bash
# View recent errors
python main.py cli list-requests --status cancelled

# Analyze failed requests
python main.py cli show-logs <failed-uuid> --log-type stderr

# Monitor system performance
python main.py cli stats

# Database maintenance
sqlite3 simulation.db "VACUUM;"
sqlite3 simulation.db "ANALYZE;"
```

## 📝 Development

### Project Structure

```
sqlite_sim/
├── src/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # Database connection management
│   │   └── models.py          # Pydantic models and schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── request_service.py # FastAPI REST API endpoints
│   │   └── agent_service.py   # Background agent workers
│   ├── qemu/
│   │   ├── __init__.py
│   │   └── vm_manager.py      # QEMU VM execution management
│   └── cli/
│       ├── __init__.py
│       └── query_tools.py     # Command-line interface tools
├── scripts/
│   └── qemu_runner.sh         # QEMU execution script
├── vm_images/                 # VM disk images (qcow2 format)
├── vm_configs/                # VM-specific configuration files
├── main.py                    # Application entry point
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── PRD.md                     # Product Requirements Document
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Testing

```bash
# Run unit tests (when available)
python -m pytest tests/

# Manual testing
python main.py config        # Test configuration
python main.py status        # Test database connection
python main.py cli stats     # Test CLI tools
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: See [PRD.md](PRD.md) for detailed requirements
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

## 🚧 Roadmap

- [ ] Web dashboard for visual monitoring
- [ ] Authentication and authorization system
- [ ] PostgreSQL database support
- [ ] Kubernetes deployment manifests
- [ ] Prometheus metrics integration
- [ ] VM template management system

---

**Made with ❤️ for the automation community**
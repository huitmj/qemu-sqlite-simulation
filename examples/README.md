# Examples and Documentation

This directory contains examples, guides, and documentation to help you get started with the QEMU SQLite Simulation System.

## 📚 Contents

### 📖 Documentation
- **[VM_SETUP_GUIDE.md](VM_SETUP_GUIDE.md)** - Comprehensive guide for creating and configuring virtual machines
- **[README.md](../README.md)** - Main project documentation
- **[PRD.md](../PRD.md)** - Product Requirements Document

### ⚙️ VM Configurations  
Ready-to-use VM configuration files in `../vm_configs/`:

| Configuration | Use Case | Resources | Features |
|---------------|----------|-----------|----------|
| `ubuntu-server.conf` | General server workloads | 2GB RAM, 2 CPU | SSH access, console output |
| `ubuntu-desktop.conf` | GUI application testing | 4GB RAM, 4 CPU | VNC access, audio support |
| `centos-minimal.conf` | RHEL/CentOS testing | 1GB RAM, 1 CPU | Minimal resources, SSH |
| `debian-testing.conf` | Latest Debian packages | 1.5GB RAM, 2 CPU | Virtio drivers |
| `alpine-docker.conf` | Container/Docker testing | 512MB RAM, 1 CPU | Lightweight, fast boot |
| `windows-test.conf` | Windows testing | 4GB RAM, 2 CPU | VNC access, license required |
| `security-sandbox.conf` | Security research | 2GB RAM, 2 CPU | Network isolation, snapshot mode |
| `performance-test.conf` | Benchmarking | 8GB RAM, 8 CPU | Maximum performance, KVM |

### 🐍 Python Examples
- **[api_examples.py](api_examples.py)** - Complete Python API usage examples

## 🚀 Quick Start

### 1. Setup VM Images
```bash
# Create directories
mkdir -p vm_images vm_configs

# Download Ubuntu Server ISO
wget https://releases.ubuntu.com/20.04/ubuntu-20.04.6-live-server-amd64.iso

# Create VM image
qemu-img create -f qcow2 vm_images/ubuntu-server.qcow2 20G

# Install OS (interactive)
qemu-system-x86_64 \
  -m 2G \
  -cdrom ubuntu-20.04.6-live-server-amd64.iso \
  -drive format=qcow2,file=vm_images/ubuntu-server.qcow2 \
  -boot d \
  -netdev user,id=net0 \
  -device e1000,netdev=net0
```

### 2. Test VM Configuration
```bash
# Test VM boots correctly
./scripts/qemu_runner.sh ubuntu-server 120

# Test with the simulation system
python main.py all &
sleep 5

# Submit test request
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "ubuntu-server",
    "commands": "echo Hello World && uname -a",
    "timeout": 300
  }'
```

### 3. Run Python Examples
```bash
# Install requests library
pip install requests

# Start the simulation system
python main.py all &

# Run examples
python examples/api_examples.py
```

## 📋 Example Workflows

### Development Testing
```bash
# Test code in clean Ubuntu environment
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "ubuntu-server",
    "commands": "git clone https://github.com/user/repo && cd repo && python3 -m pytest",
    "timeout": 600
  }'
```

### Security Analysis
```bash
# Analyze suspicious file in isolated environment
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "security-sandbox",
    "commands": "wget -O /tmp/sample.bin https://example.com/file && file /tmp/sample.bin && strings /tmp/sample.bin | head -20",
    "timeout": 300
  }'
```

### Performance Benchmarking
```bash
# Run CPU benchmark
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "performance-test",
    "commands": "sysbench cpu --cpu-max-prime=20000 --threads=8 run",
    "timeout": 600
  }'
```

### Container Testing
```bash
# Test Docker setup in Alpine
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "alpine-docker",
    "commands": "apk add docker && service docker start && docker run hello-world",
    "timeout": 400
  }'
```

## 🔧 Customization Examples

### Custom VM Configuration
```bash
# Create custom config
cat > vm_configs/my-custom.conf << 'EOF'
# Custom web development VM
MEMORY="3G"
CPU="2"
ADDITIONAL_ARGS="-netdev user,id=net0,hostfwd=tcp::8080-:80,hostfwd=tcp::3000-:3000 -device e1000,netdev=net0 -nographic -serial stdio"
EOF
```

### Batch Processing Script
```bash
#!/bin/bash
# Process multiple VMs in parallel

VMS=("ubuntu-server" "centos-minimal" "alpine-docker")
COMMANDS="echo 'Testing VM' && uname -a && df -h"

for vm in "${VMS[@]}"; do
  echo "Starting $vm..."
  curl -X POST "http://localhost:8000/requests" \
    -H "Content-Type: application/json" \
    -d "{
      \"vm_name\": \"$vm\",
      \"commands\": \"$COMMANDS\",
      \"timeout\": 300
    }" &
done

wait
echo "All VMs started!"
```

### Monitoring Script
```bash
#!/bin/bash
# Monitor system status

while true; do
  clear
  echo "=== QEMU Simulation Status ==="
  python main.py cli stats
  echo ""
  echo "Running Requests:"
  python main.py cli list-requests --status running
  sleep 10
done
```

## 📖 Additional Resources

### VM Image Sources
- **Ubuntu Cloud Images**: https://cloud-images.ubuntu.com/
- **CentOS Cloud Images**: https://cloud.centos.org/centos/
- **Debian Cloud Images**: https://cloud.debian.org/images/cloud/
- **Alpine Virtual**: https://alpinelinux.org/downloads/

### QEMU Documentation
- **QEMU User Manual**: https://www.qemu.org/docs/master/system/
- **QEMU Network Guide**: https://wiki.qemu.org/Documentation/Networking
- **KVM Acceleration**: https://www.linux-kvm.org/page/Documents

### API Documentation
- **FastAPI Docs**: http://localhost:8000/docs (when running)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🆘 Getting Help

1. **Check the main README**: [../README.md](../README.md)
2. **Review VM Setup Guide**: [VM_SETUP_GUIDE.md](VM_SETUP_GUIDE.md)  
3. **Run configuration check**: `python main.py config`
4. **Check system status**: `python main.py status`
5. **View logs**: `python main.py cli show-logs <uuid>`
6. **Test manually**: `./scripts/qemu_runner.sh <vm-name> 60`

## 🤝 Contributing Examples

We welcome contributions of new examples, VM configurations, and documentation improvements!

### Adding New VM Configs
1. Create config file in `vm_configs/`
2. Test with `./scripts/qemu_runner.sh`
3. Document use case and requirements
4. Submit pull request

### Adding New Examples
1. Create example script in `examples/`
2. Include clear documentation
3. Test thoroughly
4. Follow existing code style

---

Happy VM automation! 🚀
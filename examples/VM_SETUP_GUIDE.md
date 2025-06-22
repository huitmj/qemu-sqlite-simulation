# VM Setup Guide and Examples

This guide provides detailed instructions for creating and configuring virtual machines for use with the QEMU SQLite Simulation System.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [VM Configuration Files](#vm-configuration-files)
- [Creating VM Images](#creating-vm-images)
- [Example Configurations](#example-configurations)
- [Testing Your VMs](#testing-your-vms)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

1. **Create VM images directory:**
   ```bash
   mkdir -p vm_images vm_configs
   ```

2. **Copy example configurations:**
   ```bash
   # Examples are provided in vm_configs/ directory
   ls vm_configs/
   ```

3. **Create your first VM image:**
   ```bash
   # Download Ubuntu Server ISO
   wget https://releases.ubuntu.com/20.04/ubuntu-20.04.6-live-server-amd64.iso

   # Create VM image
   qemu-img create -f qcow2 vm_images/ubuntu-server.qcow2 20G
   ```

4. **Install operating system:**
   ```bash
   qemu-system-x86_64 \
     -m 2G \
     -cdrom ubuntu-20.04.6-live-server-amd64.iso \
     -drive format=qcow2,file=vm_images/ubuntu-server.qcow2 \
     -boot d \
     -netdev user,id=net0 \
     -device e1000,netdev=net0
   ```

## ⚙️ VM Configuration Files

VM configuration files are stored in `vm_configs/` and use bash variable syntax:

```bash
# Basic configuration template
MEMORY="2G"              # RAM allocation
CPU="2"                  # Number of CPU cores
ADDITIONAL_ARGS="..."    # Extra QEMU arguments
```

### Configuration Variables

| Variable | Description | Examples |
|----------|-------------|----------|
| `MEMORY` | RAM allocation | `512M`, `1G`, `2G`, `4G` |
| `CPU` | Number of CPU cores | `1`, `2`, `4`, `8` |
| `ADDITIONAL_ARGS` | Extra QEMU parameters | Network, display, device options |

## 🖼️ Creating VM Images

### Method 1: Install from ISO

```bash
# 1. Create empty disk image
qemu-img create -f qcow2 vm_images/my-vm.qcow2 20G

# 2. Boot from ISO and install
qemu-system-x86_64 \
  -m 2G \
  -cdrom /path/to/installer.iso \
  -drive format=qcow2,file=vm_images/my-vm.qcow2 \
  -boot d \
  -netdev user,id=net0 \
  -device e1000,netdev=net0

# 3. After installation, test boot without ISO
qemu-system-x86_64 \
  -m 2G \
  -drive format=qcow2,file=vm_images/my-vm.qcow2 \
  -netdev user,id=net0 \
  -device e1000,netdev=net0
```

### Method 2: Download Pre-built Images

```bash
# Ubuntu Cloud Images (pre-configured)
wget https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img
qemu-img convert -f qcow2 -O qcow2 focal-server-cloudimg-amd64.img vm_images/ubuntu-cloud.qcow2

# Resize if needed
qemu-img resize vm_images/ubuntu-cloud.qcow2 20G
```

### Method 3: Convert Existing Images

```bash
# Convert VirtualBox VDI to qcow2
qemu-img convert -f vdi -O qcow2 existing-vm.vdi vm_images/converted-vm.qcow2

# Convert VMware VMDK to qcow2
qemu-img convert -f vmdk -O qcow2 existing-vm.vmdk vm_images/converted-vm.qcow2
```

## 📚 Example Configurations

### 1. Ubuntu Server (ubuntu-server.conf)
**Use Case:** General purpose server workloads, web development, CI/CD testing

```bash
MEMORY="2G"
CPU="2"
ADDITIONAL_ARGS="-netdev user,id=net0,hostfwd=tcp::2222-:22 -device e1000,netdev=net0 -nographic -serial stdio"
```

**Features:**
- SSH access on port 2222
- Console output via serial
- Network connectivity
- Suitable for automation

**API Usage:**
```bash
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "ubuntu-server",
    "commands": "sudo apt update && sudo apt install -y htop && htop --version",
    "timeout": 300
  }'
```

### 2. Ubuntu Desktop (ubuntu-desktop.conf)
**Use Case:** GUI application testing, desktop automation, user interface testing

```bash
MEMORY="4G"
CPU="4"
ADDITIONAL_ARGS="-netdev user,id=net0 -device e1000,netdev=net0 -vnc :0 -vga cirrus -device AC97"
```

**Features:**
- VNC access on port 5900
- Full desktop environment
- Audio support
- Graphical applications

**API Usage:**
```bash
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "ubuntu-desktop",
    "commands": "firefox --version && gnome-calculator",
    "timeout": 600
  }'
```

### 3. Alpine Docker (alpine-docker.conf)
**Use Case:** Container testing, microservices, lightweight workloads

```bash
MEMORY="512M"
CPU="1"
ADDITIONAL_ARGS="-netdev user,id=net0 -device virtio-net,netdev=net0 -nographic -serial stdio -enable-kvm -machine q35"
```

**Features:**
- Minimal resource usage
- Fast boot time
- Docker/Podman ready
- Security-focused

**API Usage:**
```bash
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "alpine-docker",
    "commands": "apk add docker && docker --version",
    "timeout": 180
  }'
```

### 4. Security Sandbox (security-sandbox.conf)
**Use Case:** Malware analysis, security research, isolated testing

```bash
MEMORY="2G"
CPU="2"
ADDITIONAL_ARGS="-netdev user,id=net0,restrict=on -device e1000,netdev=net0 -vnc :2 -vga std -snapshot -no-acpi"
```

**Features:**
- Network isolation
- Snapshot mode (no persistence)
- VNC access on port 5902
- Security-hardened

**API Usage:**
```bash
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "security-sandbox",
    "commands": "wget -O /tmp/test.bin https://example.com/suspicious-file && file /tmp/test.bin",
    "timeout": 300
  }'
```

### 5. Performance Test (performance-test.conf)
**Use Case:** Benchmarking, stress testing, performance analysis

```bash
MEMORY="8G"
CPU="8"
ADDITIONAL_ARGS="-netdev user,id=net0 -device virtio-net,netdev=net0 -nographic -serial stdio -enable-kvm -cpu host -machine q35 -smp 8 -device virtio-balloon"
```

**Features:**
- Maximum performance
- KVM acceleration
- Host CPU passthrough
- Large memory allocation

**API Usage:**
```bash
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "performance-test",
    "commands": "sysbench cpu --cpu-max-prime=20000 --threads=8 run",
    "timeout": 600
  }'
```

## 🧪 Testing Your VMs

### Manual Testing

```bash
# Test VM boots correctly
./scripts/qemu_runner.sh ubuntu-server 60

# Test with custom commands
echo "uname -a && date" | ./scripts/qemu_runner.sh ubuntu-server 120
```

### API Testing

```bash
# Submit test request
curl -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "vm_name": "ubuntu-server",
    "commands": "echo \"Hello from VM\" && uname -a",
    "timeout": 120
  }'

# Monitor progress
python main.py cli list-requests --status running
python main.py cli show-logs <uuid> --follow
```

### Automated Testing

```bash
# Create test script
cat > test_vm.sh << 'EOF'
#!/bin/bash
set -e

VM_NAME="$1"
echo "Testing VM: $VM_NAME"

# Submit request
RESPONSE=$(curl -s -X POST "http://localhost:8000/requests" \
  -H "Content-Type: application/json" \
  -d "{
    \"vm_name\": \"$VM_NAME\",
    \"commands\": \"echo 'Test successful' && exit 0\",
    \"timeout\": 300
  }")

UUID=$(echo $RESPONSE | jq -r '.uuid')
echo "Request UUID: $UUID"

# Wait for completion
while true; do
  STATUS=$(curl -s "http://localhost:8000/requests/$UUID" | jq -r '.status')
  echo "Status: $STATUS"
  
  if [[ "$STATUS" == "done" ]]; then
    echo "✅ Test completed successfully"
    break
  elif [[ "$STATUS" == "cancelled" ]]; then
    echo "❌ Test failed"
    exit 1
  fi
  
  sleep 5
done
EOF

chmod +x test_vm.sh
./test_vm.sh ubuntu-server
```

## 🛠️ VM Preparation Tips

### Ubuntu Server Setup

```bash
# During installation or first boot:

# 1. Enable auto-login (optional)
sudo systemctl edit getty@tty1
# Add these lines:
# [Service]
# ExecStart=
# ExecStart=-/sbin/agetty --autologin ubuntu --noclear %I $TERM

# 2. Install essential packages
sudo apt update
sudo apt install -y curl wget git htop python3 python3-pip

# 3. Configure SSH (if needed)
sudo systemctl enable ssh
sudo systemctl start ssh

# 4. Set up passwordless sudo (optional)
echo "ubuntu ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ubuntu

# 5. Clean up before shutdown
sudo apt autoremove -y
sudo apt autoclean
history -c
sudo shutdown -h now
```

### Alpine Linux Setup

```bash
# After boot:

# 1. Set up basic system
setup-alpine

# 2. Install essential packages
apk add curl wget git htop python3 py3-pip

# 3. Enable services
rc-update add docker boot
service docker start

# 4. Add user to docker group
addgroup $USER docker

# 5. Clean up
apk cache clean
history -c
poweroff
```

### Windows Setup

```bash
# Windows-specific setup notes:

# 1. Install guest additions/virtio drivers
# 2. Disable Windows Defender (for testing)
# 3. Enable auto-login
# 4. Install necessary software (browsers, tools)
# 5. Create restore point
# 6. Shutdown cleanly
```

## 🔧 Custom VM Configurations

### Creating Custom Configs

```bash
# Create new configuration
cat > vm_configs/my-custom-vm.conf << 'EOF'
# My Custom VM Configuration
MEMORY="3G"
CPU="4"

# Custom networking with port forwarding
ADDITIONAL_ARGS="-netdev user,id=net0,hostfwd=tcp::8080-:80,hostfwd=tcp::3000-:3000 -device virtio-net,netdev=net0 -nographic -serial stdio"
EOF
```

### Advanced Networking

```bash
# Multiple network interfaces
ADDITIONAL_ARGS="-netdev user,id=net0 -device e1000,netdev=net0 -netdev user,id=net1 -device virtio-net,netdev=net1"

# Bridge networking (requires setup)
ADDITIONAL_ARGS="-netdev bridge,id=net0,br=br0 -device virtio-net,netdev=net0"

# No network (isolated)
ADDITIONAL_ARGS="-nographic -serial stdio"
```

### Storage Options

```bash
# Multiple disks
ADDITIONAL_ARGS="-drive format=qcow2,file=vm_images/disk1.qcow2 -drive format=qcow2,file=vm_images/disk2.qcow2"

# Shared folder (requires guest support)
ADDITIONAL_ARGS="-virtfs local,path=/host/shared,mount_tag=host0,security_model=passthrough,id=host0"

# Read-only disk
ADDITIONAL_ARGS="-drive format=qcow2,file=vm_images/readonly.qcow2,readonly=on"
```

## ❗ Troubleshooting

### Common Issues

#### VM Won't Boot
```bash
# Check image integrity
qemu-img check vm_images/your-vm.qcow2

# Test boot manually
qemu-system-x86_64 -m 1G -drive format=qcow2,file=vm_images/your-vm.qcow2 -nographic

# Check QEMU version
qemu-system-x86_64 --version
```

#### Network Issues
```bash
# Test network connectivity
# In VM configuration, add:
ADDITIONAL_ARGS="-netdev user,id=net0,dns=8.8.8.8 -device e1000,netdev=net0"

# Check port forwarding
# Host: telnet localhost 2222
# Should connect to VM SSH (if configured)
```

#### Performance Issues
```bash
# Enable KVM acceleration
ADDITIONAL_ARGS="-enable-kvm -cpu host"

# Use virtio drivers
ADDITIONAL_ARGS="-device virtio-net,netdev=net0 -drive if=virtio,format=qcow2,file=\$VM_IMAGE"

# Allocate more resources
MEMORY="4G"
CPU="4"
```

#### Console Access Issues
```bash
# Ensure serial console is enabled
ADDITIONAL_ARGS="-nographic -serial stdio"

# Alternative: VNC access
ADDITIONAL_ARGS="-vnc :0"
# Then connect with VNC viewer to localhost:5900
```

### Debug Commands

```bash
# Test VM configuration
python main.py config
python main.py status

# Manual VM test
./scripts/qemu_runner.sh your-vm 60

# Check logs
python main.py cli show-logs <uuid> --log-type stderr

# Database inspection
sqlite3 simulation.db "SELECT * FROM requests WHERE status='cancelled';"
```

### Getting Help

1. **Check system requirements:**
   - QEMU installed and accessible
   - Sufficient disk space for VM images
   - Adequate RAM for VM allocation

2. **Review configuration:**
   - VM image exists and is bootable
   - Configuration syntax is correct
   - Network settings are appropriate

3. **Test incrementally:**
   - Start with basic configuration
   - Add features one at a time
   - Test each change

4. **Community resources:**
   - QEMU documentation: https://www.qemu.org/docs/
   - GitHub Issues: Report bugs and get help
   - VM-specific forums for OS installation help

## 📝 Configuration Reference

### Common QEMU Arguments

| Argument | Purpose | Example |
|----------|---------|---------|
| `-m` | Memory allocation | `-m 2G` |
| `-smp` | CPU cores | `-smp 4` |
| `-nographic` | Console only | `-nographic` |
| `-vnc` | VNC server | `-vnc :0` |
| `-netdev` | Network backend | `-netdev user,id=net0` |
| `-device` | Add device | `-device e1000,netdev=net0` |
| `-enable-kvm` | KVM acceleration | `-enable-kvm` |
| `-cpu` | CPU model | `-cpu host` |
| `-machine` | Machine type | `-machine q35` |
| `-snapshot` | Temporary mode | `-snapshot` |

### Memory Specifications

| Syntax | Amount |
|--------|--------|
| `512M` | 512 MB |
| `1G` | 1 GB |
| `2G` | 2 GB |
| `4G` | 4 GB |
| `8192M` | 8 GB |

This guide should help you create and configure VMs for any use case with the QEMU SQLite Simulation System!
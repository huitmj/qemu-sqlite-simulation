#!/bin/bash

# QEMU VM Runner Script
# Usage: ./qemu_runner.sh <vm_name> <timeout> [additional_args]

VM_NAME="$1"
TIMEOUT="$2"
ADDITIONAL_ARGS="${@:3}"

# Default values
DEFAULT_MEMORY="512M"
DEFAULT_CPU="1"
DEFAULT_DISK_SIZE="2G"

# VM Configuration directory
VM_CONFIG_DIR="./vm_configs"
VM_IMAGES_DIR="./vm_images"

# Create directories if they don't exist
mkdir -p "$VM_CONFIG_DIR"
mkdir -p "$VM_IMAGES_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if VM image exists
check_vm_image() {
    local vm_path="$VM_IMAGES_DIR/$VM_NAME.qcow2"
    if [ ! -f "$vm_path" ]; then
        log_message "ERROR: VM image not found: $vm_path"
        log_message "Please create the VM image first or check the VM name"
        exit 1
    fi
    echo "$vm_path"
}

# Function to get VM configuration
get_vm_config() {
    local config_file="$VM_CONFIG_DIR/$VM_NAME.conf"
    
    # Default configuration
    MEMORY="$DEFAULT_MEMORY"
    CPU="$DEFAULT_CPU"
    
    # Load custom configuration if exists
    if [ -f "$config_file" ]; then
        source "$config_file"
        log_message "Loaded configuration from $config_file"
    else
        log_message "Using default configuration for $VM_NAME"
    fi
}

# Function to start QEMU with monitoring
start_qemu() {
    local vm_image="$1"
    
    log_message "Starting QEMU VM: $VM_NAME"
    log_message "Memory: $MEMORY, CPU: $CPU, Timeout: ${TIMEOUT}s"
    
    # QEMU command with serial console output
    timeout "$TIMEOUT" qemu-system-x86_64 \
        -m "$MEMORY" \
        -smp "$CPU" \
        -drive format=qcow2,file="$vm_image" \
        -nographic \
        -serial stdio \
        -monitor none \
        -no-reboot \
        $ADDITIONAL_ARGS 2>&1
    
    local exit_code=$?
    
    if [ $exit_code -eq 124 ]; then
        log_message "VM execution timed out after $TIMEOUT seconds"
    elif [ $exit_code -eq 0 ]; then
        log_message "VM execution completed successfully"
    else
        log_message "VM execution failed with exit code: $exit_code"
    fi
    
    return $exit_code
}

# Main execution
main() {
    # Validate arguments
    if [ -z "$VM_NAME" ] || [ -z "$TIMEOUT" ]; then
        echo "Usage: $0 <vm_name> <timeout> [additional_qemu_args]"
        echo "Example: $0 ubuntu-server 300 -netdev user,id=net0 -device e1000,netdev=net0"
        exit 1
    fi
    
    # Validate timeout is numeric
    if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
        log_message "ERROR: Timeout must be a number (seconds)"
        exit 1
    fi
    
    log_message "=== QEMU VM Runner Started ==="
    log_message "VM Name: $VM_NAME"
    log_message "Timeout: $TIMEOUT seconds"
    
    # Check VM image exists
    VM_IMAGE=$(check_vm_image)
    
    # Get VM configuration
    get_vm_config
    
    # Start QEMU
    start_qemu "$VM_IMAGE"
    
    local final_exit_code=$?
    log_message "=== QEMU VM Runner Finished ==="
    
    exit $final_exit_code
}

# Run main function
main "$@"
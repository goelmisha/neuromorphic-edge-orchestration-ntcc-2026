#!/bin/bash
# This script demonstrates live migration of the lava_snn_workload.py process using CRIU
# from k8s-master to k8s-worker1.

# Ensure Vagrant VMs are running and provisioned
echo "Checking Vagrant VMs status..."
vagrant status k8s-master k8s-worker1 | grep -q 'running' || { echo "Vagrant VMs not running. Please run 'vagrant up --provision' first."; exit 1; }

# --- Step 0: Ensure CRIU prerequisites are met and Redis is accessible ---
echo "Ensure CRIU is installed on VMs and Redis is exposed on k8s-master (192.168.56.100:6379)."
echo "This setup requires 'vagrant up --provision' after applying changes to Vagrantfile and docker-compose.yml."
echo "Also, Python scripts (lava_snn_workload.py, test_spike.py, dashboard.py) should be updated to use 192.168.56.100 for Redis."
sleep 2

# --- Step 1: Prepare the SNN workload script on VMs ---
echo "Copying lava_snn_workload.py to /tmp on both VMs..."
vagrant ssh k8s-master -c "sudo cp /vagrant/lava_snn_workload.py /tmp/"
vagrant ssh k8s-worker1 -c "sudo cp /vagrant/lava_snn_workload.py /tmp/"

# --- Step 2: Start the SNN workload on k8s-master ---
echo "Starting lava_snn_workload.py on k8s-master..."
# It's important to run it as a regular user or ensure proper permissions for CRIU
vagrant ssh k8s-master -c "python3 /tmp/lava_snn_workload.py & echo \$! > /tmp/snn_pid"
sleep 5 # Give it some time to initialize and connect to Redis

SNN_PID=$(vagrant ssh k8s-master -c "cat /tmp/snn_pid")
echo "SNN workload started on k8s-master with PID: $SNN_PID"

# You can run 'nix develop --command python test_spike.py' and 'nix develop --command python dashboard.py' now
# to see the workload running on k8s-master before migration.
echo "Run 'nix develop --command python test_spike.py' and 'nix develop --command python dashboard.py' in separate terminals to see the live data."
echo "Press Enter to proceed with checkpointing..."
read

# --- Step 3: Checkpoint the SNN workload on k8s-master ---
echo "Checkpointing SNN workload on k8s-master (PID: $SNN_PID)..."
vagrant ssh k8s-master -c "sudo mkdir -p /tmp/snn_checkpoint && sudo criu dump -t $SNN_PID -D /tmp/snn_checkpoint --shell-job --tcp-established --ext-unix"

if [ $? -eq 0 ]; then
    echo "Checkpoint successful. Transferring checkpoint images to k8s-worker1..."
else
    echo "Checkpoint failed. Exiting."
    exit 1
fi

# --- Step 4: Transfer checkpoint images to k8s-worker1 ---
# Using vagrant scp to transfer the directory
vagrant scp k8s-master:/tmp/snn_checkpoint k8s-worker1:/tmp/snn_checkpoint

if [ $? -eq 0 ]; then
    echo "Checkpoint images transferred to k8s-worker1. Restoring..."
else
    echo "Checkpoint transfer failed. Exiting."
    exit 1
fi

# --- Step 5: Kill the original process on k8s-master (important for live migration) ---
echo "Killing the original SNN process on k8s-master (PID: $SNN_PID)..."
vagrant ssh k8s-master -c "sudo kill -9 $SNN_PID"

# --- Step 6: Restore the SNN workload on k8s-worker1 ---
echo "Restoring SNN workload on k8s-worker1..."
vagrant ssh k8s-worker1 -c "sudo criu restore -D /tmp/snn_checkpoint --shell-job"

if [ $? -eq 0 ]; then
    echo "SNN workload successfully migrated and restored on k8s-worker1!"
    echo "The dashboard should continue to show spikes, now originating from k8s-worker1."
else
    echo "Restore failed on k8s-worker1. Check logs."
    exit 1
fi

echo "Migration process complete. You can clean up by running 'sudo rm -rf /tmp/snn_checkpoint /tmp/snn_pid' on both VMs."
echo "And 'pkill -f lava_snn_workload.py' if the process is still running after a failed restore."

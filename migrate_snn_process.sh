#!/bin/bash
# This script demonstrates live migration of the lava_snn_workload.py process using CRIU
# from k8s-master to k8s-worker1 and logs migration telemetry.

echo "Checking Vagrant VMs status..."
vagrant.exe status k8s-master k8s-worker1 | grep -q 'running' || { echo "Vagrant VMs not running. Please run 'vagrant.exe up --provision' first."; exit 1; }

echo "Ensure CRIU is installed on VMs and Redis is exposed on k8s-master (192.168.56.100:6379)."
sleep 2

echo "Copying lava_snn_workload.py to /tmp on both VMs..."
vagrant.exe ssh k8s-master -c "sudo cp /vagrant/lava_snn_workload.py /tmp/"
vagrant.exe ssh k8s-worker1 -c "sudo cp /vagrant/lava_snn_workload.py /tmp/"

echo "Starting lava_snn_workload.py on k8s-master..."
vagrant.exe ssh k8s-master -c "python3 /tmp/lava_snn_workload.py & echo \$! > /tmp/snn_pid"
sleep 5 

SNN_PID=$(vagrant.exe ssh k8s-master -c "cat /tmp/snn_pid")
echo "SNN workload started on k8s-master with PID: $SNN_PID"
echo "Press Enter to proceed with checkpointing and start the telemetry timer..."
read

# --- Phase 2: Checkpoint ---
echo "Checkpointing SNN workload on k8s-master (PID: $SNN_PID)..."
T1=$(date +%s%3N)
vagrant.exe ssh k8s-master -c "sudo mkdir -p /tmp/snn_checkpoint && sudo criu dump -t $SNN_PID -D /tmp/snn_checkpoint --shell-job --tcp-established --ext-unix"
T2=$(date +%s%3N)
DUMP_MS=$((T2 - T1))

if [ $? -ne 0 ]; then
    echo "Checkpoint failed. Exiting."
    exit 1
fi

# --- Phase 3: Transfer ---
echo "Transferring checkpoint images to k8s-worker1..."
T3=$(date +%s%3N)
vagrant.exe scp k8s-master:/tmp/snn_checkpoint k8s-worker1:/tmp/snn_checkpoint
T4=$(date +%s%3N)
TRANSFER_MS=$((T4 - T3))

if [ $? -ne 0 ]; then
    echo "Checkpoint transfer failed. Exiting."
    exit 1
fi

echo "Killing the original SNN process on k8s-master (PID: $SNN_PID)..."
vagrant.exe ssh k8s-master -c "sudo kill -9 $SNN_PID"

# --- Phase 4: Restore ---
echo "Restoring SNN workload on k8s-worker1..."
T5=$(date +%s%3N)
vagrant.exe ssh k8s-worker1 -c "sudo criu restore -D /tmp/snn_checkpoint --shell-job"
T6=$(date +%s%3N)
RESTORE_MS=$((T6 - T5))

if [ $? -eq 0 ]; then
    echo -e "\n======================================"
    echo " LIVE MIGRATION TELEMETRY (ms)"
    echo "======================================"
    echo " Phase 1 (Checkpoint) : ${DUMP_MS} ms"
    echo " Phase 2 (Transfer)   : ${TRANSFER_MS} ms"
    echo " Phase 3 (Restore)    : ${RESTORE_MS} ms"
    echo "--------------------------------------"
    echo " TOTAL DOWNTIME       : $((DUMP_MS + TRANSFER_MS + RESTORE_MS)) ms"
    echo "======================================"
else
    echo "Restore failed on k8s-worker1. Check logs."
    exit 1
fi

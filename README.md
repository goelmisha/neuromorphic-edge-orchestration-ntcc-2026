# neuromorphic-edge-orchestration-ntcc-2026

This repository contains the empirical testbed and orchestration pipeline for deploying and live-migrating Spiking Neural Network (SNN) workloads across a decentralized edge-cloud architecture. 

## Architecture Overview
* **Compute Substrate:** K3s Kubernetes control plane (`k8s-master`) and ARM64-simulated edge node (`k8s-worker1`) provisioned via Vagrant/VirtualBox.
* **Network Mesh:** Tailscale overlay network enforcing a strict 1280-byte MTU to prevent packet fragmentation.
* **Workload:** Intel Lava framework (`lava-dl`) executing a Leaky Integrate-and-Fire (LIF) neural layer.
* **Telemetry Bus:** Asynchronous Alpine Redis broker.
* **State Migration:** Checkpoint/Restore in Userspace (CRIU) orchestrating host-level SNN process migration.

## Prerequisites
* Vagrant & VirtualBox
* Docker & Docker Compose
* Nix (for hermetic Python environment reproduction)

## Execution Pipeline

**1. Provision Infrastructure**
```bash
vagrant up --provision
```
*(Note: Authenticate both nodes via the Tailscale URLs provided in the console output).*

**2. Initialize Telemetry Broker**
```bash
docker compose up -d telemetry-broker
```

**3. Launch the Observation Dashboard**
Open a new terminal:
```bash
nix develop --command python dashboard.py
```

**4. Start the SNN Workload**
Open a new terminal and deploy the process to the control plane:
```bash
vagrant ssh k8s-master -c "python3 /vagrant/lava_snn_workload.py & echo \$! > /tmp/snn_pid"
```

**5. Trigger the Data Ingestion Engine**
Open a new terminal to begin feeding the 768-D dense vector stream into the SNN:
```bash
nix develop --command python test_spike.py
```

**6. Execute Live Migration**
Trigger the CRIU state-transfer sequence from the control plane to the target edge node:
```bash
bash migrate_snn_process.sh
```

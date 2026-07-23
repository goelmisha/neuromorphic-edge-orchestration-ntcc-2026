Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.boot_timeout = 600

  # Control Plane (x86 Primary Workstation)
  config.vm.define "k8s-master" do |master|
    master.vm.hostname = "k8s-master"
    master.vm.network "private_network", ip: "192.168.56.100"
    master.vm.provider "virtualbox" do |vb|
      vb.name = "k8s-master"
      vb.memory = "3000"
      vb.cpus = 4
      vb.gui = true
      vb.customize ["modifyvm", :id, "--uartmode1", "disconnected"]
    end
    master.vm.provision "shell", inline: <<-SHELL
      sudo ip link set enp0s8 mtu 1280

      # Install Tailscale
      curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.no-arch.gpg | sudo dd of=/usr/share/keyrings/tailscale-archive-keyring.gpg
      echo "deb [signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg] https://pkgs.tailscale.com/stable/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/tailscale.list
      sudo apt-get update
      sudo apt-get install -y tailscale

      # Bring up Tailscale
      sudo tailscale up --hostname $(hostname) --accept-routes --advertise-routes=192.168.56.0/24 & # Run in background

      curl -sfL https://get.k3s.io | sh -
      sleep 10
      cp /var/lib/rancher/k3s/server/node-token /vagrant/node-token
      chmod 644 /vagrant/node-token
    SHELL
  end

  # Edge Target (ARM64 Edge Node Simulation)
  config.vm.define "k8s-worker1" do |worker1|
    worker1.vm.hostname = "k8s-worker1"
    worker1.vm.network "private_network", ip: "192.168.56.101"
    worker1.vm.provider "virtualbox" do |vb|
      vb.name = "k8s-worker1"
      vb.memory = "2048"
      vb.cpus = 1
      vb.gui = true
      vb.customize ["modifyvm", :id, "--uartmode1", "disconnected"]
    end
    worker1.vm.provision "shell", inline: <<-SHELL
      sudo ip link set enp0s8 mtu 1280

      # Install Tailscale
      curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.no-arch.gpg | sudo dd of=/usr/share/keyrings/tailscale-archive-keyring.gpg
      echo "deb [signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg] https://pkgs.tailscale.com/stable/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/tailscale.list
      sudo apt-get update
      sudo apt-get install -y tailscale

      # Bring up Tailscale
      sudo tailscale up --hostname $(hostname) --accept-routes & # Run in background

      while [ ! -f /vagrant/node-token ]; do sleep 2; done
      curl -sfL https://get.k3s.io | K3S_URL=https://192.168.56.100:6443 K3S_TOKEN=$(cat /vagrant/node-token) sh -
    SHELL
  end
end

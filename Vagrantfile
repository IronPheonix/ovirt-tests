# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "centos/7"

  N = 2
  (1..N).each do |host_id|
    config.vm.define "host#{host_id}" do |host|
      host.vm.hostname = "host#{host_id}.local"
      host.vm.network "private_network", ip: "192.168.200.1#{host_id}"

      host.vm.provision "shell", path: "scripts/host.sh"

      host.vm.provider :libvirt do |libvirt|
        libvirt.memory = 2028
      end
    end
  end

  config.vm.define "storage" do |storage|
    storage.vm.hostname = "storage.local"
    storage.vm.network "private_network", ip: "192.168.200.13"

    storage.vm.provision "shell", path: "scripts/storage.sh"

    storage.vm.provider "libvirt" do |libvirt|
      libvirt.storage :file, :size => '20G'
      libvirt.storage :file, :size => '20G'
      libvirt.storage :file, :size => '20G'
    end
  end

  config.vm.define "engine" do |engine|
    engine.vm.hostname = "ovirt.local"
    engine.vm.network "private_network", ip: "192.168.200.10"

    engine.vm.provision "shell", path: "scripts/engine.sh"

    engine.vm.provision "ansible" do |ansible|
      ansible.limit = "engine,storage"
      ansible.playbook = 'engine.yml'
    end

    engine.vm.provider :libvirt do |libvirt|
      libvirt.memory = 1024
    end

  end

end

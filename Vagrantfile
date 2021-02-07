# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

# How many slave nodes we want to create
SLAVE_COUNT = 4

# Default box to use
BOX_IMAGE = 'ubuntu/xenial64'

# Default starting address
IP_START = 10

# Name of the playbook to run
PLAYBOOK = 'example.yml'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Create the master node
  config.vm.define 'master', primary: true do |subconfig|
    subconfig.vm.box = BOX_IMAGE
    subconfig.vm.network :private_network, ip: '10.0.1.10'
  end

  # Create the slave nodes
  # (1..SLAVE_COUNT).each do |machine_id|
  #  box_name = "node#{machine_id}"

  #  # Setup one slave node
  #  config.vm.define box_name do |subconfig|
  #    subconfig.vm.box = BOX_IMAGE
  #    subconfig.vm.network :private_network, ip: "10.0.1.#{machine_id + IP_START}"

  #    # Only execute once the Ansible provisioner,
  #    # when all the machines are up and ready.
  #    if machine_id == SLAVE_COUNT
  #      subconfig.vm.provision :ansible do |ansible|
  #        # Disable default limit to connect to all the machines
  #        ansible.limit = 'all'
  #        ansible.playbook = PLAYBOOK

  #        ansible.groups = {
  #          'slaves' => (1..SLAVE_COUNT).map { |i| "node#{i}" }
  #        }
  #      end
  #    end
  #  end
  # end

  # Tell vagrant about system resources we want to use
  config.vm.provider :libvirt do |libvirt|
    # Customize the amount of memory on the VM:
    libvirt.memory = 1024
    # Customize the number of cpus on the VM:
    libvirt.cpus = 4

    # Use QEMU session instead of system connection
    libvirt.host = "nswi106_screencast"
    libvirt.username = "screencast"
    libvirt.driver = "qemu"
    libvirt.connect_via_ssh = true
    libvirt.id_ssh_key_file = "./secret/id_rsa"
    libvirt.management_network_device = "virbr0"
  end

  # Disable mounting the default vagrant folder
  config.vm.synced_folder '.', '/vagrant', disabled: true
end

# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

NODE_COUNT = 2

# Default box to use
BOX_IMAGE = 'ubuntu/xenial64'

# Assign IP address to machines
IP_START = 10

# Ansible playbook for provisioning
PLAYBOOK = './spark.yml'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Create the master node
  config.vm.define 'master', primary: true do |subconfig|
    subconfig.vm.box = BOX_IMAGE
    subconfig.vm.network :private_network, ip: "10.0.1.#{IP_START}"
    subconfig.vm.network :forwarded_port, guest: 8080, host: 8080
  end

  # Create the slave nodes
  (1..NODE_COUNT).each do |machine_id|
    box_name = "node#{machine_id}"
    config.vm.define box_name do |box|
      box.vm.box = BOX_IMAGE
      box.vm.network :private_network, ip: "10.0.2.#{machine_id + IP_START}"

      # Only execute once the Ansible provisioner,
      # when all the machines are up and ready.
      if machine_id == NODE_COUNT
        box.vm.provision :ansible do |ansible|
          # Disable default limit to connect to all the machines
          ansible.limit = 'all'
          ansible.playbook = PLAYBOOK
          ansible.groups = {
            'slaves' => (1..NODE_COUNT).map { |i| "node#{i}" }
          }
        end
      end
    end
  end

  # Disable mounting the default vagrant folder
  config.vm.synced_folder '.', '/vagrant', disabled: true

  config.vm.provider 'virtualbox' do |vb|
    # Customize the amount of memory on the VM:
    vb.memory = 1024
    # Customize the amount of memory on the VM:
    vb.cpus = 4
  end
end

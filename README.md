# NSWI106-screencast

## What is Vagrant?

TODO

## What is Ansible?

Todo

## What is Spark?

TODO


## Installation

In this screencast we will be using a Linux environment. However, the tools we
use are relatively OS agnostic, so there shouldn't have many problems applying
these steps on a different architecture.

Firstly, we will have to install the required tools, i.e. ``vagrant`` and
``ansible``. Both tools are quite popular and should be available in the
repositories of your distributions package manager. Otherwise, please refer to
their respective install pages.

- [Vagrant Installation](https://www.vagrantup.com/docs/installation)
- [Ansible Installation](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

Additionally, for testing purpuses we will use the ``virtualbox`` hypervisor.
Again, follow the official [installation guide](https://www.virtualbox.org/wiki/Downloads).


## Architecture

We will setup a simple Spark architecture with one **master** (control) node
and several **slave** nodes all connected and managed by the master. We will
have them all on the same network.

We will assign IP addresses as follows

|   node  	|        IP        	|
|:-------:	|:----------------:	|
| master  	| 10.0.1.10        	|
| slave01 	| 10.0.1.11        	|
| slave02 	| 10.0.1.12        	|
| ...     	|                  	|
| slaveXX 	| 10.0.1.(10 + XX) 	|

TODO: figure spark network


## Vagrant setup

We create a new directory ``./spark_example`` where we will store our setup.

For testing purpuses, we will setup our machines using ``vagrant``. We will use
the ``ubuntu/xenial64`` *box* (virtual machine image) provided by the
community. More boxes can be found on the [official Vagrant
site](https://app.vagrantup.com/boxes/search).

To create the initial configuration file we can run

```
> vagrant init ubuntu/xenial64
A `Vagrantfile` has been placed in this directory. You are now
ready to `vagrant up` your first virtual environment! Please read
the comments in the Vagrantfile as well as documentation on
`vagrantup.com` for more information on using Vagrant.

```

This will create a ``Vagrantfile`` in the current working directory. This file
contains a lot of comments with tips and example comfigurations. Vagrant uses
``ruby`` for configuration files, but for basic setups the knowledge of ruby is
not required.

You can now run ``vagrant up`` and ``vagrant`` will download the requested box
for you and start up the VM. You can access the VM through SSH with the
``vagrant ssh`` command. If you are done using your machine, you can turn it of
with ``vagrant halt`` or save its state with ``vagrant suspend``.  If you are
truly done with it use ``vagrant destroy`` to delete it.

``spark_example/Vagrantfile``

```ruby
# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'
BOX_NAME = 'ubuntu/xenial64'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box = BOX_NAME
end
```

As you can see, the amount of configuration required to setup a VM with vagrant
is minimal.

Next, we will setup a multi-machine environment connected through a private
network. With ``vagrant`` we can do that with only few lines of code.  To
assign a IP address to a machine and setup a private network you can use the
following vagrant option to your configuration:

```ruby
config.vm.network :private_network, ip: "AAA.BBB.CCC.DDD"
```

Every time you make some drastic changes to your configuration be sure to run
``vagrant destroy -f`` to delete your machines. Sometimes vagrant can start
from a changed configuration with only ``vagrant reload``, but in the early
testing stages it is much easier to create your VMs from scratch.

In a multi-machine setup we will have to configure the machines individually.
We can do that with a simple *for loop* like so:

```ruby
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

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Create the slave nodes
  (1..SLAVE_COUNT).each do |machine_id|

    box_name = "node#{machine_id}"

    # Setup one slave node
    config.vm.define box_name do |subconfig|
      subconfig.vm.box = BOX_IMAGE
      subconfig.vm.network :private_network, ip: "10.0.2.#{machine_id + IP_START}"
    end
  end
end
```

You can now ``vagrant up`` to create your machines. Note that there is a small
change in some of vagrant commands in multi-machine setups. For example to
``vagrant ssh`` into a machine you have to explicitly specify the machine name
as defined in the vagrant configuration. So ``vagrant ssh node1`` would connect
you to the first node. However, you can define one of your machines to be
``primary`` which will be the default option when running ``vagrant ssh``.  We
will do that shortly when we define the *master* node.

We also want to tell vagrant about the system resources we want for out
machines. We will do that globally with the ``config.vm.provider`` option.

```ruby
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

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Create the master node
  config.vm.define 'master', primary: true do |subconfig|
    subconfig.vm.box = BOX_IMAGE
    subconfig.vm.network :private_network, ip: "10.0.1.10"
  end

  # Create the slave nodes
  (1..SLAVE_COUNT).each do |machine_id|

    box_name = "node#{machine_id}"

    # Setup one slave node
    config.vm.define box_name do |subconfig|
      subconfig.vm.box = BOX_IMAGE
      subconfig.vm.network :private_network, ip: "10.0.1.#{machine_id + IP_START}"
    end
  end

  # Tell vagrant about system resources we want to use
  config.vm.provider 'virtualbox' do |vb|
    # Customize the amount of memory on the VM:
    vb.memory = 1024
    # Customize the number of cpus on the VM:
    vb.cpus = 4
  end

  # Disable mounting the default vagrant folder
  config.vm.synced_folder '.', '/vagrant', disabled: true
end
```

By default vagrant also mounts the current working directory as NFS drive to
the VM. We disabled this behaviour in the last few lines of the config.

You should now be able to connect to the master node by running ``vagrant ssh``
(without additional arguments) and from there ``ping`` other VMs on the network.

```
vagrant> ping 10.0.1.11
PING 10.0.1.11 (10.0.1.11) 56(84) bytes of data.
64 bytes from 10.0.1.11: icmp_seq=1 ttl=64 time=0.546 ms
64 bytes from 10.0.1.11: icmp_seq=2 ttl=64 time=0.547 ms
64 bytes from 10.0.1.11: icmp_seq=3 ttl=64 time=0.362 ms
...
```

## Provisioning

For provisioning we will be using ansible. Ansible configuration is done via
configuration files written in YAML called *playbooks*. Playbooks contain a
list of so-called *plays* which are essentially groups of tasks you want to
execute. Tasks are a list of *modules* which are usually the most atomic parts
of your playbooks.

A typical playbook will look something like this:
```yaml
--- # Three dashes signify YAML file, Ansible doesn't care if you forget them though
- name: My first play!
  hosts: all
  tasks:
    - name: "My first task!"
      debug: msg="Hello from VM"

- name: "My second play!"
  hosts: all
  become: True  # get superuser privilages
  tasks:
    - name: Notify user what I want to do
      debug:
        msg: I'm going upgrade a package

    - name: Upgrade the system
      apt: upgrade=yes

    - debug: msg="System is upgraded, also the `name` field is optional (but improves readability)."
```

Here we can see the ``debug`` and ``apt`` modules used. To view the full list
of supported options you can use the ``ansible-doc`` command that comes with
Ansible.

There is a lot to YAML syntax and Ansible configuration. We will explore only a
small subset of these features. If you want to know more definitely visit the
official [ansible documentation](https://docs.ansible.com/).

Next, we need to tell Ansible about the machines we want to configure. This
would typically be done through the so called *inventory*, where you specify
the hosts ansible should configure. Additionally, ansible can group hosts into
*groups*, which simplifies the configuration even further.

We will however skip this step entirely and use the built-in vagrant support
for ansible. Take the example playbook and put it into a file called
``example.yml`` in the project directory.

We will modify the ``Vagrantfile`` by adding the following lines to the
configuration.

```ruby
    config.vm.provision :ansible do |ansible|
      ansible.playbook = 'example.yml'
    end
```

You can now run ``vagrant provision`` and vagrant will setup the required
inventory and provision the VMs for you! You will see the VMs provisioned one
after another. This is actually something you don't want because ansible is
fully able (and in part expects) to run the plays in parallel. To our knowledge
there is currently no other way then running the provisioning only from the
last machine provisioned by vagrant. This "hack" is also endorsed by ansible
documentation and it's sad that there is no other, cleaner way.

We will also one last change to the vagrant configuration by telling vagrant
to add our slave nodes to a ``slaves`` group in the ansible inventory.

The final ``Vagrantfile`` looks like this:

```ruby
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
    subconfig.vm.network :private_network, ip: "10.0.1.10"
  end

  # Create the slave nodes
  (1..SLAVE_COUNT).each do |machine_id|

    box_name = "node#{machine_id}"

    # Setup one slave node
    config.vm.define box_name do |subconfig|
      subconfig.vm.box = BOX_IMAGE
      subconfig.vm.network :private_network, ip: "10.0.1.#{machine_id + IP_START}"

      # Only execute once the Ansible provisioner,
      # when all the machines are up and ready.
      if machine_id == SLAVE_COUNT
        subconfig.vm.provision :ansible do |ansible|
          # Disable default limit to connect to all the machines
          ansible.limit = 'all'
          ansible.playbook = PLAYBOOK

          ansible.groups = {
            'slaves' => (1..SLAVE_COUNT).map { |i| "node#{i}" }
          }
        end
      end
    end
  end

  # Tell vagrant about system resources we want to use
  config.vm.provider 'virtualbox' do |vb|
    # Customize the amount of memory on the VM:
    vb.memory = 1024
    # Customize the number of cpus on the VM:
    vb.cpus = 4
  end

  # Disable mounting the default vagrant folder
  config.vm.synced_folder '.', '/vagrant', disabled: true
end
```

If you run ``vagrant provision`` now you should see all the machines
provisioned in parallel.

By the way, if you are interested in how the ansible inventory looks like you
can look into the
``.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory`` in your
project directory which is a ansible inventory file generated by automagically
by vagrant.


## Installing Apache Spark through Ansible

We will now start with installation of Apache Spark on out machines. Spark is
not available through the official repositories so we will have to install it
manually. However, the installation is very simple and will serve as a pretty
good example to how are thing done in ansible.

We will assume that ansible has configured one host called ``master`` and a
group of hosts called ``slaves``. 

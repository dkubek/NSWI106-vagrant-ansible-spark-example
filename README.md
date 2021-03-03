# NSWI106-screencast

## Introduction

Final task for the NSWI106 - Linux Administration course. Setup of Apache spark
cluster using Vagrant and Ansible.

## What is Vagrant?

> Vagrant is a tool for building and managing virtual machine environments in a
> single workflow. With an easy-to-use workflow and focus on automation,
> Vagrant lowers development environment setup time, increases production
> parity, and makes the "works on my machine" excuse a relic of the past.

> Vagrant provides easy to configure, reproducible, and portable work
> environments built on top of industry-standard technology and controlled by a
> single consistent workflow to help maximize the productivity and flexibility
> of you and your team.

*Source:* [Vagrant intro](https://www.vagrantup.com/intro)

## What is Ansible?

> Ansible is an open-source software for provisioning, configuration
> management, and application-deployment tool enabling **infrastructure as code.**

*Source:* [Ansible wiki](https://en.wikipedia.org/wiki/Ansible_(software))


## What is Spark?

> Apache Spark is a unified analytics engine for large-scale data processing.
> It provides high-level APIs in Java, Scala, Python and R, and an optimized
> engine that supports general execution graphs. It also supports a rich set of
> higher-level tools including Spark SQL for SQL and structured data
> processing, MLlib for machine learning, GraphX for graph processing, and
> Structured Streaming for incremental computation and stream processing.

*Source:* [Spark overview](https://spark.apache.org/docs/latest/)

## Installation

In this screencast we will be using a Linux environment. However, the tools we
use are relatively OS agnostic, so there shouldn't be many problems applying
these steps to a different architecture.

Firstly, we will have to install the required tools, i.e. ``vagrant``  and
``ansible``. Both tools are quite popular and should be available in the
repositories every major distributions package manager.  Otherwise, please
refer to their respective install pages.

- [Vagrant Installation](https://www.vagrantup.com/docs/installation)
- [Ansible Installation](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

As a default hypervisor Vagrant uses *VirtualBox*, we however want to utilize
the native linux ``KVM`` through ``libvirt``. Vagrant  unfortunately doesn't support
it out-of-the box, but fortunately is the ``vagrant-libvirt`` plugin available.
Installing it can be as simple as:

```
> vagrant plugin install vagrant-libvirt
```

Note, that this is a third-party solution and the above step may not work
correctly in every environment. Please consult the [vagrant-libvirt
installation guide](https://github.com/vagrant-libvirt/vagrant-libvirt)

If you wish to use a different hypervisor you are free to do so. As you will
see switching switching a hypervisor in Vagrant is trivial.


## Architecture

We will setup a simple Spark cluster with one **master** (control) node and
several **worker** nodes all connected and managed by the master. All will be
connected on the same network.

We will assign IP addresses as follows

|   node  	    |        IP          	|
|:-------------:|:--------------------:	|
| master  	    | 192.168.50.10        	|
| worker-01 	| 192.168.50.11        	|
| worker-02 	| 192.168.50.12        	|
| ...     	    |                      	|
| worker-XX 	| 192.168.50.(10 + XX) 	|


For **cluster management** we will use the Spark in the simple **Standalone**
mode. To read more about cluster management options, please refer to the
[Spark Cluster Mode Overview](https://spark.apache.org/docs/latest/cluster-overview.html)


## Vagrant setup

We create a new directory named ``spark_example`` where we will store our
setup.

For our purposes, we will setup our virtual machines using ``vagrant``. We
will use the ``debian/buster64`` *box* (virtual machine image) provided by the
community. More boxes can be found on the [official Vagrant
site](https://app.vagrantup.com/boxes/search).

To create the initial configuration file we can simply run

```
> vagrant init debian/buster64
A `Vagrantfile` has been placed in this directory. You are now
ready to `vagrant up` your first virtual environment! Please read
the comments in the Vagrantfile as well as documentation on
`vagrantup.com` for more information on using Vagrant.
```

This will create a new file named ``Vagrantfile`` in the current working
directory. This file contains a lot of comments with tips and example
configurations.

Vagrant uses ``ruby`` for writing configuration files, but for
basic setups the knowledge of ruby is not required.

You can now run ``vagrant up`` and ``vagrant`` will download the requested box
for you and start up the VM. You can access the VM through SSH with the
``vagrant ssh`` command. If you are done using your machine, you can turn it
off with ``vagrant halt`` or save its state with ``vagrant suspend``.  If you
wish to permanently delete your machines it use ``vagrant destroy``.

``spark_example/Vagrantfile``

We will be starting with the following:
```ruby
# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'
BOX_IMAGE = 'debian/buster64'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box = BOX_IMAGE
end
```

As you can see, the amount of configuration required to setup a VM with Vagrant
is minimal.

### Multi-machine setup

Next, we will setup a multi-machine environment connected using a private
network. With Vagrant we are able to do that with only few lines of code.

Every time you plan to make a bigger change to your configuration be sure to
run ``vagrant destroy -f`` to delete your machines first. Sometimes vagrant can
start from a changed configuration with only ``vagrant reload``, but in the
early testing stages it is much easier to create your VMs from scratch.

We will create a multi-machine environment with the following configuration:

```ruby
# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

# How many slave nodes we want to create
WORKER_COUNT = 4

# Default box to use
BOX_IMAGE = 'debian/buster64'

# Default starting address
IP_START = 10

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Create the master node
  config.vm.define 'master', primary: true do |subconfig|
    subconfig.vm.box = BOX_IMAGE

    # Connect master to a private network
    subconfig.vm.network :private_network, ip: "192.168.50.#{IP_START}"

    # Set hostname for master
    subconfig.vm.hostname = 'master'
  end

  # Create the worker nodes
  (1..WORKER_COUNT).each do |machine_id|
    # Name of the node in format "worker-01", "worker-32", etc.
    box_name = "worker-" + machine_id.to_s.rjust(2, "0")

    # IP address of the worker
    box_ip_address = "192.168.50.#{machine_id + IP_START}"

    # Setup one slave node
    config.vm.define box_name do |subconfig|
      subconfig.vm.box = BOX_IMAGE

      # Connect a worker to a private network
      subconfig.vm.network :private_network, ip: box_ip_address

      # Set worker hostname
      subconfig.vm.hostname = box_name
    end
  end
end
```

Here, we did a number of things.

1. Because we wanted to extend the configuration the _master_ node, we defined
   a new node ``'master'`` and started a new configuration block:

    ```ruby
    # Create the master node
    config.vm.define 'master', primary: true do |subconfig|
        # ... rest of the configuration
    end
    ```

   Here we can use the ``subconfig`` variable and all the options will be tied
   only with the master node.

   Also note that we defined this node with ``primary: true``. We will get to that
   shortly.

2. We connected the node to a ``private_network`` and assigned it the
   ``192.168.50.10`` IP address with the line:

    ```ruby
    # Connect master to a private network
    subconfig.vm.network :private_network, ip: "192.168.50.#{IP_START}"
    ```

   We used to ruby _string interpolation_ syntax ``#{}``.

   We also assigned the node a unique hostname:
    ```ruby
    # Set hostname for master
    subconfig.vm.hostname = 'master'
    ```

3. Next, we added the worker nodes with the following loop

    ```ruby
    (1..WORKER_COUNT).each do |machine_id|
      # ... worker configuration
    end
    ```

   Note that the standard ruby for loop does not work. See [looping over VM definitions.](https://www.vagrantup.com/docs/vagrantfile/tips#loop-over-vm-definitions)

   The rest of the configuration is similar to the configuration of the master
   node.


You can now ``vagrant up`` to create your machines. Note that there is a small
change in some of vagrant commands in multi-machine setups. For example to
``vagrant ssh`` into a machine you have to explicitly specify the machine name
as defined in the vagrant configuration. So ``vagrant ssh worker-01`` would
connect you to the first node. However, you can define one of your machines to
be ``primary`` which will be the default option when running ``vagrant ssh``.
We did exactly that with the master node.

You should now be able to connect to the master node by running ``vagrant ssh``
(without additional arguments) and from there ``ping`` other VMs on the network.

```
vagrant > ping 192.168.50.11
PING 192.168.50.11 (192.168.50.11) 56(84) bytes of data.
64 bytes from 192.168.50.11: icmp_seq=1 ttl=64 time=0.406 ms
64 bytes from 192.168.50.11: icmp_seq=2 ttl=64 time=0.400 ms
64 bytes from 192.168.50.11: icmp_seq=3 ttl=64 time=0.453 ms
...
```

### Configuring the provider

We also want to tell vagrant about the system resources we want assign to our
machines. We will do that globally with the ``config.vm.provider`` option.

```ruby
# ... other variables
VAGRANTFILE_API_VERSION = '2'

# Parameters of the created VMs
VM_MEMORY = 6144
VM_CPUS = 8

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # ... VM configuration

  # Tell vagrant about system resources we want to use
  config.vm.provider :libvirt do |libvirt|
    # Customize the amount of memory on the VM:
    libvirt.memory = VM_MEMORY

    # Customize the number of cpus on the VM:
    libvirt.cpus = VM_CPUS
  end

end
```

Here we specified that we wish to use the ``libvirt`` provider and assigned the
desired amount of memory and CPUs.

### Disabling default NFS sharing

By default vagrant also mounts the current working directory as NFS drive to
the VM. We disabled this behaviour by adding this line at the end of the
configuration.

```ruby
# Disable mounting the default vagrant folder
config.vm.synced_folder '.', '/vagrant', disabled: true
```

### Provisioning

For provisioning we will be using [Ansible](https://www.ansible.com/). Ansible
configuration is done via configuration files written in YAML called
**playbooks**. Playbooks contain a list of so-called **plays** which are
essentially groups of tasks you want to execute. Tasks are are composed of
*modules* which are usually the most atomic parts of your playbooks.

A simple playbook might look something like this:

```yaml
--- # Three dashes signify YAML file, Ansible doesn't care if you forget them though
- name: My first play.
  hosts: all
  tasks:
    - name: "My first task!"
      debug: "msg=Hello from VM - {{ inventory_hostname }}"

- name: My second play!
  hosts: all
  become: True  # get superuser privilages
  tasks:
    - name: Notify user about what I want to do
      debug:
        msg: I'm going to install packages

    # ... tasks for installing a package

    # The `name` field is optional (but improves readability).
    - debug: msg="packages are installed."
```


We will get to the structure of an ansible-playbook shortly. For now you can go
ahead and add the contents of this file to ``setup-spark.yml``. We will use it
as a base for provisioning.

We will modify the ``Vagrantfile`` by adding the following lines to the
configuration.

```ruby
# ... other variables

# Playbook to run for provisioning
PLAYBOOK = 'setup-spark.yml'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # ... rest of the configuration

  config.vm.provision :ansible do |ansible|
    # Disable default limit to connect to all the machines
    ansible.playbook = PLAYBOOK
  end
end
```

You can now create your VMs, Vagrant you will see Vagrant run ``ansible`` and
provision them for you. You will also notice that the VMs are being provisioned
one after another (you can check that by running ``vagrant provision``).  This
is actually something we *don't* want because ansible is capable (and expected)
to run the individual plays in parallel.

To our knowledge there isn't currently a "clean" way configure Vagrant to run
the provisioning only after booting all the machines. There is however, a small
"hack" that can achieve this. You run the provisioning from the last created
machine only and turn off the default limit for provisioning (which is current
machine only). This also [endorsed by Vagrant
documentation](https://www.vagrantup.com/docs/provisioning/ansible#ansible-parallel-execution).

We modify the ``Vagrantfile`` followingly:
```ruby
(1..WORKER_COUNT).each do |machine_id|
  # ... worker variables

  # Setup one slave node
  config.vm.define box_name do |subconfig|

    # Run ansible provisioning in parallel by running the provisiong from the
    # last created node only
    if machine_id == WORKER_COUNT
      subconfig.vm.provision :ansible do |ansible|
        # Disable default limit to connect to all the machines
        ansible.limit = 'all'
        ansible.playbook = PLAYBOOK
      end
    end
  end
end
```

If you run ``vagrant provision`` now, you should see all the machines
provisioned in parallel.

There is now only a few last things we need to add to our Vagrant
configuration.

Firstly, we want to create a group within ansible and assign all the workers
to it. This will allow us to configure all the workers simultaneously.

We can do that by adding the following lines into the provisioning section:
```ruby
ansible.groups = {
  'workers' => (1..WORKER_COUNT).map { |i| 'worker-' + id_number.to_s.rjust(2, '0') }
}
```

Finally, we want to notify ansible about the IP address it should use for
configuration. This is needed in case the VMs have multiple network interfaces.
We will use this variable ourselves when configuring ansible later.  We can
achieve this by defining the ``ansible.host_vars`` field in configuration ans
supplying it a _hash_ (ruby dictionary) with key-value pairs of hostname and
value we want to set. The value is another hash containing the values we want
to supply ansible.

We start by defining a new hash called ``spark_ip_addresses`` and filling it
with the IP addresses for individual nodes like this:

```ruby
# Define hash for master node
spark_ip_addresses = {
  'master' => {
    'spark_ip_address' => '192.168.50.10'
  }
}

# ... add new entry
spark_ip_addresses[box_name] = {
  'spark_ip_address' => box_ip_address
}
```

In the provisioning section we then provide the hash to the ``ansible.host_vars``:
```ruby
ansible.host_vars = spark_ip_addresses
```
### Final Vagrantfile

The final ``Vagrantfile`` (with some minor improvements) looks like this:

```ruby
# frozen_string_literal: true

# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

# How many slave nodes we want to create
WORKER_COUNT = 4

# System resources for nodes
VM_MEMORY = 6144
VM_CPUS = 8

# Default starting host address
IP_START = 10

# Default box to use
BOX_IMAGE = 'debian/buster64'

# Playbook to run for provisioning
PLAYBOOK = 'setup-spark.yml'

# Generate a name for the worker based on its ID number
def worker_name(id_number)
  # Name of the node in format "worker-01", "worker-32", etc.
  'worker-' + id_number.to_s.rjust(2, '0')
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Create the master node
  config.vm.define 'master', primary: true do |subconfig|
    subconfig.vm.box = BOX_IMAGE

    # Connect master to a private network
    subconfig.vm.network :private_network, ip: "192.168.50.#{IP_START}"

    # Set hostname for master
    subconfig.vm.hostname = 'master'
  end

  spark_ip_addresses = {
    'master' => {
      'spark_ip_address' => "192.168.50.#{IP_START}"
    }
  }

  # Create the worker nodes
  (1..WORKER_COUNT).each do |machine_id|
    box_name = worker_name(machine_id)

    # IP address of the worker
    box_ip_address = "192.168.50.#{machine_id + IP_START}"

    # Setup one slave node
    config.vm.define box_name do |subconfig|
      subconfig.vm.box = BOX_IMAGE

      # Connect a worker to a private network
      subconfig.vm.network :private_network, ip: box_ip_address

      # Set worker hostname
      subconfig.vm.hostname = box_name

      spark_ip_addresses[box_name] = {
        'spark_ip_address' => box_ip_address
      }

      # Run ansible provisioning in parallel by running the provisiong from the
      # last created node only
      if machine_id == WORKER_COUNT
        subconfig.vm.provision :ansible do |ansible|
          # Disable default limit to connect to all the machines
          ansible.limit = 'all'
          ansible.playbook = PLAYBOOK

          ansible.host_vars = spark_ip_addresses

          ansible.groups = {
            'workers' => (1..WORKER_COUNT).map { |i| worker_name(i) }
          }
        end
      end
    end
  end

  # Tell vagrant about system resources we want to use
  config.vm.provider :libvirt do |libvirt|
    # Customize the amount of memory on the VM:
    libvirt.memory = VM_MEMORY

    # Customize the number of cpus on the VM:
    libvirt.cpus = VM_CPUS
  end

  # Disable mounting the default vagrant folder
  config.vm.synced_folder '.', '/vagrant', disabled: true
end
```

## Ansible setup

### Setting up an inventory

Firstly, we need to inform Ansible about the machines we wish to provision.
This is done through what Ansible calls an **inventory**. In an inventory you
specify the **hosts** Ansible should configure. Additionally, Ansible can group
hosts into **groups**, so you can run related task for multiple nodes at once,
which simplifies the configuration even further. The default inventory can be
found in ``/etc/ansible/hosts``.

We will be able to skip writing an inventory file entirely, because Vagrant is
able to auto-generate the inventory file for us. After running ``vagrant up``
with provisioning using Ansible set up, you can find the auto-generated file in
``.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory`` in the
root of your project directory.

Within, you should be able to see the hosts we defined in Vagrant with
information how to connect as well as the ``spark_ip_address`` variable for
each host.  There should also be defined the ``workers`` group starting with
``[workers]`` and listing all the worker hostnames.

To test that the inventory file is working correctly we can run a one-off
module using the ``ansible`` command. We will tell each machine to print its
inventory hostname.

```
> ansible all \
    -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    -m debug -a var=inventory_hostname
```

Here we tell vagrant to run the ``debug`` module printing the
``inventory_hostname`` variable for ``all`` hosts (``all`` is a automatically
created group containing all hosts in the inventory) from the specified
inventory file. More on modules in a minute.

If you wish to know more about crating inventories, please refer to [How to
build an inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html)

### Setting up ``ansible.cfg``

By default ansible will look for inventory in ``/etc/ansible/hosts`` first.
To change this behaviour and make our lives easier we will configure ansible
to use the Vagrant generated inventory.

Create a file name ``ansible.cfg`` in the root of your project and fill it
with:

```cfg
[defaults]
inventory = .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory
host_key_checking = false
```
You can now run the command in previous section as:
```
> ansible all -m debug -a var=inventory_hostname
```

If you wish to know more about configuring ansible, please refer to [Ansible
Configuration Settings](https://docs.ansible.com/ansible/latest/reference_appendices/config.html)


### Exploring basic playbook structure

Configuration in ansible is done through YAML configuration files. We will explore
the YAML syntax largely as we go. However if you wish to know more, please refer to the
[YAML syntax](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html)

Let's dissect the example playbook from Vagrant configuration.
```yaml
--- # Three dashes signify YAML file, Ansible doesn't care if you forget them though
- name: My first play.
  hosts: all
  tasks:
    - name: "My first task!"
      debug: "msg=Hello from VM - {{ inventory_hostname }}"

- name: My second play!
  hosts: all
  become: True  # get superuser privilages
  tasks:
    - name: Notify user about what I want to do
      debug:
        msg: I'm going to install packages

    # ... tasks for installing a package

    # The `name` field is optional (but improves readability).
    - debug: msg="packages are installed."
```

Here we can see a **playbook** with two **plays** defined:
 - My first play
 - My second play!

The ``hosts`` option specifies on which hosts we want to run the play. Here we
specify the ``all`` group.

The core of a play is the ``tasks`` section. In the ``tasks`` section we
specify a list of tasks we want to execute. Tasks are realized through
**modules**.  Here we used the ``debug`` module. Modules can take **options**.
We can see the ``msg`` option in use here. There are two ways to supply
arguments as seen in the example. It doesn't matter which way you choose, just
try to be consistent.

The ``become`` option allows us to elevate the play to superuser privileges.

If you want to list the options of a module, you can use the ``ansible-doc`` command
provided with Ansible:
```
> ansible-doc debug
```

To run a playbook, use the ``ansible-playbook`` command. For example:
```
> ansible-playbook setup-spark.yml
```

### Installing packages with ansible

Let's start with a clean ``setup-spark.yml`` file.

To install a package we will use the ``apt`` module. For different
distributions there are also modules like ``dfn`` or ``yum`` and partly
distribution agnostic ``package`` module (but you still have to account for
different package names between distributions).

We will install the ``ntp`` daemon for time synchronization.

We add the following to ``spark-setup.yml``.
```yaml
---
- name: Setup common
  hosts: all
  tasks:
  - name: Install the NTP daemon.
    become: True
    apt:
      name: ntp
```

Here we can see we can get superuser privileges for a single task only.

After running ``ansible-playbook setup-spark.yml`` you should see ansible
install the ``ntp`` to all hosts.


### Enabling a service

To enable a service we use the ``service`` module.

To enable and start  the ``ntp`` service add the following task to the play:
```yaml
- name: Start ntp service
  service: name=ntp state=started enabled=yes
```

Note that we could have alternatively used the YAML syntax:

```yaml
- name: Start ntp service
  service:
    name: ntp
    state: started
    enabled: yes
```

### Installing Apache Spark

Apache Spark is unfortunately not available through the official repositories
so we will have to install it manually.

We will assume that ansible has configured one host called ``master`` and a
group of hosts called ``workers``.

Firstly, we need to install some dependencies, namely Java. We also ensure,
that we have ``python3`` installed. We define a new play with this task:

```yaml
- name: Install spark
  hosts: all
  become: True
  tasks:
  - name: Installing dependencies
    apt:
      name: [ "default-jdk", "python3" ]
      update_cache: True
```

The ``update_cache`` option tells ``apt`` to update the local
repository cache.

Next, we define a new group and user under which we install the package. We
will want to run spark as a service later. For this task, Ansible provides two
modules ``group`` and ``user``. Creating them is them as straightforward as
adding the following tasks:
```yaml
- name: Create spark group
  group:
    name: spark
    state: present

- name: Create spark non-system user
  user:
    name: spark
    group: spark
    shell: /usr/sbin/nologin
```

Next, we are going to download the Apache Spark binary. They can be found here:
[https://downloads.apache.org/spark/](https://downloads.apache.org/spark/). We will
be installing ``spark-3.0.2`` with ``hadoop3.2``.

The full link to the corresponding tarball then looks like this:
```
https://downloads.apache.org/spark/spark-3.0.2/spark-3.0.2-bin-hadoop3.2.tgz
```

To make the playbook more general we will separate information into
**variables**. Ansible allows us to declare variables quite a few places ( a bit [too
many](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#understanding-variable-precedence)
for my taste). 

We've already defined some variables (*host variables* in ansible speak) when
we configured Vagrant provisioning (``spark_ip_address``). They live in the inventory.

On a play level we can declare them using the ``vars``
option. For the sake of brevity we declared the following variables (which we will use
[later](https://i.kym-cdn.com/photos/images/original/001/264/842/220.png))

 - **spark_mirror**: Mirror from which to download Spark (i.e ``https://downloads.apache.org/spark``)
 - **spark_version**: The version of Spark we wish to use (i.e. ``"3.0.2"``)
 - **hadoop_version**: Version of hadoop. (i.e ``"hadoop3.2"``)
 
 - **spark_parent_dir**: Location where we wish to put Spark ( i.e. "/usr/local" )
 - **spark_link_dir**: Directory where will the Spark reside ( i.e. "/usr/local/spark" )

And some variables for convenience:
 - **spark_name**: Just version with appended ``spark-`` prefix (``"spark-3.0.2"``)
 - **spark_fullname**: Full name of the Spark package. (``"{{ spark_name }}-bin-{{ hadoop_version }}"``)
 - **spark_target_dir**: Location where we wish to put a specific installation
    of Spark ( i.e. "/usr/local/spark-3.0.2-bin-hadoop3.2" )
 - **spark_tarball**: Name of the downloaded tarball. (``"{{ spark_fullname }}.tgz"``)
 - **spark_tarball_url**: Full link to the package (``"{{ spark_mirror }}/{{ spark_name }}/{{ spark_tarball }}"``)

The playbook with the variables defined will then look like this:
```yaml
---
- name: Install Apache Spark
  hosts: all
  becme: True
  vars:
    - spark_mirror: "https://downloads.apache.org/spark"
    - spark_version: "3.0.2"
    - hadoop_version: "hadoop3.2"

    - spark_parent_dir: "/usr/local"
    - spark_link_dir: "/usr/local/spark"

    - spark_name: "spark-{{ spark_version }}"
    - spark_fullname: "{{ spark_name }}-bin-{{ hadoop_version }}"
    - spark_target_dir: "{{ spark_parent_dir }}/{{ spark_fullname }}"
    - spark_tarball: "{{ spark_fullname }}.tgz"
    - spark_tarball_url: "{{ spark_mirror }}/{{ spark_name }}/{{ spark_tarball }}"
  tasks:
    # ... tasks
```

To download the file, Ansible provides a *module* called ``get_url``.  We
add the following task:

```yaml
- name: Downloading Apache Spark sources
  get_url:
    url: "{{ spark_tarball_url }}"
    dest: "/tmp/{{ spark_tarball }}"
    owner: spark
    group: spark
    mode: 0644
```

Again ``url``, ``dest``, ``owner``, ``group`` and ``mode`` are relevant options
of the module (``ansible-doc get-url``).

Next, we unpack the archive. We use the ``unarchive`` module.
```yaml
- name: Unpacking tarball
  unarchive:
    remote_src: yes
    dest: "{{ spark_parent_dir }}"
    src: "/tmp/{{ spark_tarball }}"
    owner: spark
    group: spark
    creates: "{{ spark_target_dir }}"
```

Here we see two notable options. The ``remote_src`` informs ansible that the
source file is located at the *remote* machine.  Without this option it would
try to find the archive on your local host (the machine from which you
are running ansible).

The ``creates`` option informs ansible about the state of the environment after
the task is done. Next time the task is run and the tarball is already
unpacked, the task will simply be skipped.  Used here, it's actually useless,
because the ``unarchive`` module is smart enough to infer this without the
option.  However it can be very useful if you, for example create a file
manually through the ``shell`` or ``command`` module.

Next, we link the module to the desired destination. Note that we could have
just renamed the directory, but linking makes it easier when we (potentially)
want to manage multiple versions.

```yaml
- name: Link spark directory
  file:
    src: "{{ spark_parent_dir }}/{{ spark_fullname }}"
    dest: "{{ spark_link_dir }}"
    state: link
```

Next we have to setup the Spark environment. We want to do two things:
 - Add Spark installation to PATH
 - Setup environment variables for Spark

To add Spark to PATH, we will simply add a new script to ``/etc/profile.d``.
These scripts are executed by the shell on startup. To generate the new file
we will use a **template**. Ansible supports the Jinja2 templating engine.

We create a new directory ``templates/`` and add a new file ``spark.sh.j2``
where we export the variables the usual way:
```jinja2
export SPARK_HOME={{ spark_link_dir }}
export PATH="$PATH:{{ spark_target_dir }}/bin:{{ spark_target_dir }}/sbin"
```

We add the following task to the playbook:
```yaml
- name: Add spark to environment
  template:
    src: "spark.sh.j2"
    dest: "/etc/profile.d/spark.sh"
    owner: root
    group: root
    mode: 0644
```
Ansible will automatically substitute the variables using the variables defined
in the playbook.

To configure spark environment, we will want to define the following
environmental variables:

 - ``SPARK_MASTER_HOST`` - IP address of the master
 - ``SPARK_MASTER_PORT`` - port on which to connect to master
 - ``SPARK_LOCAL_IP`` - IP address on which to start the local Spark process
 - ``SPARK_HOME`` - home of the current spark installation
 - ``PYSPARK_PYTHON`` - python interpreter to use for PySpark

We will group these into a YAML dictionary, which we put into the ``vars``
section.
```yaml
vars:
    # ... other variables
  - spark_master_ip: "{{ hostvars['master'].spark_ip_address }}"
  - spark_master_port: 7077
    
  - spark_local_ip: "{{ hostvars[inventory_hostname].spark_ip_address }}"
  - spark_worker_port: 7078
    
  - spark_env_vars:
      SPARK_MASTER_HOST: "{{ spark_master_ip }}"
      SPARK_MASTER_PORT: "{{ spark_master_port }}"
      SPARK_LOCAL_IP: "{{ spark_local_ip }}"
      SPARK_HOME: "{{ spark_link_dir }}"
      PYSPARK_PYTHON: "/usr/bin/python3"
```

We also defined ``spark_worker_port`` which we will use later.

Now we create a template to populate the ``spark-env.sh`` file found in
``conf/`` directory of the Spark installation.
```jinja2
{% if spark_env_vars is defined %}{% for key, value in spark_env_vars.items() %}
export {{key}}={{value}}
{% endfor %}{% endif %}
```

Here, we use Jinja in a bit more advanced way, but the result should still be
evident.

We add the following task:
```yaml
- name: Configure spark environment
  template:
    src: "spark-env.sh.j2"
    dest: "{{ spark_target_dir }}/conf/spark-env.sh"
    owner: spark
    group: spark
    mode: 0755
```

Finally, we cleanup the downloaded files:
```yaml
- name: Cleanup
  file:
    path: "/tmp/{{ spark_tarball }}"
    state: absent
```

### Adding systemd units

We won't be covering how to define systemd units. If you wish to know more
[Understanding Systemd Units and Unit
Files](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files)
might be a good start.

We define the following templates:

``spark-master.service.j2``
```cfg
[Unit]
Description=Spark Master Service
Wants=network.target network-online.target
After=network.target network-online.target

[Service]
Type=forking
User=spark
WorkingDirectory={{ spark_link_dir }}
ExecStart={{ spark_link_dir }}/sbin/start-master.sh 
ExecStop={{ spark_link_dir }}/sbin/stop-master.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

``spark-worker.service.j2``
```cfg
[Unit]
Description=Spark Worker Service
Wants=network.target network-online.target
After=network.target network-online.target

[Service]
Type=forking
User=spark
WorkingDirectory={{ spark_link_dir }}
ExecStart={{ spark_link_dir }}/sbin/start-slave.sh "spark://{{ spark_master_ip }}:{{ spark_master_port }}" --port {{ spark_worker_port }}
ExecStop={{ spark_link_dir }}/sbin/stop-slave.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

However, we will want to copy these files to the machines only if ``systemd``
is present in the system. That requires some form of flow control. We will use
the Ansible ``when`` clause.

First, we have to capture the output of a module. In Ansible this is called
*registering* a variable and can be done like this:
```yaml
- name: Check if systemd exists
  stat: path=/lib/systemd/system/
  register: systemd_check
```

Here we use the ``stat`` module to check the ``/lib/systemd/system`` path and
register the output as a new variable ``systemd_check`` . The contents of this
variable are dependent on the module used, so we recommend to use the ``debug``
module to check its contents.

We will introduce one more Ansible construct and that is ``block``. It groups
multiple tasks together so different options can be applied to them together.

The new tasks together then look like this:
```yaml
- name: Check if systemd exists
  stat: path=/lib/systemd/system/
  register: systemd_check

- block:
  - name: Create master systemd start script
    template:
      src: "spark-master.service.j2"
      dest: "/etc/systemd/system/spark-master.service"
      owner: root
      group: root
      mode: 0644

  - name: Create worker systemd start script
    template:
      src: "spark-worker.service.j2"
      dest: "/etc/systemd/system/spark-worker.service"
      owner: root
      group: root
      mode: 0644

  when: systemd_check.stat.exists == True
  become: True
```

### Creating roles

We will look at two ways of simplifying playbooks, namely **roles** and
including other YAML files using **include**.

Roles are usually defined in a ``roles/`` directory and follow a specific
directory structure.

To simplify our playbook, we might want to define two roles:
    - ``common``: role that setups common environment on all host
    - ``spark``: role that installs Spark

We therefore create the following directory structure:
```
 roles
 ├── common
 │   └── tasks
 └── spark
     ├── defaults
     ├── tasks
     ├── templates
     └── vars
```

The individual directories correspond to different parts of playbooks. For
complete overview please refer to [Role directory
structure](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html#role-directory-structure)

Basic overview of the directories:
 - ``defaults``: Contains default variables or variables we expect will be overwritten
 - ``vars``: variables we use within the role
 - ``tasks``: tasks of the role
 - ``templates``: template files

We distribute the configuration from the main playbook into to roles in the
following way:

``roles/common/tasks/main.yml``:
```yaml
---
- block:
  - name: Install the NTP daemon.
    apt:
      name: ntp

  - name: Start ntp service
    service: name=ntp state=started enabled=yes

  become: True
```

``roles/spark/defaults/main.yml``:
```yaml
---
spark_mirror: "https://downloads.apache.org/spark"
spark_version: "3.0.2"
hadoop_version: "hadoop3.2"

spark_parent_dir: "/usr/local"
spark_link_dir: "/usr/local/spark"

# Custom master configuration
spark_master_ip: "{{ hostvars['master'].ansible_default_ipv4.address
                   | default(hostvars['master'].ansible_all_ipv4_addresses[0]) }}"
spark_master_port: 7077

# IP address Spark binds to on this node
spark_local_ip: "{{ ansible_default_ipv4.address
                  | default(ansible_all_ipv4_addresses[0]) }}"
spark_worker_port: 7078

# Custom spark runtime configuration options
spark_extra_vars: {}

spark_default_vars:
  SPARK_MASTER_HOST: "{{ spark_master_ip }}"
  SPARK_MASTER_PORT: "{{ spark_master_port }}"
  SPARK_LOCAL_IP: "{{ spark_local_ip }}"
  SPARK_HOME: "{{ spark_link_dir }}"

  # Python binary executable to use for PySpark in both driver and workers
  # (default is python2.7 if available, otherwise python). Property
  # spark.pyspark.python take precedence if it is set
  PYSPARK_PYTHON: "/usr/bin/python3"
```

``roles/spark/vars/main.yml``:
```yaml
---
spark_env_vars: "{{ spark_extra_vars | default({}) | combine(spark_default_vars) }}"

spark_name: "spark-{{ spark_version }}"
spark_fullname: "{{ spark_name }}-bin-{{ hadoop_version }}"
spark_tarball: "{{ spark_fullname }}.tgz"
spark_tarball_url: "{{ spark_mirror }}/{{ spark_name }}/{{ spark_tarball }}"
spark_target_dir: "{{ spark_parent_dir }}/{{ spark_fullname }}"
```

``roles/spark/tasks/systemd.yml``:
```yaml
---
- name: Check if systemd exists
  stat: path=/lib/systemd/system/
  register: systemd_check

- block:
  - name: Create master systemd start script
    template:
      src: "spark-master.service.j2"
      dest: "/etc/systemd/system/spark-master.service"
      owner: root
      group: root
      mode: 0644

  - name: Create worker systemd start script
    template:
      src: "spark-worker.service.j2"
      dest: "/etc/systemd/system/spark-worker.service"
      owner: root
      group: root
      mode: 0644

  when: systemd_check.stat.exists == True
  become: True
```

``roles/spark/tasks/main.yml``:
```yaml
- name: Check for existing ansible installation
  stat:
    path: '{{ spark_target_dir }}'
  register: spark_installation
  tags:
    - spark

- name: Download, install and setup Spark environment
  when: not spark_installation.stat.exists
  block:
  - name: Installing dependencies
    apt:
      name: [ "default-jdk", "python3" ]

  - name: Create spark group
    group:
      name: spark
      state: present

  - name: Create spark non-system user
    user:
      name: spark
      group: spark
      shell: /usr/sbin/nologin

  - name: Downloading Apache Spark sources
    get_url:
      url: "{{ spark_tarball_url }}"
      dest: "/tmp/{{ spark_tarball }}"
      owner: spark
      group: spark
      mode: 0644

  - name: Unpacking tarball
    unarchive:
      remote_src: yes
      dest: "{{ spark_parent_dir }}"
      src: "/tmp/{{ spark_tarball }}"
      owner: spark
      group: spark
      creates: "{{ spark_target_dir }}"

  - name: Add spark to environment
    template:
      src: "spark.sh.j2"
      dest: "/etc/profile.d/spark.sh"
      owner: root
      group: root
      mode: 0644

  - name: Configure spark environment
    template:
      src: "spark-env.sh.j2"
      dest: "{{ spark_target_dir }}/conf/spark-env.sh"
      owner: spark
      group: spark
      mode: 0755
  become: True

- name: Link spark directory
  become: True
  file:
    src: "{{ spark_parent_dir }}/{{ spark_fullname }}"
    dest: "{{ spark_link_dir }}"
    state: link

- name: Cleanup
  become: True
  file:
    path: "/tmp/{{ spark_tarball }}"
    state: absent


- name: Include systemd services
  include: systemd.yml
```

The final directory structure looks like this:
```
 roles
 ├── common
 │   └── tasks
 │       └── main.yml
 └── spark
     ├── defaults
     │   └── main.yml
     ├── tasks
     │   ├── main.yml
     │   └── systemd.yml
     ├── templates
     │   ├── spark-env.sh.j2
     │   ├── spark-master.service.j2
     │   ├── spark.sh.j2
     │   └── spark-worker.service.j2
     └── vars
         └── main.yml
```

A few notable changes happened:
1. default values for ``spark_master_ip`` and ``spark_local_ip`` have been
   defined using the Jinja ``default`` filter.
2. definition of spark environmental variables has been moved into
   ``spark_default_vars``, a new dictionary``spark_extra_vars`` has been
   defined and they are combined into the ``spark_env_vars`` using the Jinja
   ``combine`` filter
3. the tasks for systemd are defined in its own file ``systemd.yml`` and
   included from ``main.yml``
4. the spark installation now proceeds only when it detects that Spark is not
   installed

Finally, we edit the ``setup-spark.yml``:
```yaml
- name: Install spark
  hosts: all
  roles:
    - common
    - role: spark
      vars:
        spark_local_ip: "{{ hostvars[inventory_hostname].spark_ip_address }}"
        spark_master_ip: "{{ hostvars['master'].spark_ip_address }}"
  tasks:
    - name: Add vagrant to spark group
      become: True
      user:
        name: vagrant
        groups: spark
        append: yes

- name: Start master node
  hosts: master
  tasks:
    - name: Start master service
      become: True
      service:
        name: spark-master
        state: started
        enabled: yes

    - name: Copy example files to master
      become: True
      copy:
        src: example/
        dest: /example
        owner: spark
        group: spark
        mode: 0755

- name: Start worker nodes
  hosts: all
  tasks:
    - name: Start worker service
      become: True
      service:
        name: spark-worker
        state: started
```


## Some notes to Apache Spark ML
### Download the data

**Do not forget to distribute the files to the workers!**

Boston Housing dataset:

`wget https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv`

Mnist train and test:

`wget https://pjreddie.com/media/files/mnist_train.csv`
`wget https://pjreddie.com/media/files/mnist_test.csv`

I have also created a script for downloading the data in `pyspark/download_data.sh`:
```bash
#!/usr/bin/env bash

wget https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv
wget https://pjreddie.com/media/files/mnist_train.csv
wget https://pjreddie.com/media/files/mnist_test.csv
```

## Spark Shell

Find the directory where Spark is installed using `echo $SPARK_HOME`.
In this directory run `./bin/pyspark` to enter the Python Spark Shell. This connects
you to the cluster automatically by creating SparkSession (more on that later).

Spark Shell is interactive so you can try whatever you want. It's good for learning
how Spark ML works.

## SparkSession
This is an entry point to the cluster. Every program you want to run on the cluster
needs object of this type. Spark Shell creates it without you even noticing.

You can create SparkSession by:
```python
spark = SparkSession.builder.master("spark://192.168.50.10:7077").appName("Linear regression with pipeline - Boston").getOrCreate()
```
where `spark://192.168.50.10:7077` is the address of the master node, then you choose a name for
the app and create the SparkSession (or get one earlier created). Note that in older versions there was SparkContext, however
the SparkSession replaced it and therefore SparkContext is no longer used. 

## How to store data?

There are multiple objects that can store data:
1. RDD - Resilient Distributed Dataset
2. DataFrame
3. DataSet

We will talk only about RDD and DataFrames since only these two types we use in our project.

### RDD
RDD is the oldest object that represents data. It is
 - immutable - when the object is created it cannot be modified (modification returns a new RDD)
 - fault tolerant - when something goes wrong the app doesn't crash
 - distributed - RDD is divided into logic partitions and distributed between cluster worker nodes and therefore the parallelization is possible
 - lazy evaluated - RDDs are lazy evaluated meaning actions and transformations are evaluated only when necessary. Imagine
a person who is really lazy but does everything (you can rely on him). He just postpones all work
and when you start to yell that you really need it, he finally does it.

We can perform **transformations** and **actions** on RDD:
 - transformations return a new RDD (since it is immutable). Possible transformations are `.map()`, `.filter()`, `.randomSplit()`, ...
 - actions return non-RDD object (for example just an int number) - `.first()`, `.count()`, ...

You can create a RDD from existing collections (lists for example) or from files on the disk.

### DataFrames

This is the newer object representing data that we will use in our applications.

If you have experience with Pandas DataFames, this is virtually the same. You can think about Spark ML DataFrames
as Pandas DataFrames. Spark DataFrames have only some optimizations under the hood.

DataFrame is just a 2D array with labelled columns. It is also:
 - immutable
 - fault tolerant
 - distributed
 - lazy evaluated

You can create one from RDD, existing collections (like lists) or from files on the disk (.csv, .txt, .xml, HDFS, S3, HBase, ...).
We create DataFrame in `lr_pipeline.py` from a `.csv` file like this:

`data = spark.read.format("csv").option('header', 'true').option('inferSchema', 'true').load(filename)`

In our video there is explained what all the commands mean.

You can also create DataFrame from a list like this:
```python
our_list = [('Martin', 180), ('David', 182), ('Dennis', 190), ('Tobias', 183)]

columns = ["name", "height"]
our_DataFrame = spark.CreateDataFrame(data=our_list, schema=columns)
```

#### Simple operations on DataFrames I didn't have time to show on video

 - `df.show(10)` ... shows header and first 10 lines of the DataFrame
 - `df.printSchema()` ... prints schema - the header with column type
 - `df.select("col_name").show()` ... shows only col_name column
 - `df.filter(df["col_name"] > 10).show()` .. filters only rows which have a value > 10 in column col_name

And other very useful commands:
`train, test = df.randomSplit([0.8, 0.2])` ... splits the DataFrame to train and test sets
`train.schema.names` ... returns list of names of the columns

## VectorAssembler
Transformer that creates a new column by connecting more columns together to a list. We use it in `lr_pipeline.py`:

```python
v_assembler = VectorAssembler(inputCols=features_list, outputCol='features')
new_dataframe = v_assembler.transform(old_dataframe)
```

## Pipeline

This is a concept from ML that makes the whole workflow of data easier. You put data into pipeline
and the pipeline transforms it to the output. In pipeline there can be many stages - many transformers
and estimators. In file `lr_pipeline.py` we demonstrate a very simple pipeline with just one
transformer (polynomial expansion) and one estimator (linear regression):

```python
poly_exp = PolynomialExpansion(degree=3, inputCol="features", outputCol="poly_features")
lr = LinearRegression(regParam=0.1, featuresCol="poly_features")

pipeline = Pipeline(stages=[poly_exp, lr])
```

Te pipeline then behaves like a simple estimator - you put data to input and on that
data you fit a model:

```python
model = pipeline.fit(train)
```

A model is a transformer. It transforms input data into predictions:
```python
prediction = model.transform(train).select("prediction")
```

To evaluate our model we can use Evaluators - for linear regression:
```python
evaluator = RegressionEvaluator()

prediction_and_labels = model.transform(train).select("prediction", "label")
print("Precision train: " + str(evaluator.evaluate(prediction_and_labels)))

prediction_and_labels = model.transform(test).select("prediction", "label")
print("Precision test: " + str(evaluator.evaluate(prediction_and_labels)))
```

The whole file `lr_pipeline.py` with a `prepare_data()` function that prepares data for the model looks like this:

```python
from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import PolynomialExpansion
from pyspark.sql import SparkSession

def prepare_data(filename):
    """ 
    Transform data for ML learning algorithm

    Input: Data to be transformed (DataFrame)
    Returns: Transformed data (DataFrame)
    """

    data = spark.read.format("csv").option('header', 'true').option('inferSchema', 'true').load(filename)

    data = data.withColumnRenamed('medv', 'label')
    # get columns that represent features
    features_list = data.columns
    # pop last column since it is our target
    features_list.remove('label')

    # make a new column with a vector of features
    v_assembler = VectorAssembler(inputCols=features_list, outputCol='features')

    return v_assembler.transform(data)

if __name__ == "__main__":
    train_ratio = 0.8
    test_ratio = 1 - train_ratio

    # create SparkSession - the entry to the cluster
    spark = SparkSession.builder.master("spark://192.168.50.10:7077").appName("Linear regression with pipeline - Boston").getOrCreate()

    data = prepare_data("BostonHousing.csv")

    # split data into train and test DataFrames
    train, test = data.randomSplit([train_ratio, test_ratio])

    poly_exp = PolynomialExpansion(degree=3, inputCol="features", outputCol="poly_features")

    lr = LinearRegression(regParam=0.1, featuresCol="poly_features")

    pipeline = Pipeline(stages=[poly_exp, lr])
    # fit the model
    model = pipeline.fit(train)

    evaluator = RegressionEvaluator()

    prediction_and_labels = model.transform(train).select("prediction", "label")
    print("Precision train: " + str(evaluator.evaluate(prediction_and_labels)))

    prediction_and_labels = model.transform(test).select("prediction", "label")
    print("Precision test: " + str(evaluator.evaluate(prediction_and_labels)))
```

## Running the application on the cluster

To run the application on the cluster we use `bin/spark-submit` script in `$SPARK_HOME` directory.

**Note**: every node needs access to the files used in our models. We use Boston Housing and MNIST datasets.
I have created a script to download all data. This script has to be run in all worker nodes.

To run the application on our cluster, run:
`/usr/local/spark/bin/spark-submit --master "spark://192.168.50.10:7077" linear_regression.py 2> logfile`

We redirected logs to logfile. If you want to see what Spark is doing, erase `2> logfile`.

**Note**: As you can see in logfile, Spark does many things. It has to initialize the whole cluster,
create server where you can watch your jobs (on localhost on port 4040) and many others.
Therefore the overhead for our application is large. When we use as little amount of data
as in the BostonHousing dataset, the size of the overhead causes the application to run for a
longer time than in regular Python. Therefore Spark ML is not suitable for really tiny apps as
it takes longer to run them due to the overhead. But Spark ML is excellent when we have large
models and large amount of data - the overhead is tiny compared to the model and parallelization is
really beneficial.

## Multilayer Perceptron

## Grid Search

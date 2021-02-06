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

We will proceed with creating out playbook by showing how to install Spark on
one host manually and simultaneously translating tasks into Ansible for automatic
provisioning.

Firstly, we need create our playbook ``spark_example/spark.yml`` (be sure to
point your vagrant configuration to this file). Let's start with simple
playbook to ensure things are working as expected. We will create one play
to run on *all* hosts, and from every host print a debug message.

```yaml
---
- name: Install Apache Spark
  hosts: all
  tasks:
    - name: Test
      debug:
        msg: "Hello from {{ inventory_hostname }}"
```

This example also shows a simple case of *variable expansion*,
``inventory_hostname`` is a variable provided by ansible which will be expanded
into the appropriate hostname as specified in the inventory file.

Output should look something similar to this:
```
PLAY [Install Apache Spark] ****************************************************

TASK [Gathering Facts] *********************************************************
ok: [node1]
ok: [node2]
ok: [master]

TASK [Test] ********************************************************************
ok: [master] => {
    "msg": "Hello from master"
}
ok: [node1] => {
    "msg": "Hello from node1"
}
ok: [node2] => {
    "msg": "Hello from node2"
}

PLAY RECAP *********************************************************************
master                     : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
node1                      : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
node2                      : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

From now on, I will omit the output of the ansible log and hope we are on the
same page.

Let's start with the installation.

First things first, we need to install all the required dependencies. Apache
Spark requires JDK and Scala. On a ubuntu machine you would install them like this:

```
vagrant> sudo apt update
vagrant> sudo apt install openjdk-8-jdk scala
```

In ansible we will use one of the provided modules ``apt``, which aptly (hah!)
takes the responsibility of the equally named ``apt`` package manager.

```yaml
- name: Installing dependencies
  become: True
  apt:
    name: [ "openjdk-8-jdk", "scala", "python3" ]
    update_cache: yes
    cache_valid_time: 3600
```

Here we used the apt module and provided it with three options ``name``,
``update_cache`` and ``cache_valid_time``. The ``name`` option takes a list of
packages we wish to install,``update_cache`` tells apt to update the local
repository cache and ``cache_valid_time`` specifies the time for which we
decide the cache is valid (which speeds things up during testing among other
things). As with other options consult the ``ansible-doc`` for full list and
specification of options.

We also used the ``become`` option to tell ansible we wish to elevate this task
with superuser privilages.

Next, we are going to download the Apache Spark binary. Which can be found here:
[https://downloads.apache.org/spark/](https://downloads.apache.org/spark/) We will
be installing ``spark-3.0.1`` with ``hadoop3.2``. The full link to the tarball
then looks like this:

```
https://downloads.apache.org/spark/spark-3.0.1/spark-3.0.1-bin-hadoop3.2.tgz
```

To make out playbook more general we will separate information into
*variables*. Ansible allows us to declare variables in many places ( a bit [too
many](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#understanding-variable-precedence)
for my taste). On a play level we can declare them right using the ``vars``
option.  For the sake of brevity we declared the following variables (some of
which we wil use
[later](https://i.kym-cdn.com/photos/images/original/001/264/842/220.png))

- **spark_mirror**: Mirror from which to download Spark (i.e ``https://downloads.apache.org/spark``)
- **spark_version**: The version of Spark we wish to use (i.e. ``"3.0.1"``)
- **hadoop_version**: Version of hadoop. (i.e ``"hadoop3.2"``)

- **spark_parent_dir**: Location where we wish to put Spark ( i.e. "/usr/local" )
- **spark_target_dir**: Directory where will the Spark reside ( i.e. "/usr/local/spark" )

And some variables for convenience:
- **spark_name**: Just appended ``spark-`` prefix to the version (``"spark-3.0.1"``)
- **spark_fullname**: Full name of the wanted Spark package. (``"{{ spark_name }}-bin-{{ hadoop_version }}"``)
- **spark_tarball**: Name of the downloaded tarball. (``"{{ spark_fullname }}.tgz"``)
- **spark_tarball_url**: Full link to the package (``"{{ spark_mirror }}/{{ spark_name }}/{{ spark_tarball }}"``)

The playbook will then look like this:

```yaml
---
- name: Install Apache Spark
  hosts: all
  vars:
    - spark_mirror: "https://downloads.apache.org/spark"
    - spark_version: "3.0.1"
    - spark_name: "spark-{{ spark_version }}"
    - hadoop_version: "hadoop3.2"

    - spark_fullname: "{{ spark_name }}-bin-{{ hadoop_version }}"
    - spark_tarball: "{{ spark_fullname }}.tgz"
    - spark_tarball_url: "{{ spark_mirror }}/{{ spark_name }}/{{ spark_tarball }}"

    - spark_parent_dir: "/usr/local"
    - spark_target_dir: "/usr/local/spark"
  tasks:
    - name: Installing dependencies
      become: True
      apt:
        name: [ "openjdk-8-jdk", "scala", "python3" ]
        update_cache: yes
        cache_valid_time: 3600
```

Using shell we would download the package with something like this:
```
vagrant> sudo wget -O /tmp/spark-3.0.1-bin-hadoop2.7.tgz https://downloads.apache.org/spark/spark-3.0.1/spark-3.0.1-bin-hadoop2.7.tgz
```

Again ansible provides a useful *module* called ``get_url``. We add the following task:

```yaml
- name: Downloading Apache Spark sources
  become: True
  become_user: root
  get_url:
    url: "{{ spark_tarball_url }}"
    dest: "/tmp/{{ spark_tarball }}"
    mode: 644
```

Again ``url``, ``dest``, ``mode`` are relevant options for the module. The new
option ``become_user`` tells ``ansible`` to switch to the ``root`` account for
this task. It might be a bit superfluous here, but it doesn't hurt (most
notable it changes the group and user of created files to root which we could
have done with the ``owner`` and ``group`` options of ``get_url``)

Next we need to unpack the archive. 

Shell:
```
vagrant> sudo tar -xf /tmp/spark-3.0.1-bin-hadoop3.2.tgz -C /usr/local
vagrant> sudo chown -R root: /usr/local/spark-3.0.1-bin-hadoop3.2
```

For ansible se will use the ``unarchive`` module.
```yaml
- name: Unpacking tarball
  become: True
  become_user: root
  unarchive:
    remote_src: yes
    dest: '{{ spark_parent_dir }}'
    src: '/tmp/{{ spark_tarball }}'
    creates: '{{spark_parent_dir}}/{{ spark_fullname }}'
```

Here we see two notable options. The ``remote_src`` informs ansible that the
source file is located at the remote machine instead of your local host (the
machine from which you are running ansible).

The ``creates`` option informs ansible about the state of the environment after
the task is done. This way the next time the task is done and the tarball is
already unpacked, the task will simply be skipped. It's actually useless here
because the ``unarchive`` module is smart enough to infer this without the
option.  However it can be very useful if you, for example create a file
manually through the ``shell`` or ``command`` module.

Next we link the module to the desired destination. Note that we could have
just renamed the directory, but linking makes it easier when we (potentionally)
want to manage multiple versions.

Shell:
```
vagrant> sudo ln -s /usr/local/spark-3.0.1-bin-hadoop3.2/ /usr/local/spark
```
Ansible:
```yaml
- name: Link spark directory
  become: True
  become_user: root
  file:
    src: '{{ spark_parent_dir }}/{{ spark_fullname }}'
    dest: '{{ spark_target_dir }}'
    state: link
```

Next, we have to inform our system about the new Spark installation. In Linux
systems this is done through the environmental variables. Usually you would put
your new variables in files like ``.bash_profile``, ``.profile``,
``/etc/profile.d/`` etc.

However, Ansible's ``command`` module happens before shell starts so these variables
would not be discovered. However, all hope is not lost and we can put our
new environmental variables into ``/etc/environment``. However there is
a small drawback. Because this file is evaluated before shell the usual
`` PATH=$PATH:/new/path/bin `` doesn't work (the variables don't get expanded).
So we have to manipulate the ``PATH`` variable inside manually. It looks like
we are not the first ones to run to this problem ansible user **Ali-Akber Saifee**
provides a [solution](https://coderwall.com/p/ynvi0q/updating-path-with-ansible-system-wide).

Shell: *(you would probably edit the ``/etc/environment this file in a text editor)*
Ansible:
```yaml
- name: Add spark home to the environment
  become: True
  lineinfile:
    path: "/etc/environment"
    line: "{{ item }}"
  with_items:
    - 'SPARK_HOME={{ spark_target_dir }}'
    - 'PYSPARK_PYTHON=/usr/bin/python3'

# Courtesy of: https://coderwall.com/p/ynvi0q/updating-path-with-ansible-system-wide
- name: Include Spark in default path
  become: True
  lineinfile:
    dest: "/etc/environment"
    backrefs: yes
    regexp: 'PATH=(["]*)((?!.*?{{ item }}).*?)(["]*)$'
    line: 'PATH=\1\2:{{ item }}\3'
  with_items:
    - "{{ spark_target_dir }}/bin"
    - "{{ spark_target_dir }}/sbin"
```

Here we see in action the very useful ``lineinfile`` module, which helps us
edit files.

We see also the ``with_items`` construct, which is a simple *flow-control*
construct that generates tasks by expanding the ``item`` variable with the
supplied values (it's actually a bit more powerful than that, see
documentation).

And that's it! Spark (should) be successfully installed.

The final ``spark.yml`` looks like this:
```yaml
- name: Install Apache Spark
  hosts: all
  vars:
    - spark_mirror: "https://downloads.apache.org/spark"
    - spark_version: "3.0.1"
    - spark_name: "spark-{{ spark_version }}"
    - hadoop_version: "hadoop3.2"

    - spark_fullname: "{{ spark_name }}-bin-{{ hadoop_version }}"
    - spark_tarball: "{{ spark_fullname }}.tgz"
    - spark_tarball_url: "{{ spark_mirror }}/{{ spark_name }}/{{ spark_tarball }}"

    - spark_parent_dir: "/usr/local"
    - spark_target_dir: "/usr/local/spark"

  tasks:
    - name: Installing dependencies
      become: True
      apt:
        name: [ "openjdk-8-jdk", "scala", "python3" ]
        update_cache: yes
        cache_valid_time: 3600

    - name: Downloading Apache Spark sources
      become: True
      become_user: root
      get_url:
        url: "{{ spark_tarball_url }}"
        dest: "/tmp/{{ spark_tarball }}"
        mode: 644

    - name: Unpacking tarball
      become: True
      become_user: root
      unarchive:
        remote_src: yes
        dest: '{{ spark_parent_dir }}'
        src: '/tmp/{{ spark_tarball }}'
        creates: '{{spark_parent_dir}}/{{ spark_fullname }}'

    - name: Link spark directory
      become: True
      become_user: root
      file:
        src: '{{ spark_parent_dir }}/{{ spark_fullname }}'
        dest: '{{ spark_target_dir }}'
        state: link

    - name: Add spark home to the environment
      become: True
      lineinfile:
        path: "/etc/environment"
        line: "{{ item }}"
      with_items:
        - 'SPARK_HOME={{ spark_target_dir }}'
        - 'PYSPARK_PYTHON=/usr/bin/python3'

    # Courtesy of: https://coderwall.com/p/ynvi0q/updating-path-with-ansible-system-wide
    - name: Include Spark in default path
      become: True
      lineinfile:
        dest: "/etc/environment"
        backrefs: yes
        regexp: 'PATH=(["]*)((?!.*?{{ item }}).*?)(["]*)$'
        line: 'PATH=\1\2:{{ item }}\3'
      with_items:
        - "{{ spark_target_dir }}/bin"
        - "{{ spark_target_dir }}/sbin"
```

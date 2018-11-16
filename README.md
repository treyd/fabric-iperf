# fabric-iperf

A Fabric-based toolkit to run iperf tests on remote systems

## Description
This tool will let you run iperf on a set of remote systems to determine
the network quality (TCP throughput, etc) between every system.

For example, if you have 3 systems on a network named `A, B, C`,
this tool will test the following 9 paths:
 
 - `B -> A`
 - `C -> A`
 - `A -> B`
 - `C -> B`
 - `B -> C`
 - `A -> C`
 
Note that, as in the real world, this tool considers the forward and 
reverse path as two separate paths. For large numbers of systems, 
the number of paths can grow quite large (`N^2 - N`).  These paths will 
be tested one by one (to avoid co-interference). Use caution when
 scaling.


## Installation
This tool requires [Fabric](https://www.fabfile.org) version 1.14.0.  You can install 
Fabric easily by running the command `pip install Fabric==1.14.0`.

Note: `fabric-iperf` is *not* compatible with Fabric 2.x (see #1)

Once Fabric is installed, check out this repository to your machine

```
git clone https://github.com/treyd/fabric-iperf
```

`cd` to the `fabric-iperf` directory and run the command `fab --list`
to verify Fabric is installed and can see the tasks. 

## Setup
Fabric uses SSH to communicate with remote hosts, so you will need SSH
access to these systems.  Also, the SSH user needs to have `sudo`
privileges.

Fabric can also use OpenSSH config files and use public key auth for passwordless access.
See [Fabric documentation](http://docs.fabfile.org/en/latest/usage/fab.html) for more
info.

## Usage
The task that will run tests is the `test_network` task.  You can run it on 
a list of hosts given on the command-line, e.g:

```
fab -u username -H 192.168.202.77,192.168.202.78,192.168.202.79 test_network
```

Fabric will prompt you for a password if required, but will cache the
 password for use later.
 
If iperf is not installed on your remote systems, you can use the
`install_iperf` task to install it (uses `yum` or `apt-get` depending on
your distro)
 
 


 

![alt text][RX-M LLC]


# Cloud Foundry Container Runtime


## Lab 7 - Kubernetes Local Setup


Kubernetes is an open-source platform for automating deployment, scaling, and operations of application containers
across clusters of hosts. Kubernetes seeks to foster an ecosystem of components and tools that relieve the burden of
running applications in public and private clouds and can run on a range of platforms, from your laptop, to VMs on a
cloud provider, to racks of bare metal servers.

The effort required to set up a cluster varies from running a single command to installing and configuring individual
programs on each node in your cluster. In this lab we will setup the simplest possible single node Kubernetes cluster to
gain basic familiarity with Kubernetes. Our installation has several prerequisites:

- **Linux** – Our lab system vm is preinstalled with Ubuntu 16.04 though most Linux distributions supporting modern
container managers will work. Kubernetes is easiest to install on RHEL/Centos 7 and Ubuntu 16.04.
- **Docker** – Kubernetes will work with a variety of container managers but Docker is the most tested and widely
deployed (various minimum versions of Docker are required depending on the installation approach you take). The latest
Docker version is almost always recommended.
- **etcd** – Kubernetes requires a distributed key/value store to manage cluster metadata, we will use etcd for this
purpose.
- **Kubernetes** – Kubernetes is a microservice-based system and is composed of several services. The Kubelet handles
container operations for a given node, the API server supports the main cluster API, etc.

This lab will walk you through a basic, from scratch, Kubernetes installation, giving you a complete ground up view of
Kubernetes acquisition, build, and deployment in a simplified one node setting. The model below illustrates the
Kubernetes master and node roles, we will run both on a single system.

![alt text](./images/01.png "01")


### 1. Install Kubernetes Package Support

In this first step we will prepare our system and set it up to use packages from apt.kubernetes.io and then install the
mandatory Kubernetes packages from there.


#### Swap (vs memory limits)

As of 1.8 The kubelet fails if swap is enabled on a node. The 1.8 release notes suggest:

> To override the default and run with /proc/swaps on, set --fail-swap-on=false

However, for our purposes we can simply turn off swap:

```
user@ubuntu:~$ sudo cat /proc/swaps

Filename				Type		Size	Used	Priority
/dev/sda5                               partition	2094076	0	-1

user@ubuntu:~$ sudo swapoff -a

user@ubuntu:~$ sudo cat /proc/swaps

Filename				Type		Size	Used	Priority

user@ubuntu:~$
```

If you plan to reboot your VM you should also comment the swap volume entry in the file system table file, fstab:

```
user@ubuntu:~$ sudo vim /etc/fstab

user@ubuntu:~$ cat /etc/fstab

# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
# / was on /dev/sda1 during installation
UUID=ae4d6013-3015-4619-a301-77a55030c060 /               ext4    errors=remount-ro 0       1
# swap was on /dev/sda5 during installation
# UUID=70f4d3ab-c8a1-48f9-bf47-2e35e4d4275f none            swap    sw              0       0

user@ubuntu:~$
```

If you do not comment out the swap volume (the last line in the example above) the swap will re-enable on reboot and the
Kubelet will fail to start and therefore the rest of your cluster will not start either.


#### kubeadm

The kubeadm deployment tool requires that it run as root. Become root:

```
user@ubuntu:~$ sudo su -

root@ubuntu:~#
```

Some apt package repos use the aptitude protocol however the kubernetes packages are served of htts so we need to add
the apt https transport:

```
root@ubuntu:~# apt-get update && apt-get install -y apt-transport-https

Hit:1 http://us.archive.ubuntu.com/ubuntu xenial InRelease
Get:2 http://security.ubuntu.com/ubuntu xenial-security InRelease [102 kB]
Hit:3 https://download.docker.com/linux/ubuntu xenial InRelease                   
Get:4 http://us.archive.ubuntu.com/ubuntu xenial-updates InRelease [102 kB]       
Get:5 http://us.archive.ubuntu.com/ubuntu xenial-backports InRelease [102 kB]                 
Get:6 http://us.archive.ubuntu.com/ubuntu xenial-updates/main amd64 Packages [699 kB]
Get:7 http://us.archive.ubuntu.com/ubuntu xenial-updates/main i386 Packages [653 kB]
Fetched 1,659 kB in 3s (423 kB/s)                        
Reading package lists... Done
Reading package lists... Done
Building dependency tree       
Reading state information... Done
apt-transport-https is already the newest version (1.2.24).
0 upgraded, 0 newly installed, 0 to remove and 256 not upgraded.

root@ubuntu:~#
```

`apt-transport-https` was installed in the first lab, but here for completeness. Now add the Google cloud packages repo
key so that we can install packages hosted by Google:

```
root@ubuntu:~# curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

OK

root@ubuntu:~#
```

Next add a repository list file with an entry for Ubuntu Xenial apt.kubernetes.io packages. The following command copies
the text you enter to the "kubernetes.list" file, up to but not including the string "EOF".

```
root@ubuntu:~# echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" \
| sudo tee -a /etc/apt/sources.list.d/kubernetes.list

deb http://apt.kubernetes.io/ kubernetes-xenial main

root@ubuntu:~#
```

Update the package indexes to add the Kubernetes packages from apt.kubernetes.io:

```
root@ubuntu:~# apt-get update

Get:1 http://security.ubuntu.com/ubuntu xenial-security InRelease [102 kB]
Hit:2 http://us.archive.ubuntu.com/ubuntu xenial InRelease                                                
Hit:4 http://us.archive.ubuntu.com/ubuntu xenial-updates InRelease                                        
Hit:5 https://download.docker.com/linux/ubuntu xenial InRelease                    
Get:6 http://us.archive.ubuntu.com/ubuntu xenial-backports InRelease [102 kB]       
Get:3 https://packages.cloud.google.com/apt kubernetes-xenial InRelease [8,972 B]           
Get:7 https://packages.cloud.google.com/apt kubernetes-xenial/main amd64 Packages [12.4 kB]
Fetched 226 kB in 1s (151 kB/s)     
Reading package lists... Done

root@ubuntu:~#
```

Notice the new kubernetes-xenial repository above.

Now we can install standard Kubernetes packages.


### 2. Install Kubernetes with kubeadm

Kubernetes 1.4 added alpha support for the kubeadm tool, version 1.6 moved it to beta. The `kubeadmn` tool simplifies
the process of starting a Kubernetes cluster. To use `kubeadm` we'll also need the `kubectl` cluster CLI tool and the
`kubelet` node manager. We'll also install Kubernetes CNI (Container Network Interface) support for multi-host
networking should we add additional nodes.

> Note: Kubeadm offers no cloud provider (AWS/GCP/etc.) integrations (load balancers, etc.). Kops is the preferred tool
for K8s installation on cloud systems.

Use the aptitude package manager to install the desired packages:

```
root@ubuntu:~# apt-get install -y kubelet kubeadm kubectl kubernetes-cni

Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  ebtables socat
The following NEW packages will be installed:
  ebtables kubeadm kubectl kubelet kubernetes-cni socat

...

Setting up kubernetes-cni (0.6.0-00) ...
Setting up socat (1.7.3.1-1) ...
Setting up kubelet (1.10.0-00) ...
Setting up kubectl (1.10.0-00) ...
Setting up kubeadm (1.10.0-00) ...
Processing triggers for systemd (229-4ubuntu21.1) ...
Processing triggers for ureadahead (0.100.0-19) ...

root@ubuntu:~#
```


### 3. Start the Kubernetes Master Components

Have a look at the kubeadm help menu, notice we are using a "BETA" tool.

```
root@ubuntu:~# kubeadm -h

kubeadm: easily bootstrap a secure Kubernetes cluster.

    ┌──────────────────────────────────────────────────────────┐
    │ KUBEADM IS CURRENTLY IN BETA                             │
    │                                                          │
    │ But please, try it out and give us feedback at:          │
    │ https://github.com/kubernetes/kubeadm/issues             │
    │ and at-mention @kubernetes/sig-cluster-lifecycle-bugs    │
    │ or @kubernetes/sig-cluster-lifecycle-feature-requests    │
    └──────────────────────────────────────────────────────────┘

Example usage:

    Create a two-machine cluster with one master (which controls the cluster),
    and one node (where your workloads, like Pods and Deployments run).

    ┌──────────────────────────────────────────────────────────┐
    │ On the first machine:                                    │
    ├──────────────────────────────────────────────────────────┤
    │ master# kubeadm init                                     │
    └──────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────┐
    │ On the second machine:                                   │
    ├──────────────────────────────────────────────────────────┤
    │ node# kubeadm join <arguments-returned-from-init>        │
    └──────────────────────────────────────────────────────────┘

    You can then repeat the second step on as many other machines as you like.

Usage:
  kubeadm [command]

Available Commands:
  alpha       Experimental sub-commands not yet fully functional.
  completion  Output shell completion code for the specified shell (bash or zsh).
  config      Manage configuration for a kubeadm cluster persisted in a ConfigMap in the cluster.
  help        Help about any command
  init        Run this command in order to set up the Kubernetes master.
  join        Run this on any machine you wish to join an existing cluster
  reset       Run this to revert any changes made to this host by 'kubeadm init' or 'kubeadm join'.
  token       Manage bootstrap tokens.
  upgrade     Upgrade your cluster smoothly to a newer version with this command.
  version     Print the version of kubeadm

Flags:
  -h, --help   help for kubeadm

Use "kubeadm [command] --help" for more information about a command.

root@ubuntu:~#
```

Check the version of the tool.

```
root@ubuntu:~# kubeadm version

kubeadm version: &version.Info{Major:"1", Minor:"10", GitVersion:"v1.10.0", GitCommit:"fc32d2f3698e36b93322a3465f63a14e9f0eaead", GitTreeState:"clean", BuildDate:"2018-03-26T16:44:10Z", GoVersion:"go1.9.3", Compiler:"gc", Platform:"linux/amd64"}
root@ubuntu:~#
```

With all of the necessary prerequisites installed we can now use `kubeadm` to initialize a cluster.

**NOTE** in the output below, this line: `[apiclient] All control plane components are healthy after 59.502392 seconds`
indicates the approximate time it took to get the cluster up and running; this includes time spent downloading Docker
images for the control plane components, generating keys, manifests, etc. This example was captured with an uncontended
wired connection--yours may take 5-10 minutes on slow or shared wifi, _be patient!_.

```
root@ubuntu:~# kubeadm init

[init] Using Kubernetes version: v1.10.0
[init] Using Authorization modes: [Node RBAC]
[preflight] Running pre-flight checks.
	[WARNING SystemVerification]: docker version is greater than the most recently validated version. Docker version: 18.03.0-ce. Max validated version: 17.03
	[WARNING FileExisting-crictl]: crictl not found in system path
Suggestion: go get github.com/kubernetes-incubator/cri-tools/cmd/crictl
[certificates] Generated ca certificate and key.
[certificates] Generated apiserver certificate and key.
[certificates] apiserver serving cert is signed for DNS names [ubuntu kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 192.168.225.210]
[certificates] Generated apiserver-kubelet-client certificate and key.
[certificates] Generated etcd/ca certificate and key.
[certificates] Generated etcd/server certificate and key.
[certificates] etcd/server serving cert is signed for DNS names [localhost] and IPs [127.0.0.1]
[certificates] Generated etcd/peer certificate and key.
[certificates] etcd/peer serving cert is signed for DNS names [ubuntu] and IPs [192.168.225.210]
[certificates] Generated etcd/healthcheck-client certificate and key.
[certificates] Generated apiserver-etcd-client certificate and key.
[certificates] Generated sa key and public key.
[certificates] Generated front-proxy-ca certificate and key.
[certificates] Generated front-proxy-client certificate and key.
[certificates] Valid certificates and keys now exist in "/etc/kubernetes/pki"
[kubeconfig] Wrote KubeConfig file to disk: "/etc/kubernetes/admin.conf"
[kubeconfig] Wrote KubeConfig file to disk: "/etc/kubernetes/kubelet.conf"
[kubeconfig] Wrote KubeConfig file to disk: "/etc/kubernetes/controller-manager.conf"
[kubeconfig] Wrote KubeConfig file to disk: "/etc/kubernetes/scheduler.conf"
[controlplane] Wrote Static Pod manifest for component kube-apiserver to "/etc/kubernetes/manifests/kube-apiserver.yaml"
[controlplane] Wrote Static Pod manifest for component kube-controller-manager to "/etc/kubernetes/manifests/kube-controller-manager.yaml"
[controlplane] Wrote Static Pod manifest for component kube-scheduler to "/etc/kubernetes/manifests/kube-scheduler.yaml"
[etcd] Wrote Static Pod manifest for a local etcd instance to "/etc/kubernetes/manifests/etcd.yaml"
[init] Waiting for the kubelet to boot up the control plane as Static Pods from directory "/etc/kubernetes/manifests".
[init] This might take a minute or longer if the control plane images have to be pulled.
[apiclient] All control plane components are healthy after 59.502392 seconds
[uploadconfig] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[markmaster] Will mark node ubuntu as master by adding a label and a taint
[markmaster] Master ubuntu tainted and labelled with key/value: node-role.kubernetes.io/master=""
[bootstraptoken] Using token: qcof7m.533xwn1varmcum5x
[bootstraptoken] Configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstraptoken] Configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstraptoken] Configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstraptoken] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[addons] Applied essential addon: kube-dns
[addons] Applied essential addon: kube-proxy

Your Kubernetes master has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

You can now join any number of machines by running the following on each node
as root:

  kubeadm join 192.168.225.210:6443 --token qcof7m.533xwn1varmcum5x --discovery-token-ca-cert-hash sha256:5d585c9ca7b6025b1a04eee03b49ba34ad6b3385c9c417de7e6e1f291199a2c9

root@ubuntu:~#
```

Examine the output from kubeadm above; you **do not** need to follow the steps just now, we will be discussing and
performing them during the rest of this lab. Note that we get two preflight check warnings:

```
	[WARNING SystemVerification]: docker version is greater than the most recently validated version. Docker version: 18.03.0-ce. Max validated version: 17.03
	[WARNING FileExisting-crictl]: crictl not found in system path
```

Both are warnings and can be ignored but it is good to understand warnings that you ignore. The first complaint is that
Docker 17.03 is the highest tested version. Newer versions of Docker are backwards compatible API wise so this is ok.
Next we are warned that crictl is not found. The crictl tool is the CLI tool for the Container Runtime Interface (CRI)
control (ctl). This is a bogus warning and will probably go away soon (if kubeadm depends on crictl it should install
it!!).

Now that we have started k8s, we can resume being a regular user.

```
root@ubuntu:~# exit

logout

user@ubuntu:~$
```

The `kubeadm` tool generates an auth token which we can use to add additional nodes to the cluster, and then creates the
keys and certificates necessary for TLS. The initial master configures itself as a CA and self signs its certificate.
All of the PKI/TLS related files can be found in `/etc/kubernetes/pki`.

```
user@ubuntu:~$ ls -l /etc/kubernetes/pki/

total 60
-rw-r--r-- 1 root root 1216 Mar 28 10:13 apiserver.crt
-rw-r--r-- 1 root root 1094 Mar 28 10:13 apiserver-etcd-client.crt
-rw------- 1 root root 1675 Mar 28 10:13 apiserver-etcd-client.key
-rw------- 1 root root 1675 Mar 28 10:13 apiserver.key
-rw-r--r-- 1 root root 1099 Mar 28 10:13 apiserver-kubelet-client.crt
-rw------- 1 root root 1675 Mar 28 10:13 apiserver-kubelet-client.key
-rw-r--r-- 1 root root 1025 Mar 28 10:13 ca.crt
-rw------- 1 root root 1675 Mar 28 10:13 ca.key
drwxr-xr-x 2 root root 4096 Mar 28 10:13 etcd
-rw-r--r-- 1 root root 1025 Mar 28 10:13 front-proxy-ca.crt
-rw------- 1 root root 1679 Mar 28 10:13 front-proxy-ca.key
-rw-r--r-- 1 root root 1050 Mar 28 10:13 front-proxy-client.crt
-rw------- 1 root root 1679 Mar 28 10:13 front-proxy-client.key
-rw------- 1 root root 1675 Mar 28 10:13 sa.key
-rw------- 1 root root  451 Mar 28 10:13 sa.pub
user@ubuntu:~$
```

The `.crt` files are certificates with public keys embedded and the `.key` files are private keys. The `apiserver` files
are used by the `kube-apiserver` the ca files are associated with the certificate authority that `kubeadm` created and
the `sa` files are the Service Account keys used to gain root control of the cluster. Clearly all of the files here with
a key suffix should be carefully protected.


### 4. Exploring the Cluster

The `kubeadm` tool launches the `kubelet` on the local system to bootstrap the cluster services. Using the `kubelet`,
the kubeadm tool can run the remainder of the Kubernetes services in containers. This is, as they say, eating one's
own dog food. Kubernetes is a system promoting the use of microservice architecture and container packaging. Once the
`kubelet` is running, the balance of the Kubernetes microservices can be launched via container images.

Display information on the `kubelet` process:

```
user@ubuntu:~$ ps -fwwp $(pidof kubelet) | sed -e 's/--/\n--/g'

UID         PID   PPID  C STIME TTY          TIME CMD
root       4743      1  3 04:42 ?        00:00:31 /usr/bin/kubelet
--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf
--kubeconfig=/etc/kubernetes/kubelet.conf
--pod-manifest-path=/etc/kubernetes/manifests
--allow-privileged=true
--network-plugin=cni
--cni-conf-dir=/etc/cni/net.d
--cni-bin-dir=/opt/cni/bin
--cluster-dns=10.96.0.10
--cluster-domain=cluster.local
--authorization-mode=Webhook
--client-ca-file=/etc/kubernetes/pki/ca.crt
--cadvisor-port=0
--rotate-certificates=true
--cert-dir=/var/lib/kubelet/pki

user@ubuntu:~$
```

The switches used to launch the `kubelet` include:

- `--bootstrap-kubeconfig` - kubeconfig file that will be used to get client certificate for kubelet
- `--kubeconfig` - `kubelet` config file, contains `kube-apiserver` address and keys to authenticate with
- `--pod-manifest-path` - location of start pod configs the `kubelet` will run automatically
- `--allow-privileged` - tells the `kubelet` to allow containers to run with full root privileges when requested
- `--network-plugin` - sets the network plugin interface to be used
- `--cni-conf-dir` - specifies the CNI configuration directory (this directory is not created initially)
- `--cni-bin-dir` - specifies the CNI directory where executables are located
- `--cluster-dns` - the location of the cluster specific DNS service
- `--cluster-domain` - the domain name of the cluster
- `--authorization-mode` - allows for authorization to be driven by a remote service using REST
- `--client-ca-file` - sets the client certificate authentication file to be used
- `--cadvisor-port=0` - sets the port of the localhost cAdvisor endpoint (cAdvisor is a container monitoring tool)
- `--rotate-certificates=true` - (beta feature) Auto rotate the kubelet client certificates by requesting new certificates from the kube-apiserver when the certificate expiration approaches
- `--cert-dir=/var/lib/kubelet/pki` - The directory where the TLS certs are located

The `kubeadm` utility has configured the `kubelet` as a systemd service and enabled it so it will restart automatically
when we reboot. Examine the `kubelet` service configuration:

```
user@ubuntu:~$ systemctl --all --full status kubelet

● kubelet.service - kubelet: The Kubernetes Node Agent
   Loaded: loaded (/lib/systemd/system/kubelet.service; enabled; vendor preset: enabled)
  Drop-In: /etc/systemd/system/kubelet.service.d
           └─10-kubeadm.conf
   Active: active (running) since Wed 2018-03-28 10:13:24 PDT; 35min ago
     Docs: http://kubernetes.io/docs/
 Main PID: 3803 (kubelet)
    Tasks: 14
   Memory: 44.0M
      CPU: 48.274s
   CGroup: /system.slice/kubelet.service
           └─3803 /usr/bin/kubelet --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf --pod-manifest-path

Mar 28 10:48:22 ubuntu kubelet[3803]: W0328 10:48:22.753626    3803 cni.go:171] Unable to update cni config: No networks found in /etc/cni/net.d
Mar 28 10:48:22 ubuntu kubelet[3803]: E0328 10:48:22.754690    3803 kubelet.go:2125] Container runtime network not ready: NetworkReady=false reason:NetworkPlu
Mar 28 10:48:27 ubuntu kubelet[3803]: W0328 10:48:27.756939    3803 cni.go:171] Unable to update cni config: No networks found in /etc/cni/net.d
Mar 28 10:48:27 ubuntu kubelet[3803]: E0328 10:48:27.757110    3803 kubelet.go:2125] Container runtime network not ready: NetworkReady=false reason:NetworkPlu
user@ubuntu:~$
```

As you can see from the "Loaded" line the service is enabled, indicating it will start on system boot.

Take a moment to review the systemd service start up files. First the service file:

```
user@ubuntu:~$ sudo cat /lib/systemd/system/kubelet.service

[Unit]
Description=kubelet: The Kubernetes Node Agent
Documentation=http://kubernetes.io/docs/

[Service]
ExecStart=/usr/bin/kubelet
Restart=always
StartLimitInterval=0
RestartSec=10

[Install]
WantedBy=multi-user.target
user@ubuntu:~$
```

This just starts the service (/usr/bin/kubelet) and restarts in after 10 seconds if it crashes.

Now look over the configuration files in the service.d directory:

```
user@ubuntu:~$ sudo ls /etc/systemd/system/kubelet.service.d

10-kubeadm.conf
user@ubuntu:~$
```

Files in this directory are processed in lexical order. The numeric prefix ("10") makes it easy to order the files.
Display the one config file:

```
user@ubuntu:~$ sudo cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

[Service]
Environment="KUBELET_KUBECONFIG_ARGS=--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf"
Environment="KUBELET_SYSTEM_PODS_ARGS=--pod-manifest-path=/etc/kubernetes/manifests --allow-privileged=true"
Environment="KUBELET_NETWORK_ARGS=--network-plugin=cni --cni-conf-dir=/etc/cni/net.d --cni-bin-dir=/opt/cni/bin"
Environment="KUBELET_DNS_ARGS=--cluster-dns=10.96.0.10 --cluster-domain=cluster.local"
Environment="KUBELET_AUTHZ_ARGS=--authorization-mode=Webhook --client-ca-file=/etc/kubernetes/pki/ca.crt"
Environment="KUBELET_CADVISOR_ARGS=--cadvisor-port=0"
Environment="KUBELET_CERTIFICATE_ARGS=--rotate-certificates=true --cert-dir=/var/lib/kubelet/pki"
ExecStart=
ExecStart=/usr/bin/kubelet $KUBELET_KUBECONFIG_ARGS $KUBELET_SYSTEM_PODS_ARGS $KUBELET_NETWORK_ARGS $KUBELET_DNS_ARGS $KUBELET_AUTHZ_ARGS $KUBELET_CADVISOR_ARGS $KUBELET_CERTIFICATE_ARGS $KUBELET_EXTRA_ARGS
user@ubuntu:~$
```

So this is where all of the kubelet command line arguments come from.

Because the `kubelet` is passed the `--pod-manifest-path` switch it will start all of the pods described in the
specified directory.

```
user@ubuntu:~$ systemctl --all --full status kubelet | sed -e 's/--/\n--/g' | grep manifest

--pod-manifest-path=/etc/kubernetes/manifests
user@ubuntu:~$
```

List the files in the manifests directory:

```
user@ubuntu:~$ ls -l /etc/kubernetes/manifests/

total 16
-rwx------ 1 root root  876 Dec  4 11:11 etcd.yaml
-rwx------ 1 root root 2572 Dec  4 11:11 kube-apiserver.yaml
-rwx------ 1 root root 2133 Dec  4 11:11 kube-controller-manager.yaml
-rwx------ 1 root root  991 Dec  4 11:11 kube-scheduler.yaml
user@ubuntu:~$
```

Each of these files specifies a key component of our cluster's master node. The `etcd` component is the key/value store
housing our cluster's state. The `kube-apiserver` is the service implementing the Kubernetes API endpoints. The
`kube-scheduler` selects nodes for new pods to run on. The `kube-controller-manager` ensures that the correct number of
pods are running.

These YAML files tell the `kubelet` to run the associated cluster components in their own pods with the necessary
settings and container images. Display the images used on your system:

```
user@ubuntu:~$ sudo grep image /etc/kubernetes/manifests/*.yaml

/etc/kubernetes/manifests/etcd.yaml:    image: k8s.gcr.io/etcd-amd64:3.1.12
/etc/kubernetes/manifests/kube-apiserver.yaml:    image: k8s.gcr.io/kube-apiserver-amd64:v1.10.0
/etc/kubernetes/manifests/kube-controller-manager.yaml:    image: k8s.gcr.io/kube-controller-manager-amd64:v1.10.0
/etc/kubernetes/manifests/kube-scheduler.yaml:    image: k8s.gcr.io/kube-scheduler-amd64:v1.10.0
user@ubuntu:~$
```

In the example above, etcd v3.1.12 and Kubernetes 1.10 are in use. All of the images are dynamically pulled by Docker
from the gcr.io registry server using the "google_containers" public namespace.

List the containers running under Docker:

```
user@ubuntu:~$ docker container ls --format "{{.Command}}" --no-trunc | awk -F"--" '{print $1}'

"/usr/local/bin/kube-proxy
"/pause"
"kube-apiserver
"kube-scheduler
"kube-controller-manager
"etcd
"/pause"
"/pause"
"/pause"
"/pause"
user@ubuntu:~$
```

We will discuss the `pause` containers later.

Several Kubernetes services are running:

- etcd - The key/value store used to hold Kubernetes cluster state
- kube-apiserver - The Kubernetes api server
- kube-scheduler - The Kubernetes pod scheduler
- kube-controller-manager - The Kubernetes replica manager
- kube-proxy - Modifies the system iptables to support the service routing mesh (runs on all nodes)

The `kube-proxy` service addon is included by `kubeadm`.


#### Configure kubectl

The command line tool used to interact with our Kubernetes cluster is `kubectl`. While you can use `curl` and other
programs to communicate with Kubernetes at the API level, the `kubectl` command makes interacting with the cluster from
the command line easy, packaging up your requests and making the API calls for you.

Run the `kubectl config view` subcommand to display the current client configuration.

```yaml
user@ubuntu:~$ kubectl config view

apiVersion: v1
clusters: []
contexts: []
current-context: ""
kind: Config
preferences: {}
users: []
user@ubuntu:~$
```

As you can see the only value we have configured is the apiVersion which is set to v1, the current Kubernetes API
version. The `kubectl` command tries to reach the API server on port 8080 via the localhost loopback without TLS by
default.

Kubeadm establishes a config file during deployment of the control plane and places it in /etc/kubernetes as admin.conf.
We will take a closer look at this config file in lab 3 but for now follow the steps kubeadm describes in its output,
placing it in a new .kube directory under your home directory.

```
user@ubuntu:~$ mkdir -p $HOME/.kube

user@ubuntu:~$ sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config

user@ubuntu:~$ sudo chown user $HOME/.kube/config

user@ubuntu:~$
```

Verify the kubeconfig we just copied is understood:

```yaml
user@ubuntu:~$ kubectl config view

apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: REDACTED
    server: https://192.168.225.210:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
user@ubuntu:~$
```

The default context should be `kubernetes-admin@kubernetes`.

```
user@ubuntu:~$ kubectl config current-context

kubernetes-admin@kubernetes

user@ubuntu:~$
```

_If is not_, activate the kubernetes-admin@kubernetes context:

```
user@ubuntu:~$ kubectl config use-context kubernetes-admin@kubernetes

Switched to context "kubernetes-admin@kubernetes".

user@ubuntu:~$
```

Verify that the new context can access the cluster:

```
user@ubuntu:~$ kubectl get nodes

NAME      STATUS     ROLES     AGE       VERSION
ubuntu    NotReady   master    11m       v1.10.0
user@ubuntu:~$
```


#### Taints

During the default initialization of the cluster, kubeadm applies labels and taints to the master node so that no
workloads will run there. Because we want to run a one node cluster for testing, this will not do.

In Kubernetes terms, the master node is tainted. A taint consists of a _key_, a _value_, and an _effect_. The effect
must be _NoSchedule_, _PreferNoSchedule_ or _NoExecute_. You can view the taints on your node with the `kubectl`
command. Use the `kubectl describe` subcommand to see details for the master node having the host name "ubuntu":

```
user@ubuntu:~$ kubectl describe node ubuntu | grep -i taints

Taints:			node-role.kubernetes.io/master:NoSchedule
user@ubuntu:~$
```

We will examine the full describe output later but as you can see the master has the "node-role.kubernetes.io/master"
taint with the effect "NoSchedule".

This means the `kube-scheduler` can not place pods on this node. To remove this taint we can use the `kubectl taint`
subcommand.

**NOTE** The command below removes ("-") the dedicated ("dedicated") taint from all (--all) nodes in the cluster. **Do
not forget the trailing** `-` **following the taint key "dedicated"!** The `-` is what tells Kubernetes to remove the
taint!

> We know what you're thinking and we agree, "taint" is an awful name for this feature and a trailing dash with no space
is an equally wacky way to remove something.

```
user@ubuntu:~$ kubectl taint nodes --all node-role.kubernetes.io/master-

node "ubuntu" untainted
user@ubuntu:~$
```

Confirm the taint was removed.

```
user@ubuntu:~$ kubectl describe node ubuntu | grep -i taints

Taints:			<none>
user@ubuntu:~$
```

We haven't talked about annotations, but taint information is stored as an annotation thus it may not be retrieved via
standard tooling like `kubectl get nodes ubuntu -o taint`, etc.


### 5. Enable Networking and Related Features

You may have noticed that the _kube-dns_ plugin was listed as a master addon by `kubeadm` during the `init`.

```
...
[addons] Applied essential addon: kube-dns
...
```

However, it does not show up as one of the Docker containers running.  Lets install `jq` to more easily search and
format JSON output.

```
user@ubuntu:~$ sudo apt-get install jq -y

Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  libonig2
The following NEW packages will be installed:
  jq libonig2
0 upgraded, 2 newly installed, 0 to remove and 256 not upgraded.
Need to get 232 kB of archives.
After this operation, 829 kB of additional disk space will be used.
Get:1 http://us.archive.ubuntu.com/ubuntu xenial/universe amd64 libonig2 amd64 5.9.6-1 [88.1 kB]
Get:2 http://us.archive.ubuntu.com/ubuntu xenial/universe amd64 jq amd64 1.5+dfsg-1 [144 kB]
Fetched 232 kB in 1s (197 kB/s)
Selecting previously unselected package libonig2:amd64.
(Reading database ... 123525 files and directories currently installed.)
Preparing to unpack .../libonig2_5.9.6-1_amd64.deb ...
Unpacking libonig2:amd64 (5.9.6-1) ...
Selecting previously unselected package jq.
Preparing to unpack .../jq_1.5+dfsg-1_amd64.deb ...
Unpacking jq (1.5+dfsg-1) ...
Processing triggers for man-db (2.7.5-1) ...
Setting up libonig2:amd64 (5.9.6-1) ...
Setting up jq (1.5+dfsg-1) ...
Processing triggers for libc-bin (2.23-0ubuntu9) ...
user@ubuntu:~$
```

Next we'll call the Docker remote api and parse the response via jq:

```
user@ubuntu:~$ curl -s --unix-sock /var/run/docker.sock http:/containers/json | jq '.[].Image | match(".*dns.*")'

user@ubuntu:~$
```

Try listing the pods running on the cluster.

```
user@ubuntu:~$ kubectl get pods

No resources found.

user@ubuntu:~$
```

Nothing is returned because we are configured to view the "default" cluster namespace. System pods run in the Kubernetes
"kube-system" namespace. You can show all namespaces by using the _--all-namspaces_ switch.

```
user@ubuntu:~$ kubectl get pods --all-namespaces

NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE
kube-system   etcd-ubuntu                      1/1       Running   0          25m
kube-system   kube-apiserver-ubuntu            1/1       Running   0          25m
kube-system   kube-controller-manager-ubuntu   1/1       Running   0          25m
kube-system   kube-dns-545bc4bfd4-957v6        0/3       Pending   0          26m
kube-system   kube-proxy-l9jv6                 1/1       Running   0          26m
kube-system   kube-scheduler-ubuntu            1/1       Running   0          25m
user@ubuntu:~$
```

We confirmed no container(s) with DNS in the name are running, we do see a system pods with dns. Notice the STATUS is
Pending and 0 of 3 containers are READY.  

Why is it failing to start? Lets review the POD related events for kube-dns.

```
user@ubuntu:~$ kubectl get events --namespace=kube-system | grep dns

1m          27m          91        kube-dns-545bc4bfd4-957v6.14fd2d3426f56dfb        Pod                                                     Warning   FailedScheduling        default-scheduler       No nodes are available that match all of the predicates: NodeNotReady (1).
27m         27m          1         kube-dns-545bc4bfd4.14fd2d34270086ad              ReplicaSet                                              Normal    SuccessfulCreate        replicaset-controller   Created pod: kube-dns-545bc4bfd4-957v6
27m         27m          1         kube-dns.14fd2d34248f1004                         Deployment                                              Normal    ScalingReplicaSet       deployment-controller   Scaled up replica set kube-dns-545bc4bfd4 to 1
user@ubuntu:~$
```

That gives us a hint; we have a node running but why isn't it ready? It turns out that we told Kubernetes we would use
CNI for networking but we have not yet supplied a CNI plugin. We can easily add the Weave CNI VXLAN based container
networking drivers using a POD spec from the Internet.

The weave-kube path below points to a Kubernetes spec for a DaemonSet, which is a resource that runs on every node in a
cluster. You can review that spec via curl:

```
user@ubuntu:~$ curl -L \
"https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"

apiVersion: v1
kind: List
items:
  - apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: weave-net

...

user@ubuntu:~$
```

You can test the spec without running it using the `--dry-run=true` switch:

```
user@ubuntu:~$ kubectl apply -f \
"https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')" --dry-run=true

serviceaccount "weave-net" created (dry run)
clusterrole.rbac.authorization.k8s.io "weave-net" created (dry run)
clusterrolebinding.rbac.authorization.k8s.io "weave-net" created (dry run)
role.rbac.authorization.k8s.io "weave-net" created (dry run)
rolebinding.rbac.authorization.k8s.io "weave-net" created (dry run)
daemonset.extensions "weave-net" created (dry run)

user@ubuntu:~$
```

The config file creates several resources:

- The ServiceAccount, ClusterRole, ClusterRoleBinding, Role and Rolebinding configure the RBAC permissions for Weave
- The DaemonSet ensures that the weaveworks SDN images are running in a pod on all hosts

Run it for real this time:

```
user@ubuntu:~$ kubectl apply -f \
"https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"

serviceaccount "weave-net" created
clusterrole "weave-net" created
clusterrolebinding "weave-net" created
role "weave-net" created
rolebinding "weave-net" created
daemonset "weave-net" created

user@ubuntu:~$
```

Rerun your "get pods" subcommand to ensure that all containers in all pods are running (it may take a minute for
everything to start):

```
user@ubuntu:~$ kubectl get pods --all-namespaces

NAMESPACE     NAME                             READY     STATUS    RESTARTS   AGE
kube-system   etcd-ubuntu                      1/1       Running   0          52m
kube-system   kube-apiserver-ubuntu            1/1       Running   0          51m
kube-system   kube-controller-manager-ubuntu   1/1       Running   0          51m
kube-system   kube-dns-545bc4bfd4-957v6        3/3       Running   0          52m
kube-system   kube-proxy-l9jv6                 1/1       Running   0          52m
kube-system   kube-scheduler-ubuntu            1/1       Running   0          51m
kube-system   weave-net-q2gds                  2/2       Running   0          6m
user@ubuntu:~$
```

If we check related DNS pod events once more, we see progress!

```
user@ubuntu:~$ kubectl get events --namespace=kube-system --sort-by='{.lastTimestamp}' | grep dns

53m         53m          1         kube-dns.152024eafb7893aa                         Deployment                                              Normal    ScalingReplicaSet       deployment-controller   Scaled up replica set kube-dns-86f4d74b45 to 1
53m         53m          1         kube-dns-86f4d74b45.152024eafd36863d              ReplicaSet                                              Normal    SuccessfulCreate        replicaset-controller   Created pod: kube-dns-86f4d74b45-dz9gl
3m          53m          176       kube-dns-86f4d74b45-dz9gl.152024eafc147ae3        Pod                                                     Warning   FailedScheduling        default-scheduler       0/1 nodes are available: 1 node(s) were not ready.
38s         38s          1         kube-dns-86f4d74b45-dz9gl.152027d3cce67c8b        Pod                                                     Normal    SuccessfulMountVolume   kubelet, ubuntu         MountVolume.SetUp succeeded for volume "kube-dns-config"
38s         38s          1         kube-dns-86f4d74b45-dz9gl.152027d3ce794745        Pod                                                     Normal    SuccessfulMountVolume   kubelet, ubuntu         MountVolume.SetUp succeeded for volume "kube-dns-token-m9kbv"
37s         37s          1         kube-dns-86f4d74b45-dz9gl.152027d3ef3006da        Pod          spec.containers{kubedns}                   Normal    Pulling                 kubelet, ubuntu         pulling image "k8s.gcr.io/k8s-dns-kube-dns-amd64:1.14.8"
31s         31s          1         kube-dns-86f4d74b45-dz9gl.152027d57a63c90a        Pod          spec.containers{kubedns}                   Normal    Started                 kubelet, ubuntu         Started container
31s         31s          1         kube-dns-86f4d74b45-dz9gl.152027d56d9b0eac        Pod          spec.containers{kubedns}                   Normal    Pulled                  kubelet, ubuntu         Successfully pulled image "k8s.gcr.io/k8s-dns-kube-dns-amd64:1.14.8"
31s         31s          1         kube-dns-86f4d74b45-dz9gl.152027d57a8ce5f1        Pod          spec.containers{dnsmasq}                   Normal    Pulling                 kubelet, ubuntu         pulling image "k8s.gcr.io/k8s-dns-dnsmasq-nanny-amd64:1.14.8"
31s         31s          1         kube-dns-86f4d74b45-dz9gl.152027d5706db941        Pod          spec.containers{kubedns}                   Normal    Created                 kubelet, ubuntu         Created container
23s         23s          1         kube-dns-86f4d74b45-dz9gl.152027d72f947add        Pod          spec.containers{dnsmasq}                   Normal    Pulled                  kubelet, ubuntu         Successfully pulled image "k8s.gcr.io/k8s-dns-dnsmasq-nanny-amd64:1.14.8"
23s         23s          1         kube-dns-86f4d74b45-dz9gl.152027d7329e2377        Pod          spec.containers{dnsmasq}                   Normal    Created                 kubelet, ubuntu         Created container
23s         23s          1         kube-dns-86f4d74b45-dz9gl.152027d73d408c5d        Pod          spec.containers{dnsmasq}                   Normal    Started                 kubelet, ubuntu         Started container
23s         23s          1         kube-dns-86f4d74b45-dz9gl.152027d73d6f0246        Pod          spec.containers{sidecar}                   Normal    Pulling                 kubelet, ubuntu         pulling image "k8s.gcr.io/k8s-dns-sidecar-amd64:1.14.8"
17s         17s          1         kube-dns-86f4d74b45-dz9gl.152027d899a74691        Pod          spec.containers{sidecar}                   Normal    Pulled                  kubelet, ubuntu         Successfully pulled image "k8s.gcr.io/k8s-dns-sidecar-amd64:1.14.8"
17s         17s          1         kube-dns-86f4d74b45-dz9gl.152027d8a779a2f0        Pod          spec.containers{sidecar}                   Normal    Started                 kubelet, ubuntu         Started container
17s         17s          1         kube-dns-86f4d74b45-dz9gl.152027d89c8b8d81        Pod          spec.containers{sidecar}                   Normal    Created                 kubelet, ubuntu         Created container
user@ubuntu:~$
```

Another way to view logs is to use LASTSEEN option to sort, in conjunction with `-w` which watches the logs (type
control c to exit this mode).

```
user@ubuntu:~$ kubectl get events --namespace=kube-system -w --sort-by=LASTSEEN

...
^c
user@ubuntu:~$
```

Lets look at the logs of the DNS related containers.

```
user@ubuntu:~$ kubectl get pods -o json --namespace=kube-system \
| jq -r '.items[] | select(.metadata.name | startswith("kube-dns")) | .spec.containers[].name' \
| xargs -I % kubectl logs $(kubectl get pods -o name --namespace=kube-system | grep dns) \
--namespace=kube-system -c %

I1204 19:58:45.759940       1 dns.go:48] version: 1.14.4-2-g5584e04
I1204 19:58:45.760656       1 server.go:70] Using configuration read from directory: /kube-dns-config with period 10s
I1204 19:58:45.760715       1 server.go:113] FLAG: --alsologtostderr="false"
I1204 19:58:45.760742       1 server.go:113] FLAG: --config-dir="/kube-dns-config"
I1204 19:58:45.760756       1 server.go:113] FLAG: --config-map=""
I1204 19:58:45.760765       1 server.go:113] FLAG: --config-map-namespace="kube-system"
I1204 19:58:45.760776       1 server.go:113] FLAG: --config-period="10s"
I1204 19:58:45.760807       1 server.go:113] FLAG: --dns-bind-address="0.0.0.0"

...

user@ubuntu:~$
```

Congratulations, you have completed the Kubernetes local setup lab!

<br>

_Copyright (c) 2013-2018 RX-M LLC, Cloud Native Consulting, all rights reserved_

[RX-M LLC]: http://rx-m.io/rxm-cnc.svg "RX-M LLC"

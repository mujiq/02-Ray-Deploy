Detailed Specifications for Ray Cluster Deployment on Ubuntu using Ansible and Docker
This document outlines the detailed specifications for deploying a Ray cluster on Ubuntu servers using Ansible for automation and Docker for containerization. The deployment will be idempotent, ensuring a clean slate before each new deployment, and all configuration files will be managed centrally on the Ansible control (master) node.
1. Architecture Overview
The Ray cluster will consist of:
Ansible Control Node: A machine (typically the user's workstation or a dedicated server) from which Ansible playbooks are executed. This node will store all Ansible playbooks, roles, inventory, and Ray configuration files.
Ray Head Node: A dedicated Ubuntu server that will host the Ray head process, Redis, and optionally a Ray Dashboard. This node will also serve as the central point for Ray cluster management.
Ray Worker Nodes: One or more Ubuntu servers that will host Ray worker processes. These nodes will connect to the Ray head node.
Each Ray node (head and workers) will run Ray within Docker containers, providing isolation and consistent environments.
+---------------------+             +---------------------+             +---------------------+
| Ansible Control Node|             |    Ray Head Node    |             |   Ray Worker Node   |
|---------------------|             |---------------------|             |---------------------|
| - Ansible Playbooks |             | - Docker Engine     |             | - Docker Engine     |
| - Inventory Files   |             | - Ray Head Container|             | - Ray Worker Container|
| - Ray Config Files  |             |   (Ray, Redis, Dash)|             |                     |
|                     | <---------> |                     | <---------> |                     |
|                     |   (SSH/SCP) |                     |   (Ray/Redis)|                     |
+---------------------+             +---------------------+             +---------------------+


2. Prerequisites
Before running the Ansible playbook, ensure the following prerequisites are met:
2.1 Ansible Control Node
Ansible: Version 2.10 or higher installed.
Python: Python 3 and pip installed.
boto3 (Optional): If deploying on AWS EC2 or similar cloud providers, boto3 might be required for dynamic inventory or instance management.
SSH Key: An SSH key pair configured for passwordless access to all target Ubuntu servers. The public key must be present on all target nodes.
ssh-agent: Recommended for managing SSH keys.
2.2 Target Ubuntu Servers (Head and Worker Nodes)
Operating System: Ubuntu Server 20.04 LTS or newer.
Python: Python 3 installed (usually pre-installed on Ubuntu).
sudo privileges: A user with sudo privileges configured for Ansible to use.
Internet Access: Required for installing Docker and pulling Docker images.
Firewall Rules: Ensure necessary ports are open (e.g., SSH (22), Ray head port (6379 by default), Ray dashboard port (8265 by default), and worker ports).
3. Ansible Playbook Structure
The Ansible project will be structured as follows:
ray-cluster-ansible/
├── inventory.ini                 # Static inventory file
├── ansible.cfg                   # Ansible configuration
├── site.yml                      # Main playbook
├── roles/
│   ├── common/                   # Common tasks for all nodes
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── handlers/
│   │       └── main.yml
│   ├── docker/                   # Docker installation and configuration
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── handlers/
│   │       └── main.yml
│   ├── ray_head/                 # Ray head node specific tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── templates/
│   │   │   └── ray_head_start.sh.j2 # Script to start Ray head
│   │   │   └── ray_config.yaml.j2   # Ray cluster config (optional)
│   │   └── handlers/
│   │       └── main.yml
│   ├── ray_worker/               # Ray worker node specific tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── templates/
│   │   │   └── ray_worker_start.sh.j2 # Script to start Ray worker
│   │   └── handlers/
│   │       └── main.yml
└── group_vars/
    └── all.yml                   # Global variables
    └── head_nodes.yml            # Variables specific to head nodes
    └── worker_nodes.yml          # Variables specific to worker nodes


inventory.ini Example:
[head_nodes]
ray_head_node ansible_host=192.168.1.10 ansible_user=ubuntu

[worker_nodes]
ray_worker_node_1 ansible_host=192.168.1.11 ansible_user=ubuntu
ray_worker_node_2 ansible_host=192.168.1.12 ansible_user=ubuntu

[ray_cluster:children]
head_nodes
worker_nodes


ansible.cfg Example:
[defaults]
inventory = inventory.ini
remote_user = ubuntu
private_key_file = ~/.ssh/id_rsa # Path to your SSH private key
host_key_checking = False        # Disable for initial setup, enable in production
roles_path = ./roles


4. Idempotency Strategy (Cleanup and Re-deployment)
Idempotency will be achieved by:
Pre-deployment Cleanup: Before deploying new components, existing Docker containers, images (if specified), and Ray-related files will be removed.
Conditional Execution: Tasks will use when clauses to ensure actions are only taken if necessary (e.g., only install Docker if not already installed).
State Management: Ansible's declarative nature inherently helps with idempotency. For services, state=started and state=restarted will be used appropriately.
Cleanup Tasks (within main.yml of relevant roles):
Docker Containers: Stop and remove all Ray-related Docker containers.
- name: Stop and remove existing Ray head container
  community.docker.docker_container:
    name: ray_head
    state: absent
    force_delete: true
  ignore_errors: true # Continue even if container doesn't exist
  when: inventory_hostname in groups['head_nodes']

- name: Stop and remove existing Ray worker container
  community.docker.docker_container:
    name: ray_worker
    state: absent
    force_delete: true
  ignore_errors: true
  when: inventory_hostname in groups['worker_nodes']


Docker Images: Optionally remove specific Ray Docker images to ensure a fresh pull.
- name: Remove Ray Docker image (optional, for fresh pull)
  community.docker.docker_image:
    name: "{{ ray_docker_image }}"
    state: absent
  ignore_errors: true


Ray-related Files: Remove any previously deployed Ray start scripts or configuration files from the target nodes.
- name: Remove old Ray head start script
  ansible.builtin.file:
    path: /usr/local/bin/start_ray_head.sh
    state: absent
  when: inventory_hostname in groups['head_nodes']

- name: Remove old Ray worker start script
  ansible.builtin.file:
    path: /usr/local/bin/start_ray_worker.sh
    state: absent
  when: inventory_hostname in groups['worker_nodes']


5. Configuration Management
All Ray configuration files and Docker run commands will be managed as Jinja2 templates on the Ansible control node. These templates will be rendered with variables defined in group_vars and then copied to the respective target nodes.
Example: group_vars/all.yml
---
ray_docker_image: "rayproject/ray:2.9.0" # Specify Ray version
ray_redis_port: 6379
ray_dashboard_port: 8265
ray_object_manager_port: 8076
ray_node_manager_port: 8077
ray_metrics_export_port: 8080
ray_temp_dir: "/tmp/ray" # Persistent temp directory for Ray


Example: group_vars/head_nodes.yml
---
ray_head_ip: "{{ hostvars[groups['head_nodes'][0]]['ansible_host'] }}"


Example: ray_head/templates/ray_head_start.sh.j2
#!/bin/bash
# This script starts the Ray head node within a Docker container.

# Stop and remove any existing container with the same name
docker stop ray_head > /dev/null 2>&1 || true
docker rm ray_head > /dev/null 2>&1 || true

# Create the Ray temporary directory if it doesn't exist
mkdir -p {{ ray_temp_dir }}
chmod 777 {{ ray_temp_dir }}

# Run the Ray head container
docker run -d \
  --name ray_head \
  --network host \
  --shm-size=2gb \
  -v {{ ray_temp_dir }}:{{ ray_temp_dir }} \
  {{ ray_docker_image }} \
  ray start --head \
  --port {{ ray_redis_port }} \
  --dashboard-port {{ ray_dashboard_port }} \
  --object-manager-port {{ ray_object_manager_port }} \
  --node-manager-port {{ ray_node_manager_port }} \
  --metrics-export-port {{ ray_metrics_export_port }} \
  --temp-dir {{ ray_temp_dir }} \
  --num-cpus "{{ ansible_facts['processor_vcpus'] }}" \
  --memory "{{ ansible_facts['ansible_memtotal_mb'] * 0.8 }}MiB" # Use 80% of total memory


Example: ray_worker/templates/ray_worker_start.sh.j2
#!/bin/bash
# This script starts a Ray worker node within a Docker container.

# Stop and remove any existing container with the same name
docker stop ray_worker > /dev/null 2>&1 || true
docker rm ray_worker > /dev/null 2>&1 || true

# Create the Ray temporary directory if it doesn't exist
mkdir -p {{ ray_temp_dir }}
chmod 777 {{ ray_temp_dir }}

# Run the Ray worker container
docker run -d \
  --name ray_worker \
  --network host \
  --shm-size=2gb \
  -v {{ ray_temp_dir }}:{{ ray_temp_dir }} \
  {{ ray_docker_image }} \
  ray start --address="{{ ray_head_ip }}:{{ ray_redis_port }}" \
  --temp-dir {{ ray_temp_dir }} \
  --num-cpus "{{ ansible_facts['processor_vcpus'] }}" \
  --memory "{{ ansible_facts['ansible_memtotal_mb'] * 0.8 }}MiB" # Use 80% of total memory


6. Detailed Steps (Ansible Tasks)
6.1 site.yml (Main Playbook)
---
- name: Deploy Ray Cluster
  hosts: ray_cluster
  become: true
  gather_facts: true
  vars_files:
    - group_vars/all.yml

  roles:
    - common
    - docker

- name: Configure Ray Head Node
  hosts: head_nodes
  become: true
  gather_facts: true
  vars_files:
    - group_vars/all.yml
    - group_vars/head_nodes.yml

  roles:
    - ray_head

- name: Configure Ray Worker Nodes
  hosts: worker_nodes
  become: true
  gather_facts: true
  vars_files:
    - group_vars/all.yml
    - group_vars/worker_nodes.yml

  roles:
    - ray_worker


6.2 roles/common/tasks/main.yml
---
- name: Update apt cache
  ansible.builtin.apt:
    update_cache: yes
    cache_valid_time: 3600 # Update every hour

- name: Install common packages
  ansible.builtin.apt:
    name:
      - curl
      - apt-transport-https
      - ca-certificates
      - software-properties-common
    state: present


6.3 roles/docker/tasks/main.yml
---
- name: Check if Docker is installed
  ansible.builtin.command: docker --version
  register: docker_check
  ignore_errors: true
  changed_when: false

- name: Add Docker GPG key
  ansible.builtin.apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present
  when: docker_check.rc != 0

- name: Add Docker APT repository
  ansible.builtin.apt_repository:
    repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_facts['lsb']['codename'] }} stable"
    state: present
  when: docker_check.rc != 0

- name: Install Docker Engine
  ansible.builtin.apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-buildx-plugin
      - docker-compose-plugin
    state: present
    update_cache: yes
  when: docker_check.rc != 0

- name: Ensure Docker service is running and enabled
  ansible.builtin.systemd:
    name: docker
    state: started
    enabled: yes

- name: Add 'ubuntu' user to docker group (if not already added)
  ansible.builtin.user:
    name: "{{ ansible_user }}"
    groups: docker
    append: yes
  when: docker_check.rc != 0 # Only add if Docker was just installed


6.4 roles/ray_head/tasks/main.yml
---
- name: Ensure Ray temporary directory exists on head node
  ansible.builtin.file:
    path: "{{ ray_temp_dir }}"
    state: directory
    mode: '0777' # Ensure full permissions for Ray processes

- name: Stop and remove existing Ray head container (idempotency)
  community.docker.docker_container:
    name: ray_head
    state: absent
    force_delete: true
  ignore_errors: true

- name: Remove old Ray head start script (idempotency)
  ansible.builtin.file:
    path: /usr/local/bin/start_ray_head.sh
    state: absent

- name: Copy Ray head start script to head node
  ansible.builtin.template:
    src: ray_head_start.sh.j2
    dest: /usr/local/bin/start_ray_head.sh
    mode: '0755'

- name: Start Ray head container
  ansible.builtin.command: /usr/local/bin/start_ray_head.sh
  args:
    chdir: /usr/local/bin
  register: ray_head_start_output
  changed_when: "'ray_head' not in ray_head_start_output.stdout" # Only report change if container was actually started/restarted

- name: Display Ray head container status
  ansible.builtin.command: docker ps -f name=ray_head
  register: ray_head_ps
  changed_when: false

- name: Print Ray head container status
  ansible.builtin.debug:
    msg: "{{ ray_head_ps.stdout }}"

- name: Wait for Ray head to be ready (optional, for robustness)
  ansible.builtin.wait_for:
    port: "{{ ray_redis_port }}"
    host: "{{ ansible_host }}"
    timeout: 60
    state: started
  delegate_to: localhost # Check from Ansible control node
  when: inventory_hostname in groups['head_nodes']

- name: Wait for Ray dashboard to be ready (optional)
  ansible.builtin.wait_for:
    port: "{{ ray_dashboard_port }}"
    host: "{{ ansible_host }}"
    timeout: 60
    state: started
  delegate_to: localhost
  when: inventory_hostname in groups['head_nodes']


6.5 roles/ray_worker/tasks/main.yml
---
- name: Ensure Ray temporary directory exists on worker node
  ansible.builtin.file:
    path: "{{ ray_temp_dir }}"
    state: directory
    mode: '0777' # Ensure full permissions for Ray processes

- name: Stop and remove existing Ray worker container (idempotency)
  community.docker.docker_container:
    name: ray_worker
    state: absent
    force_delete: true
  ignore_errors: true

- name: Remove old Ray worker start script (idempotency)
  ansible.builtin.file:
    path: /usr/local/bin/start_ray_worker.sh
    state: absent

- name: Copy Ray worker start script to worker node
  ansible.builtin.template:
    src: ray_worker_start.sh.j2
    dest: /usr/local/bin/start_ray_worker.sh
    mode: '0755'

- name: Start Ray worker container
  ansible.builtin.command: /usr/local/bin/start_ray_worker.sh
  args:
    chdir: /usr/local/bin
  register: ray_worker_start_output
  changed_when: "'ray_worker' not in ray_worker_start_output.stdout"

- name: Display Ray worker container status
  ansible.builtin.command: docker ps -f name=ray_worker
  register: ray_worker_ps
  changed_when: false

- name: Print Ray worker container status
  ansible.builtin.debug:
    msg: "{{ ray_worker_ps.stdout }}"


7. Ray Cluster Configuration
The primary Ray cluster configuration is handled via command-line arguments passed to ray start within the Docker run commands. For more advanced configurations (e.g., autoscaling, resource limits per node), a ray_cluster_config.yaml file can be created as a template on the Ansible control node and mounted into the Docker containers.
Example: ray_head/templates/ray_config.yaml.j2 (Optional)
# Example Ray cluster configuration (for advanced use cases like autoscaling)
# This file would be mounted into the Ray head container.
# This example is illustrative; actual content depends on Ray's configuration needs.
cluster_name: my-ansible-ray-cluster
min_workers: 0
max_workers: 10
idle_timeout_minutes: 5
provider:
    type: custom # Or aws, gcp, azure etc.
    # ... provider-specific configuration ...
head_node:
    resources: {"CPU": 1, "GPU": 0}
    # ... other head node specific settings ...
worker_nodes:
    - resources: {"CPU": 1, "GPU": 0}
      # ... worker node specific settings ...


If using ray_config.yaml, the ray_head_start.sh.j2 would need to mount this file:
# ...
  -v /path/to/ray_config.yaml:/opt/ray/ray_cluster_config.yaml \ # Mount the config file
  {{ ray_docker_image }} \
  ray start --head \
  --config-file /opt/ray/ray_cluster_config.yaml \ # Use the config file
# ...


8. Verification Steps
After running the Ansible playbook, verify the cluster deployment:
Check Docker Containers:
On each node (head and workers), SSH in and run:
docker ps

You should see ray_head running on the head node and ray_worker running on worker nodes.
Access Ray Dashboard:
Open a web browser and navigate to http://<RAY_HEAD_NODE_IP>:8265. You should see the Ray Dashboard, indicating the head node is operational.
Check Ray Cluster Status:
From the Ray head node (SSH in), run:
docker exec ray_head ray status

This command should show all connected nodes (head and workers) and their resources.
Run a Simple Ray Program:
From the Ray head node (SSH in), you can run a simple Python script to test the cluster:
docker exec -it ray_head python -c "import ray; ray.init(); print(ray.cluster_resources())"

This should print the aggregated resources of your Ray cluster.
This detailed specification provides a robust and idempotent approach to deploying a Ray cluster using Ansible and Docker on Ubuntu, with all configurations centrally managed.

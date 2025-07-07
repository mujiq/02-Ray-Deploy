# Monitoring Role

This Ansible role sets up a comprehensive monitoring stack for the Ray cluster using:

- **Prometheus**: For collecting and storing metrics
- **Node Exporter**: For system-level metrics (CPU, memory, disk I/O, network)
- **cAdvisor**: For container-level metrics
- **Grafana**: For visualization and dashboards

## Components

### Prometheus

- Runs on the head node
- Scrapes metrics from all nodes in the cluster
- Default port: 9090
- Data directory: `/home/gpadmin/prometheus_data`

### Node Exporter

- Runs on all nodes (head and workers)
- Exposes system metrics
- Default port: 9100

### cAdvisor

- Runs on all nodes (head and workers)
- Collects container metrics
- Default port: 8080

### Grafana

- Runs on the head node
- Provides dashboards for visualization
- Default port: 3000
- Default credentials: admin/admin
- Data directory: `/home/gpadmin/grafana_data`

## Dashboards

The following dashboards are automatically provisioned:

1. **Node Exporter Dashboard**: System-level metrics for all nodes
2. **Docker Container Dashboard**: Container-level metrics for all containers
3. **Ray Cluster Dashboard**: Specific metrics for Ray containers

## Accessing the Dashboards

- Prometheus: `http://<head-node-ip>:9090`
- Grafana: `http://<head-node-ip>:3000`

## Metrics Collected

### System Metrics (via Node Exporter)

- CPU usage
- Memory usage
- Disk I/O
- Network traffic
- Filesystem usage

### Container Metrics (via cAdvisor)

- Container CPU usage
- Container memory usage
- Container network traffic
- Container disk I/O

### Ray-specific Metrics

- Ray container CPU usage
- Ray container memory usage
- Ray container network traffic
- Ray container disk I/O 
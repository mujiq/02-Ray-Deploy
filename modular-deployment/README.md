# Ray Cluster Modular Deployment System

## Overview

This modular deployment system provides a checkpoint-based approach to deploying Ray clusters with human-in-the-loop approval for critical operations. The system is designed to be integrated with REST APIs and WebUI interfaces for remote management.

## Architecture

### Components

1. **Checkpoint Playbooks** - Individual Ansible playbooks for each deployment phase
2. **Validation Scripts** - Python scripts for status checking and health monitoring
3. **REST API Interface** - Flask-based API server for programmatic control
4. **Master Orchestrator** - Command-line tool for deployment management
5. **Approval System** - Human-in-the-loop approval mechanism for destructive operations

### Design Principles

- **Idempotent Operations** - All checkpoints can be run multiple times safely
- **Human Approval** - Critical operations require explicit human approval
- **Status Tracking** - Comprehensive logging and status reporting
- **API-First Design** - Built for integration with WebUI and automation systems
- **Incremental Deployment** - Resume from any checkpoint after failures

## Checkpoints

### 1. Prerequisites Check (`01-prerequisites-check.yml`)
- **Purpose**: Validate system requirements and network connectivity
- **Approval Required**: No
- **Destructive**: No
- **What it does**:
  - Check Python installation
  - Validate SSH connectivity
  - Check system resources (CPU, memory, disk)
  - Test network connectivity between nodes

### 2. Docker Installation (`02-docker-installation.yml`)
- **Purpose**: Install and configure Docker on all nodes
- **Approval Required**: Yes
- **Destructive**: No
- **What it does**:
  - Install Docker packages
  - Configure Docker daemon
  - Add users to docker group
  - Start Docker service
  - Pull required container images

### 3. Cleanup Existing (`03-cleanup-existing.yml`)
- **Purpose**: Remove existing Ray installations
- **Approval Required**: Yes
- **Destructive**: Yes ⚠️
- **What it does**:
  - Stop and remove Ray containers
  - Kill Ray processes
  - Clean up temporary directories
  - Remove configuration files

### 4. Ray Deployment (`04-ray-deployment.yml`)
- **Purpose**: Deploy Ray head and worker nodes
- **Approval Required**: No
- **Destructive**: No
- **What it does**:
  - Deploy Ray head container
  - Deploy Ray worker containers
  - Configure cluster networking
  - Verify cluster connectivity

### 5. Monitoring Deployment (`05-monitoring-deployment.yml`)
- **Purpose**: Deploy monitoring stack
- **Approval Required**: No
- **Destructive**: No
- **What it does**:
  - Deploy Prometheus
  - Deploy Grafana with dashboards
  - Deploy Node Exporter on all nodes
  - Deploy cAdvisor for container metrics

### 6. Final Validation (`06-final-validation.yml`)
- **Purpose**: Comprehensive cluster validation
- **Approval Required**: No
- **Destructive**: No
- **What it does**:
  - Test Ray cluster functionality
  - Validate monitoring endpoints
  - Run sample workloads
  - Generate deployment report

## Usage

### Command Line Interface

#### List Available Checkpoints
```bash
./modular-deployment/deploy-master.py --list-checkpoints
```

#### Run Single Checkpoint
```bash
./modular-deployment/deploy-master.py --checkpoint prerequisites-check
```

#### Deploy Complete Cluster
```bash
./modular-deployment/deploy-master.py --deploy
```

#### Resume from Specific Checkpoint
```bash
./modular-deployment/deploy-master.py --deploy --start-from ray-deployment
```

#### Auto-approve All Checkpoints (DANGEROUS)
```bash
./modular-deployment/deploy-master.py --deploy --auto-approve
```

### Validation and Status Checking

#### Check Overall Status
```bash
./modular-deployment/validation/validate-checkpoint.py
```

#### Check Specific Checkpoint
```bash
./modular-deployment/validation/validate-checkpoint.py --checkpoint docker-installation
```

#### Check Cluster Health Only
```bash
./modular-deployment/validation/validate-checkpoint.py --health-only
```

#### Check Approval Requirements
```bash
./modular-deployment/validation/validate-checkpoint.py --approval-check cleanup-existing
```

### REST API Server

#### Start API Server
```bash
cd modular-deployment/api-interface
pip install flask flask-cors
python flask-api-server.py
```

#### API Endpoints

**Get Cluster Status**
```http
GET /api/v1/cluster/status
```

**Execute Checkpoint**
```http
POST /api/v1/checkpoints/docker-installation
Content-Type: application/json

{
  "approve": true
}
```

**Grant Approval**
```http
POST /api/v1/approvals/cleanup-existing
Content-Type: application/json

{
  "approved_by": "admin",
  "reason": "Planned maintenance",
  "acknowledge_risks": true
}
```

**Get Execution Status**
```http
GET /api/v1/executions/{execution_id}
```

## Approval System

### How Approvals Work

1. **Check Requirement** - Checkpoint checks if approval is required
2. **Request Approval** - System prompts for human approval
3. **Approval File** - Creates approval file in `/tmp/checkpoint-{name}-approved`
4. **Execute** - Checkpoint proceeds with operation
5. **Cleanup** - Approval file is removed after completion

### Approval Methods

#### Interactive (CLI)
```bash
# System will prompt for approval
./modular-deployment/deploy-master.py --checkpoint cleanup-existing
```

#### API-based
```bash
# Grant approval via API
curl -X POST http://localhost:8000/api/v1/approvals/cleanup-existing \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": "admin", 
    "reason": "Planned upgrade",
    "acknowledge_risks": true
  }'
```

#### Manual File Creation
```bash
# Manually create approval file
echo '{"approved_at": "'$(date -Iseconds)'", "approved_by": "manual"}' > /tmp/checkpoint-cleanup-existing-approved
```

## Integration with WebUI

### API Integration Points

The REST API provides all necessary endpoints for WebUI integration:

1. **Status Dashboard** - Real-time cluster status and checkpoint progress
2. **Approval Interface** - UI for reviewing and approving destructive operations
3. **Execution Control** - Start, stop, and monitor checkpoint executions
4. **Health Monitoring** - Live cluster health and performance metrics

### Sample WebUI Flow

1. **Dashboard View** - Show cluster status and available actions
2. **Deployment Planning** - Select checkpoints to execute
3. **Approval Workflow** - Present approval requests with impact details
4. **Progress Monitoring** - Real-time execution status and logs
5. **Health Monitoring** - Grafana dashboard integration

### API Response Examples

**Cluster Status**
```json
{
  "deployment_status": "IN_PROGRESS",
  "completed_checkpoints": ["prerequisites-check", "docker-installation"],
  "total_checkpoints": 6,
  "cluster_health": {
    "overall_status": "HEALTHY",
    "ray_cluster": {"status": "HEALTHY", "nodes": 5},
    "monitoring": {"status": "HEALTHY"},
    "containers": {"total": 15, "running": 15}
  }
}
```

**Approval Required Response**
```json
{
  "error": "APPROVAL_REQUIRED",
  "checkpoint": "cleanup-existing",
  "approval_info": {
    "approval_required": true,
    "destructive_operation": true,
    "impact_summary": [
      "⚠️ DESTRUCTIVE: Remove all existing Ray containers",
      "⚠️ DESTRUCTIVE: Delete Ray temporary directories"
    ]
  }
}
```

## File Structure

```
modular-deployment/
├── playbooks/                      # Checkpoint playbooks
│   ├── 01-prerequisites-check.yml
│   ├── 02-docker-installation.yml
│   ├── 03-cleanup-existing.yml
│   ├── 04-ray-deployment.yml
│   ├── 05-monitoring-deployment.yml
│   └── 06-final-validation.yml
├── validation/                     # Status validation tools
│   └── validate-checkpoint.py
├── api-interface/                  # REST API server
│   ├── rest-api-spec.yaml         # OpenAPI specification
│   └── flask-api-server.py        # Flask implementation
├── deploy-master.py               # Master orchestrator
└── README.md                      # This file
```

## Monitoring and Logging

### Checkpoint Results
- Each checkpoint saves results to `/tmp/checkpoint-{name}-{node}.json`
- Includes status, timestamps, and detailed execution information
- Used by validation scripts and API for status reporting

### Deployment Tracking
- Master deployment state saved to `/tmp/deployment-complete.json`
- Failure information saved to `/tmp/deployment-failure.json`
- Execution logs available through API

### Health Monitoring
- Prometheus metrics on port 9090
- Grafana dashboards on port 3000
- Node Exporter on port 9100 (all nodes)
- cAdvisor on port 8081 (all nodes)

## Security Considerations

### Approval System
- Destructive operations require explicit approval
- Approval includes operator identification and reasoning
- Risk acknowledgment required for destructive operations

### API Security
- Consider adding authentication/authorization for production
- Rate limiting for checkpoint execution endpoints
- Input validation for all API requests

### Network Security
- Ensure proper firewall rules for monitoring ports
- Secure SSH key management for Ansible
- Monitor access to approval files

## Troubleshooting

### Common Issues

**Checkpoint Fails**
1. Check checkpoint status: `validate-checkpoint.py --checkpoint <name>`
2. Review Ansible logs for specific errors
3. Verify prerequisites are met
4. Check approval requirements

**Approval Not Working**
1. Verify approval file exists: `ls /tmp/checkpoint-*-approved`
2. Check file permissions and content
3. Ensure checkpoint name matches exactly

**API Server Issues**
1. Check Python dependencies: `pip install flask flask-cors`
2. Verify paths to playbooks and inventory
3. Check port 8000 availability

### Recovery Procedures

**Failed Deployment**
1. Check failure information: `cat /tmp/deployment-failure.json`
2. Resume from failed checkpoint: `--start-from <checkpoint-name>`
3. Fix underlying issues before retrying

**Corrupted State**
1. Clean up approval files: `rm /tmp/checkpoint-*-approved`
2. Reset checkpoint data: `rm /tmp/checkpoint-*.json`
3. Start fresh deployment

## Future Enhancements

### Planned Features
- Web-based UI for deployment management
- Advanced scheduling and orchestration
- Integration with CI/CD pipelines
- Automated rollback capabilities
- Enhanced monitoring and alerting

### API Extensions
- Authentication and authorization
- Webhook notifications
- Advanced filtering and querying
- Bulk operations support
- Historical deployment tracking

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review checkpoint logs and status
3. Validate system prerequisites
4. Check API documentation for integration issues 
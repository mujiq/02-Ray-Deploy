# Ray Cluster Deployment with Ansible and Docker

## Overview

This project provides a comprehensive Ray cluster deployment solution using Ansible and Docker, featuring:

- **Modular Checkpoint-Based Deployment** - Human-in-the-loop approval system
- **Complete Monitoring Stack** - Prometheus, Grafana, Node Exporter, cAdvisor
- **REST API Interface** - Ready for WebUI integration
- **Idempotent Operations** - Safe deployment and recovery mechanisms
- **Production-Ready Monitoring** - Comprehensive metrics and dashboards

## Quick Start

### 1. Deploy Complete Ray Cluster
```bash
# Interactive deployment with approval prompts
./modular-deployment/deploy-master.py --deploy

# Or auto-approve all operations (use with caution)
./modular-deployment/deploy-master.py --deploy --auto-approve
```

### 2. Check Cluster Status
```bash
./modular-deployment/validation/validate_checkpoint.py --format text
```

### 3. Access Monitoring Dashboards
- **Ray Dashboard**: http://192.168.40.240:8265
- **Prometheus**: http://192.168.40.240:9090  
- **Grafana**: http://192.168.40.240:3000 (admin/admin123)

### 4. Deploy AI Services
```bash
# Deploy TTS Service
cd ai-services/tts/
./deployment/deploy_tts.sh --install-deps --port 8000

# Test TTS Service
curl -X POST http://192.168.40.240:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Ray cluster!", "emotion": "happy"}'
```

### 5. Access AI Services
- **TTS Service API**: http://192.168.40.240:8000
- **TTS API Docs**: http://192.168.40.240:8000/docs
- **TTS WebSocket**: ws://192.168.40.240:8000/ws/tts

## Architecture

### Current Deployment
- **Head Node**: 1 node (MASTER) - 32 CPUs, 125GB RAM
- **Worker Nodes**: 4 nodes (G-241, G-242, G-243, G-244) - 16 CPUs each
- **Total Cluster**: 96 CPUs, 500GB+ RAM
- **Monitoring**: Full Prometheus/Grafana stack deployed
- **AI Services**: Production-ready TTS service deployed

### Components

#### 1. **Modular Deployment System**
```
modular-deployment/
├── playbooks/           # 6 checkpoint playbooks
├── validation/          # Status validation tools
├── api-interface/       # REST API server & OpenAPI spec  
├── deploy-master.py     # Master orchestrator
└── README.md           # Detailed documentation
```

#### 2. **AI Services** 🤖
```
ai-services/
├── tts/                 # Text-to-Speech service (Production Ready)
│   ├── deployment/      # Ray Serve TTS deployment
│   ├── tests/           # Comprehensive test suite
│   └── docs/            # API documentation
└── README.md           # AI services overview
```

**Current Services:**
- **🎵 TTS Service** (port 8000): Multi-model text-to-speech with streaming
  - Models: Kyutai TTS, Orpheus TTS, FastSpeech2
  - Features: Emotion control, voice cloning, real-time streaming
  - Auto-scaling: 1-5 replicas based on load

**Planned Services:**
- **🖼️ Image Generation**: Stable Diffusion, DALL-E style
- **🧠 LLM Service**: Large Language Models for text generation
- **🎭 Computer Vision**: Object detection, image classification

#### 3. **Ray Cluster Services**
- **Ray Head**: Central coordinator with dashboard
- **Ray Workers**: Distributed compute nodes
- **Redis**: Cluster state management
- **Docker**: Containerized deployment

#### 4. **Monitoring Stack**
- **Prometheus** (port 9090): Metrics collection and storage
- **Grafana** (port 3000): Visualization dashboards
- **Node Exporter** (port 9100): System metrics on all nodes
- **cAdvisor** (port 8081): Container metrics on all nodes

## Deployment Checkpoints

The deployment is broken into 6 modular checkpoints:

| Checkpoint | Description | Approval Required | Destructive |
|------------|-------------|-------------------|-------------|
| **1. Prerequisites Check** | Validate system requirements | ❌ No | ❌ No |
| **2. Docker Installation** | Install Docker on all nodes | ✅ Yes | ❌ No |
| **3. Cleanup Existing** | Remove existing Ray installations | ✅ Yes | ⚠️ **Yes** |
| **4. Ray Deployment** | Deploy Ray head and workers | ❌ No | ❌ No |
| **5. Monitoring Deployment** | Deploy Prometheus/Grafana | ❌ No | ❌ No |
| **6. Final Validation** | Comprehensive testing | ❌ No | ❌ No |

### Checkpoint Management

#### Run Single Checkpoint
```bash
./modular-deployment/deploy-master.py --checkpoint prerequisites-check
```

#### Resume from Specific Checkpoint
```bash
./modular-deployment/deploy-master.py --deploy --start-from ray-deployment
```

#### List All Checkpoints
```bash
./modular-deployment/deploy-master.py --list-checkpoints
```

## Human-in-the-Loop Approval System

### Approval Methods

#### 1. Interactive CLI
```bash
# System prompts for approval
./modular-deployment/deploy-master.py --checkpoint cleanup-existing
```

#### 2. REST API
```bash
curl -X POST http://localhost:8000/api/v1/approvals/cleanup-existing \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": "admin",
    "reason": "Planned maintenance", 
    "acknowledge_risks": true
  }'
```

#### 3. Manual File Creation
```bash
echo '{"approved_at": "'$(date -Iseconds)'", "approved_by": "manual"}' > \
  /tmp/checkpoint-cleanup-existing-approved
```

## REST API Server

### Start API Server
```bash
cd modular-deployment/api-interface
pip install flask flask-cors
python flask-api-server.py
```

### Key Endpoints

#### Cluster Management
```http
GET  /api/v1/cluster/status          # Overall cluster status
GET  /api/v1/cluster/health          # Health metrics
GET  /api/v1/nodes                   # List all nodes
```

#### Checkpoint Control
```http
GET  /api/v1/checkpoints             # List all checkpoints
POST /api/v1/checkpoints/{name}      # Execute checkpoint
GET  /api/v1/checkpoints/{name}      # Check status
```

#### Approval Management
```http
GET  /api/v1/approvals/{name}        # Check approval requirements
POST /api/v1/approvals/{name}        # Grant approval
```

### Example API Usage

**Get Cluster Status:**
```bash
curl http://localhost:8000/api/v1/cluster/status | jq
```

**Execute Checkpoint with Approval:**
```bash
curl -X POST http://localhost:8000/api/v1/checkpoints/docker-installation \
  -H "Content-Type: application/json" \
  -d '{"approve": true}'
```

## Monitoring and Metrics

### Available Dashboards
1. **Node Exporter Dashboard** - System metrics (CPU, memory, disk I/O, network)
2. **Docker Container Dashboard** - Container-level resource usage  
3. **Ray Cluster Dashboard** - Ray-specific performance metrics

### Key Metrics Tracked
- **System Resources**: CPU utilization, memory usage, disk I/O
- **Network Performance**: Traffic, bandwidth, connection counts
- **Container Metrics**: Resource usage per container
- **Ray Cluster**: Task execution, node health, resource allocation
- **Storage**: Disk usage, I/O patterns across all nodes

### Grafana Access
- **URL**: http://192.168.40.240:3000
- **Username**: admin
- **Password**: admin123

## Status Validation

### Check Overall Status
```bash
./modular-deployment/validation/validate_checkpoint.py --format text
```

### Check Specific Checkpoint
```bash
./modular-deployment/validation/validate_checkpoint.py --checkpoint docker-installation
```

### Check Cluster Health Only
```bash
./modular-deployment/validation/validate_checkpoint.py --health-only
```

### Check Approval Requirements
```bash
./modular-deployment/validation/validate_checkpoint.py --approval-check cleanup-existing
```

## Testing Suite

### Comprehensive Test Framework
The project includes a comprehensive testing suite organized in the `tests/` directory:

```
tests/
├── cluster/          # Ray cluster functionality tests
│   ├── quick_test.py            # Fast connectivity test
│   ├── detailed_test.py         # Comprehensive performance test
│   ├── simple_cluster_test.py   # 5-minute stress test
│   └── test_ray_cluster.py      # Legacy comprehensive test
├── docker/           # Docker configuration tests
│   └── test-docker.yml          # Docker installation verification
├── validation/       # Configuration validation tests
│   ├── validate_cluster_versions.py   # Version consistency check
│   └── validate_checkpoint.py         # Deployment validation
└── benchmark/        # Performance benchmarking (future)
```

### Quick Test Commands

**Run All Tests (Recommended):**
```bash
./run_tests.sh
```

**Run Specific Test Category:**
```bash
./run_tests.sh --category cluster
```

**List All Available Tests:**
```bash
./run_tests.sh --list
```

**Manual Test Execution:**
```bash
# Run Quick Cluster Test
sudo docker cp tests/cluster/quick_test.py ray_head:/tmp/
sudo docker exec ray_head python /tmp/quick_test.py

# Validate Cluster Versions
python3 tests/validation/validate_cluster_versions.py

# Test Docker Configuration
ansible-playbook tests/docker/test-docker.yml
```

### Expected Test Results
- ✅ All 5 nodes detected and responsive
- ✅ 96 total CPU cores available
- ✅ Version consistency across cluster
- ✅ Efficient task distribution (20x+ parallelization)
- ✅ No container health issues

For detailed testing documentation, see [tests/README.md](tests/README.md).

## File Structure

### Current Project Layout
```
02-Ray-Deploy/
├── specs/                           # Project specifications
├── ai-services/                     # AI Services for Ray cluster
│   ├── tts/                         # Text-to-Speech service
│   │   ├── deployment/              # TTS deployment scripts
│   │   ├── tests/                   # TTS test suite
│   │   └── docs/                    # TTS documentation
│   └── README.md                    # AI services overview
├── tests/                           # Comprehensive testing suite
│   ├── cluster/                     # Ray cluster functionality tests
│   ├── docker/                      # Docker configuration tests  
│   ├── validation/                  # Configuration validation tests
│   └── benchmark/                   # Performance benchmarking (future)
├── roles/                           # Ansible roles
│   ├── common/                      # Common setup tasks
│   ├── docker/                      # Docker installation
│   ├── ray_head/                    # Ray head node setup
│   ├── ray_worker/                  # Ray worker node setup
│   └── monitoring/                  # Monitoring stack
├── group_vars/                      # Ansible variables
├── modular-deployment/              # Modular deployment system
│   ├── playbooks/                   # Individual checkpoint playbooks
│   ├── api-interface/               # REST API server
│   └── deploy-master.py             # Master orchestrator
├── inventory.ini                    # Cluster node definitions
├── site.yml                         # Legacy monolithic playbook
└── README.md                        # This file
```

## WebUI Integration

The system is designed for seamless WebUI integration:

### API Integration Points
1. **Status Dashboard** - Real-time cluster status and progress
2. **Approval Interface** - Review and approve destructive operations
3. **Execution Control** - Start, stop, monitor checkpoint executions
4. **Health Monitoring** - Live performance metrics and alerts

### Sample WebUI Flow
1. **Dashboard** → Show cluster status and available actions
2. **Planning** → Select checkpoints to execute
3. **Approval** → Review impact and grant approvals
4. **Monitoring** → Track progress and view logs
5. **Health** → Integrated Grafana dashboards

## Security Features

### Approval System
- **Destructive Operation Protection** - Explicit approval required
- **Operator Identification** - Track who approved what
- **Risk Acknowledgment** - Must acknowledge destructive operations
- **Audit Trail** - Complete operation logging

### Best Practices
- **Idempotent Operations** - Safe to run multiple times
- **Rollback Capability** - Resume from any checkpoint
- **Input Validation** - Secure API endpoints
- **Access Control** - Consider authentication for production

## Troubleshooting

### Common Issues

#### Checkpoint Fails
1. Check status: `validate_checkpoint.py --checkpoint <name>`
2. Review Ansible logs for errors
3. Verify prerequisites are met
4. Check approval requirements

#### Approval Not Working  
1. Verify approval file: `ls /tmp/checkpoint-*-approved`
2. Check file permissions and content
3. Ensure checkpoint name matches exactly

#### API Server Issues
1. Install dependencies: `pip install flask flask-cors`
2. Verify paths to playbooks and inventory
3. Check port 8000 availability

### Recovery Procedures

#### Failed Deployment
1. Check failure info: `cat /tmp/deployment-failure.json`
2. Resume from checkpoint: `--start-from <checkpoint-name>`
3. Fix underlying issues before retry

#### Reset State
1. Clean approval files: `rm /tmp/checkpoint-*-approved`
2. Reset checkpoint data: `rm /tmp/checkpoint-*.json`
3. Start fresh deployment

## Legacy Deployment (Monolithic)

For reference, the original monolithic deployment is still available:

```bash
# Deploy everything at once (legacy method)
ansible-playbook site.yml

# Test Docker installation
ansible-playbook test-docker.yml
```

## Performance Optimization

### Current Cluster Performance
- **Total CPUs**: 96 cores across 5 nodes
- **Memory**: 500GB+ total RAM
- **Network**: Gigabit connectivity
- **Storage**: High-performance local disks

### Scaling Recommendations
- **Add Workers**: Update inventory.ini and run worker deployment
- **GPU Support**: Add GPU-enabled nodes for ML workloads
- **Storage**: Consider distributed storage for large datasets
- **Networking**: Monitor for bottlenecks in high-throughput scenarios

## Future Enhancements

### Planned Features
- **Web UI** - Complete dashboard for deployment management
- **Advanced Scheduling** - Cron-based deployment automation
- **CI/CD Integration** - Pipeline integration hooks
- **Automated Rollback** - Intelligent failure recovery
- **Enhanced Monitoring** - Custom alerts and notifications

### API Extensions
- **Authentication** - OAuth/JWT integration
- **Webhooks** - Event notifications
- **Advanced Querying** - Filtering and search
- **Bulk Operations** - Multi-node operations
- **Historical Tracking** - Deployment history and analytics

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review checkpoint logs: `/tmp/checkpoint-*.json`
3. Validate prerequisites: `01-prerequisites-check.yml`
4. Check API documentation: `modular-deployment/api-interface/rest-api-spec.yaml`

---

## Success! 🎉

Your Ray cluster is now deployed with:
- ✅ **5-node cluster** (1 head + 4 workers)
- ✅ **96 total CPU cores** 
- ✅ **Complete monitoring stack**
- ✅ **Modular deployment system**
- ✅ **REST API interface**
- ✅ **Human-in-the-loop safety**

**Ready for production workloads and WebUI integration!** 
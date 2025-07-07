# 🤖 AI Services for Ray Cluster

A collection of production-ready AI services designed for deployment on Ray cluster infrastructure.

## 🌟 Overview

This directory contains AI services that leverage the Ray cluster's distributed computing capabilities for scalable AI inference. Each service is designed to be:

- **Production-ready** with monitoring and health checks
- **Auto-scaling** based on load using Ray Serve
- **Fault-tolerant** with robust error handling
- **API-first** with REST and WebSocket support
- **Well-documented** with comprehensive guides

## 📁 Available Services

### 🎵 Text-to-Speech (TTS) Service
**Location**: `tts/`  
**Status**: ✅ Production Ready

**Features**:
- Multiple state-of-the-art models (Kyutai, Orpheus, FastSpeech2)
- Real-time streaming audio generation
- Emotion control (happy, sad, angry, neutral)
- Voice cloning capabilities
- WebSocket streaming support
- Auto-scaling (1-5 replicas)

**Quick Start**:
```bash
cd tts/
./deployment/deploy_tts.sh --install-deps
```

**Documentation**: [TTS Service README](tts/README.md)

### 🔮 Future Services (Planned)

#### 🖼️ Image Generation Service
**Status**: 📋 Planned

**Features** (Planned):
- Stable Diffusion models
- DALL-E style generation
- Image-to-image transformation
- Batch processing
- Style transfer

#### 🧠 Large Language Model (LLM) Service
**Status**: 📋 Planned

**Features** (Planned):
- Multiple LLM models (Llama, GPT-style)
- Text generation and completion
- Conversational AI
- Code generation
- RAG (Retrieval Augmented Generation)

#### 🎭 Computer Vision Service
**Status**: 📋 Planned

**Features** (Planned):
- Object detection
- Image classification
- Face recognition
- OCR (Optical Character Recognition)
- Video analysis

## 🏗️ Architecture

### Service Structure
Each AI service follows a standardized structure:

```
ai-services/<service-name>/
├── deployment/           # Deployment scripts and configurations
│   ├── deploy_<service>.py      # Main service (Ray Serve)
│   ├── deploy_<service>.sh      # Automated deployment script
│   └── requirements_<service>.txt # Python dependencies
├── tests/               # Testing and client examples
│   └── <service>_client_examples.py # Test suite
├── docs/                # Documentation
│   └── README.md               # Detailed documentation
├── models/              # Model-specific implementations (optional)
├── utils/               # Utility functions (optional)
└── README.md           # Service overview
```

### Ray Cluster Integration

All services are designed to leverage the existing Ray cluster:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ray Head      │    │  Ray Worker 1   │    │  Ray Worker 2   │
│  192.168.40.240 │    │ 192.168.40.241  │    │ 192.168.40.242  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Service Router  │    │ AI Service      │    │ AI Service      │
│ Load Balancer   │    │ Replicas        │    │ Replicas        │
│ Health Monitor  │    │ Model Loading   │    │ Model Loading   │
│ Ray Dashboard   │    │ GPU Processing  │    │ GPU Processing  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Cluster Resources**:
- **Total CPUs**: 96 cores across 5 nodes
- **Memory**: 500GB+ total RAM
- **GPUs**: Available for model acceleration
- **Storage**: High-performance local disks

## 🚀 Getting Started

### Prerequisites

1. **Ray Cluster Running**:
   ```bash
   # Check cluster status
   python3 -c "import ray; ray.init(); print(ray.cluster_resources())"
   ```

2. **Python Environment**:
   - Python 3.9+ (compatible with Ray cluster)
   - Ray 2.47.1
   - GPU support (optional but recommended)

### Deploying Services

#### Option 1: Individual Service Deployment
```bash
# Deploy TTS service
cd ai-services/tts/
./deployment/deploy_tts.sh --install-deps --port 8000
```

#### Option 2: Multi-Service Deployment (Future)
```bash
# Deploy all services (planned feature)
./deploy_all_services.sh
```

### Service Discovery

Services will be available at:
- **TTS Service**: `http://ray-head:8000`
- **Image Service**: `http://ray-head:8001` (planned)
- **LLM Service**: `http://ray-head:8002` (planned)
- **Vision Service**: `http://ray-head:8003` (planned)

## 📊 Monitoring & Management

### Ray Dashboard
Access the Ray dashboard at: `http://192.168.40.240:8265`

**Features**:
- Cluster resource usage
- Service deployment status
- Performance metrics
- Error tracking
- Auto-scaling visualization

### Service Health Checks
Each service provides standardized health endpoints:

```bash
# TTS service health
curl http://ray-head:8000/health

# General format
curl http://ray-head:<port>/health
```

### Logging
Services use structured logging with:
- Ray native logging system
- Service-specific log files
- Error tracking and alerting
- Performance metrics collection

## 🔧 Development Guidelines

### Adding New Services

1. **Create Service Directory**:
   ```bash
   mkdir -p ai-services/<new-service>/{deployment,tests,docs,models}
   ```

2. **Follow Architecture**:
   - Inherit from `ray.serve.Deployment`
   - Implement health checks
   - Add auto-scaling configuration
   - Create comprehensive tests

3. **Required Files**:
   - `deployment/deploy_<service>.py` - Main service
   - `deployment/deploy_<service>.sh` - Deployment script
   - `deployment/requirements_<service>.txt` - Dependencies
   - `tests/<service>_client_examples.py` - Test suite
   - `docs/README.md` - Documentation
   - `README.md` - Service overview

### Code Standards

- **Python Style**: Follow PEP 8
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit tests and integration tests
- **Error Handling**: Robust error handling and logging
- **Performance**: Optimize for Ray cluster distribution

### Testing

```bash
# Test individual service
cd ai-services/<service>/
python3 tests/<service>_client_examples.py

# Run cluster tests (from project root)
./run_tests.sh --category cluster
```

## 🌐 API Standards

All AI services follow consistent API patterns:

### Common Endpoints
- `GET /health` - Service health and metrics
- `GET /models` - Available models
- `GET /docs` - API documentation (Swagger/OpenAPI)
- `POST /predict` - Main inference endpoint
- `POST /batch` - Batch processing
- `WS /stream` - Real-time streaming

### Request/Response Format
```json
{
  "request_id": "uuid",
  "timestamp": "iso-format",
  "data": { /* service-specific */ },
  "options": { /* service-specific */ }
}
```

### Error Handling
```json
{
  "error": {
    "code": "SERVICE_ERROR",
    "message": "Human readable message",
    "details": { /* additional context */ }
  }
}
```

## 📈 Performance & Scaling

### Expected Performance

| Service | Latency | Throughput | GPU Memory | CPU Cores |
|---------|---------|------------|------------|-----------|
| TTS     | 200-800ms | 10-50 req/s | 2-8GB | 2-4 |
| Image   | 1-5s    | 5-20 req/s | 4-12GB | 4-8 |
| LLM     | 100-2000ms | 1-10 req/s | 8-24GB | 8-16 |
| Vision  | 50-500ms | 20-100 req/s | 2-6GB | 2-4 |

### Auto-scaling Configuration
```python
autoscaling_config = {
    "min_replicas": 1,
    "max_replicas": 5,
    "target_num_ongoing_requests_per_replica": 2,
    "upscale_delay_s": 30,
    "downscale_delay_s": 300
}
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/new-ai-service`
3. **Implement** following the architecture guidelines
4. **Test** thoroughly with the existing Ray cluster
5. **Document** comprehensively
6. **Submit** a pull request

### Service Development Checklist

- [ ] Service follows directory structure
- [ ] Ray Serve deployment implemented
- [ ] Health checks and metrics
- [ ] Auto-scaling configuration
- [ ] Comprehensive tests
- [ ] API documentation
- [ ] Error handling
- [ ] Performance optimization
- [ ] Integration with cluster

## 📄 License

This project is part of the Ray cluster deployment system and follows the same licensing terms.

---

## 🎉 AI Services Ecosystem

The AI services ecosystem provides a scalable, production-ready platform for deploying multiple AI models on the Ray cluster. Each service is designed for:

✅ **High Performance** - Optimized for Ray cluster distribution  
✅ **Auto-scaling** - Responds to load automatically  
✅ **Production Ready** - Monitoring, health checks, error handling  
✅ **Easy Integration** - REST APIs and WebSocket support  
✅ **Comprehensive Testing** - Full test suites and examples  

**Cluster Status**: 5 nodes, 96 CPUs, 500GB+ RAM  
**Current Services**: TTS (Production Ready)  
**Planned Services**: Image Generation, LLM, Computer Vision  

🚀 **Ready for enterprise AI workloads!** 
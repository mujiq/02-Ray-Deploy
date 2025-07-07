# 🚀 AI Services Quick Start

Quick commands for deploying and using AI services on the Ray cluster.

## 🎵 Text-to-Speech (TTS) Service

### Deploy TTS Service
```bash
# Navigate to TTS directory
cd ai-services/tts/

# Deploy with dependency installation
./deployment/deploy_tts.sh --install-deps --port 8000

# Check deployment status
./deployment/deploy_tts.sh --check-cluster
```

### Test TTS Service
```bash
# Run comprehensive test suite
python3 tests/tts_client_examples.py

# Quick health check
curl http://192.168.40.240:8000/health

# Test basic synthesis
curl -X POST http://192.168.40.240:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the refactored TTS service!", "emotion": "happy"}'
```

### Stop TTS Service
```bash
./deployment/deploy_tts.sh --stop-service
```

## 📁 Directory Navigation

### From Project Root
```bash
# Navigate to AI services
cd ai-services/

# Navigate to TTS service
cd ai-services/tts/

# View TTS documentation
cat ai-services/tts/docs/README.md

# Run TTS tests
python3 ai-services/tts/tests/tts_client_examples.py
```

### From TTS Directory
```bash
cd ai-services/tts/

# Deploy service
./deployment/deploy_tts.sh --install-deps

# Run tests  
python3 tests/tts_client_examples.py

# View detailed docs
cat docs/README.md
```

## 🌐 Service URLs

After deployment, services are available at:

- **TTS Service API**: http://192.168.40.240:8000
- **TTS API Documentation**: http://192.168.40.240:8000/docs  
- **TTS WebSocket**: ws://192.168.40.240:8000/ws/tts
- **Health Check**: http://192.168.40.240:8000/health

## 🔄 Deployment Workflow

1. **Navigate to service directory**:
   ```bash
   cd ai-services/tts/
   ```

2. **Deploy with dependencies**:
   ```bash
   ./deployment/deploy_tts.sh --install-deps
   ```

3. **Verify deployment**:
   ```bash
   curl http://192.168.40.240:8000/health
   ```

4. **Run comprehensive tests**:
   ```bash
   python3 tests/tts_client_examples.py
   ```

5. **Use the service**:
   ```bash
   # Basic synthesis
   curl -X POST http://192.168.40.240:8000/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text": "Your text here", "emotion": "neutral"}'
   ```

## 📖 Documentation

- **AI Services Overview**: `ai-services/README.md`
- **TTS Service Overview**: `ai-services/tts/README.md`  
- **TTS Detailed Docs**: `ai-services/tts/docs/README.md`
- **Main Project**: `README.md`

## 🛠️ Development

### Adding New AI Services
```bash
# Create new service structure
mkdir -p ai-services/new-service/{deployment,tests,docs}

# Follow the TTS service as a template
cp -r ai-services/tts/* ai-services/new-service/

# Update service-specific files
# - deployment/deploy_new_service.py
# - deployment/deploy_new_service.sh  
# - tests/new_service_client_examples.py
# - docs/README.md
# - README.md
```

### Testing Changes
```bash
# Test specific service
cd ai-services/service-name/
python3 tests/service_client_examples.py

# Test overall cluster (from project root)
./run_tests.sh --category cluster
```

## 🎯 Common Commands

### Check Ray Cluster Status
```bash
# From any directory
python3 -c "import ray; ray.init(); print(ray.cluster_resources())"
```

### View Service Logs
```bash
# Check Ray dashboard
# http://192.168.40.240:8265

# Check service health
curl http://192.168.40.240:8000/health
```

### Restart Services
```bash
cd ai-services/tts/
./deployment/deploy_tts.sh --stop-service
./deployment/deploy_tts.sh --install-deps
```

---

## ✅ Success Indicators

After deployment, you should see:

- ✅ Health check returns `{"status": "healthy"}`
- ✅ API docs available at `/docs` endpoint
- ✅ Service responds to synthesis requests
- ✅ Ray dashboard shows deployed service
- ✅ Auto-scaling configured (1-5 replicas)

**The refactored AI services are ready for production use!** 🎉 
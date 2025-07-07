# 🎵 Ray TTS Service Deployment

A comprehensive Text-to-Speech (TTS) service deployed on Ray cluster with real-time streaming capabilities, multiple model support, and production-ready features.

## 🌟 Features

### Core Capabilities
- **Real-time Streaming**: Low-latency audio generation with streaming support
- **Multiple TTS Models**: Support for state-of-the-art models from Hugging Face
- **Emotion Control**: Generate speech with different emotional tones
- **Voice Cloning**: Zero-shot voice cloning capabilities (model dependent)
- **WebSocket Streaming**: Real-time bidirectional audio streaming
- **Auto-scaling**: Ray Serve auto-scaling based on load

### Supported Models
1. **Kyutai TTS (1.6B)** - Optimized for streaming, ~200ms latency
2. **Orpheus TTS (3B)** - Human-like quality with emotion control
3. **FastSpeech2** - Fast inference, reliable fallback
4. **F5-TTS** - Flow matching based, high quality (planned)

### Production Features
- **Health Monitoring**: Comprehensive health checks and metrics
- **Batch Processing**: Efficient batch synthesis
- **Multiple Formats**: WAV, MP3, FLAC audio output
- **REST API**: Full REST API with OpenAPI documentation
- **Error Handling**: Robust error handling and fallbacks

## 🚀 Quick Start

### 1. Prerequisites

**Ray Cluster**: Ensure your Ray cluster is running
```bash
# Check cluster status
./deploy_tts.sh --check-cluster
```

**Python Dependencies**: Install required packages
```bash
# Install all dependencies
./deploy_tts.sh --install-deps
```

### 2. Deploy TTS Service

**One-command deployment:**
```bash
# Deploy with defaults (port 8000)
./deploy_tts.sh

# Deploy with custom port and install dependencies
./deploy_tts.sh --install-deps --port 8080
```

**Manual deployment:**
```bash
# Install dependencies
pip install -r requirements_tts.txt

# Deploy service
python3 deploy_tts_service.py --ray-address auto --port 8000
```

### 3. Test the Service

```bash
# Test deployment
./deploy_tts.sh --test-service

# Manual health check
curl http://localhost:8000/health

# Basic synthesis test
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test!", "emotion": "happy"}'
```

## 📡 API Reference

### Base URL
```
http://your-ray-head-ip:8000
```

### Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": ["kyutai", "orpheus", "fastspeech2"],
  "gpu_memory_used": 2.4,
  "uptime": 3600.5
}
```

#### Text Synthesis
```http
POST /synthesize
```

**Request:**
```json
{
  "text": "Hello, world!",
  "voice_id": "default",
  "language": "en",
  "speed": 1.0,
  "emotion": "happy",
  "output_format": "wav"
}
```

**Response:**
```json
{
  "audio_url": "/audio/speech_12345.wav",
  "duration": 2.3,
  "model_used": "kyutai",
  "processing_time": 0.45,
  "voice_id": "default"
}
```

#### Streaming Synthesis
```http
POST /synthesize/stream
```

Returns audio stream directly as binary data.

#### Voice Cloning
```http
POST /voice-clone
```

**Request:**
```json
{
  "text": "Clone this voice",
  "reference_audio_base64": "base64_encoded_audio",
  "reference_text": "Original audio transcript",
  "language": "en"
}
```

#### WebSocket Streaming
```
ws://your-ray-head-ip:8000/ws/tts
```

Send JSON requests and receive binary audio chunks in real-time.

#### List Models
```http
GET /models
```

**Response:**
```json
{
  "available_models": ["kyutai", "orpheus", "fastspeech2"],
  "primary_model": "kyutai",
  "fallback_model": "fastspeech2"
}
```

## 💻 Client Examples

### Python Client
```python
import requests

# Basic synthesis
response = requests.post("http://localhost:8000/synthesize", json={
    "text": "Hello, world!",
    "emotion": "happy",
    "speed": 1.2
})

result = response.json()
print(f"Audio duration: {result['duration']}s")
```

### WebSocket Client
```python
import asyncio
import websockets
import json

async def stream_tts():
    uri = "ws://localhost:8000/ws/tts"
    async with websockets.connect(uri) as websocket:
        # Send request
        await websocket.send(json.dumps({
            "text": "Streaming test",
            "emotion": "neutral"
        }))
        
        # Receive audio chunks
        while True:
            chunk = await websocket.recv()
            if isinstance(chunk, bytes):
                # Process audio chunk
                print(f"Received {len(chunk)} bytes")
            else:
                break

asyncio.run(stream_tts())
```

### cURL Examples
```bash
# Basic synthesis
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from the TTS service!",
    "emotion": "happy",
    "speed": 1.1,
    "voice_id": "professional"
  }'

# Streaming download
curl -X POST http://localhost:8000/synthesize/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Long text for streaming..."}' \
  --output speech.wav

# Health check
curl http://localhost:8000/health | jq

# List available models
curl http://localhost:8000/models | jq
```

## 🔧 Configuration

### Environment Variables
```bash
# Ray cluster settings
export RAY_ADDRESS="ray://head-node:10001"
export RAY_SERVE_HTTP_HOST="0.0.0.0"
export RAY_SERVE_HTTP_PORT="8000"

# Model settings
export TTS_PRIMARY_MODEL="kyutai"
export TTS_FALLBACK_MODEL="fastspeech2"
export TTS_GPU_MEMORY_FRACTION="0.8"

# Performance settings
export TTS_MAX_CONCURRENT_REQUESTS="10"
export TTS_BATCH_SIZE="4"
export TTS_TIMEOUT_SECONDS="30"
```

### Ray Serve Configuration
```python
# Auto-scaling configuration
autoscaling_config = {
    "min_replicas": 1,
    "max_replicas": 5,
    "target_num_ongoing_requests_per_replica": 2,
    "upscale_delay_s": 30,
    "downscale_delay_s": 300
}

# Resource allocation
ray_actor_options = {
    "num_cpus": 2,
    "num_gpus": 0.5,  # Share GPU across replicas
    "memory": 4 * 1024 * 1024 * 1024  # 4GB
}
```

## 📊 Performance & Monitoring

### Expected Performance
- **Latency**: 200-800ms depending on model and text length
- **Throughput**: 10-50 requests/second per replica
- **GPU Memory**: 2-8GB depending on loaded models
- **CPU Usage**: 1-4 cores per replica

### Monitoring Endpoints
- **Health**: `/health` - Service status and resource usage
- **Metrics**: Ray dashboard at `http://ray-head:8265`
- **Logs**: Ray logs and service-specific logs

### Performance Tuning
```python
# For high throughput
autoscaling_config = {
    "min_replicas": 3,
    "max_replicas": 10,
    "target_num_ongoing_requests_per_replica": 1
}

# For low latency
ray_actor_options = {
    "num_cpus": 4,
    "num_gpus": 1.0  # Dedicated GPU per replica
}

# For memory efficiency
model_config = {
    "models_to_load": ["fastspeech2"],  # Load only fast models
    "use_fp16": True,  # Half precision
    "batch_size": 1    # No batching for low latency
}
```

## 🛠️ Development & Testing

### Running Tests
```bash
# Run comprehensive client tests
python3 tts_client_examples.py

# Performance benchmark
python3 -c "
from tts_client_examples import TTSClient, performance_benchmark
client = TTSClient()
results = performance_benchmark(client, num_requests=20)
print(f'Average RPS: {results[\"rps\"]:.2f}')
"

# Emotion testing
python3 -c "
from tts_client_examples import TTSClient, emotion_testing_example
client = TTSClient()
emotion_testing_example(client)
"
```

### Adding New Models
1. **Create Model Class**: Inherit from `BaseTTSModel`
2. **Implement Methods**: `_load_model_impl()` and `synthesize()`
3. **Register Model**: Add to model loading in `TTSService.load_models()`
4. **Update Configuration**: Add to requirements and documentation

Example:
```python
class NewTTSModel(BaseTTSModel):
    def __init__(self):
        super().__init__("new-model")
        self.sample_rate = 22050
    
    async def _load_model_impl(self):
        # Load your model here
        pass
    
    async def synthesize(self, text: str, **kwargs) -> np.ndarray:
        # Implement synthesis logic
        pass
```

## 🚀 Deployment Scenarios

### Single Node Deployment
```bash
# For development/testing
./deploy_tts.sh --ray-address auto --port 8000
```

### Multi-Node Cluster
```bash
# Deploy on head node
./deploy_tts.sh --ray-address ray://head-node:10001 --port 8000

# Service will auto-scale across worker nodes
```

### Production Deployment
```bash
# With monitoring and error handling
./deploy_tts.sh \
  --ray-address ray://head-node:10001 \
  --port 8000 \
  --install-deps

# Setup reverse proxy (nginx)
server {
    listen 80;
    server_name tts.yourdomain.com;
    
    location / {
        proxy_pass http://ray-head:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://ray-head:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_tts.txt .
RUN pip install -r requirements_tts.txt

# Copy application
COPY deploy_tts_service.py .
COPY tts_client_examples.py .

# Expose port
EXPOSE 8000

# Run service
CMD ["python3", "deploy_tts_service.py", "--ray-address", "auto", "--port", "8000"]
```

## 🔍 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check Ray cluster
./deploy_tts.sh --check-cluster

# Check dependencies
pip install -r requirements_tts.txt

# Check logs
tail -f tts_service.log
```

#### Out of Memory
```bash
# Reduce model size or use CPU
export CUDA_VISIBLE_DEVICES=""

# Reduce batch size
export TTS_BATCH_SIZE="1"

# Use smaller models
export TTS_PRIMARY_MODEL="fastspeech2"
```

#### Poor Performance
```bash
# Increase replicas
# Edit autoscaling_config in deploy_tts_service.py

# Use GPU acceleration
nvidia-smi  # Check GPU availability

# Optimize model loading
# Load only required models
```

#### Network Issues
```bash
# Check port availability
netstat -tlnp | grep 8000

# Check firewall
sudo ufw status

# Test connectivity
curl -v http://localhost:8000/health
```

### Debug Mode
```bash
# Enable verbose logging
export RAY_LOG_LEVEL="DEBUG"
export TTS_LOG_LEVEL="DEBUG"

# Run with debug
python3 deploy_tts_service.py --ray-address auto --port 8000 --verbose
```

## 📚 API Documentation

Full interactive API documentation is available at:
```
http://your-ray-head-ip:8000/docs
```

This provides:
- Complete endpoint documentation
- Request/response schemas
- Interactive testing interface
- Example requests and responses

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/new-model`
3. **Implement** your changes
4. **Test** thoroughly: `python3 tts_client_examples.py`
5. **Document** your changes
6. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Kyutai** for the streaming TTS model
- **Canopy Labs** for Orpheus TTS
- **Facebook/Meta** for FastSpeech2
- **Ray Team** for the excellent serving framework
- **Hugging Face** for model hosting and transformers library

---

## 🎉 Success! Your TTS Service is Ready!

You now have a production-ready Text-to-Speech service running on your Ray cluster with:

✅ **Multiple State-of-the-Art Models**  
✅ **Real-time Streaming Capabilities**  
✅ **Emotion and Voice Control**  
✅ **Auto-scaling and Load Balancing**  
✅ **Comprehensive API and WebSocket Support**  
✅ **Production Monitoring and Health Checks**  

**Service URL**: `http://your-ray-head-ip:8000`  
**API Docs**: `http://your-ray-head-ip:8000/docs`  
**WebSocket**: `ws://your-ray-head-ip:8000/ws/tts`  

🚀 **Ready for production workloads and real-time applications!** 
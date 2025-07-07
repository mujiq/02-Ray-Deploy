# 🎵 Text-to-Speech (TTS) Service

A production-ready Text-to-Speech service for Ray cluster deployment with real-time streaming capabilities and multiple state-of-the-art models.

## 🌟 Overview

This TTS service provides:
- **Real-time streaming** audio generation
- **Multiple models** (Kyutai, Orpheus, FastSpeech2)
- **Emotion control** (happy, sad, angry, neutral)
- **Voice cloning** capabilities
- **Auto-scaling** with Ray Serve
- **WebSocket streaming** support

## 📁 Directory Structure

```
ai-services/tts/
├── deployment/           # Deployment scripts and configurations
│   ├── deploy_tts_service.py    # Main TTS service (Ray Serve)
│   ├── deploy_tts.sh            # Automated deployment script
│   └── requirements_tts.txt     # Python dependencies
├── tests/               # Testing and client examples
│   └── tts_client_examples.py   # Comprehensive test suite
├── docs/                # Documentation
│   └── README.md               # Detailed documentation
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Deploy the Service
```bash
# From the ai-services/tts/ directory
cd ai-services/tts/

# One-command deployment
./deployment/deploy_tts.sh

# Or with dependency installation
./deployment/deploy_tts.sh --install-deps --port 8000
```

### 2. Test the Service
```bash
# Run comprehensive tests
python3 tests/tts_client_examples.py

# Quick health check
curl http://localhost:8000/health

# Basic synthesis test
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from TTS service!", "emotion": "happy"}'
```

## 📚 Documentation

For detailed documentation, deployment guides, API reference, and examples, see:
- **[Complete Documentation](docs/README.md)** - Full deployment and usage guide
- **[API Reference](docs/README.md#-api-reference)** - REST API endpoints
- **[Examples](docs/README.md#-client-examples)** - Client usage examples
- **[Troubleshooting](docs/README.md#-troubleshooting)** - Common issues and solutions

## 🎯 Key Features

### Supported Models
1. **Kyutai TTS (1.6B)** - Streaming optimized, ~200ms latency
2. **Orpheus TTS (3B)** - Human-like quality with emotion control
3. **FastSpeech2** - Fast inference, reliable fallback

### API Endpoints
- `POST /synthesize` - Text-to-speech synthesis
- `POST /synthesize/stream` - Streaming audio generation
- `POST /voice-clone` - Voice cloning (model dependent)
- `GET /health` - Service health and metrics
- `WS /ws/tts` - WebSocket streaming

### Production Features
- **Auto-scaling**: 1-5 replicas based on load
- **Health monitoring**: Comprehensive metrics
- **Error handling**: Robust fallbacks
- **Multiple formats**: WAV, MP3, FLAC output

## 🛠️ Development

### Prerequisites
- Ray cluster running (Python 3.9+ recommended)
- GPU support (optional but recommended)
- Dependencies from `deployment/requirements_tts.txt`

### Local Development
```bash
# Install dependencies
pip install -r deployment/requirements_tts.txt

# Run service locally
python3 deployment/deploy_tts_service.py --ray-address auto

# Test with examples
python3 tests/tts_client_examples.py
```

### Adding New Models
1. Create model class inheriting from `BaseTTSModel`
2. Implement `_load_model_impl()` and `synthesize()` methods
3. Register in `TTSService.load_models()`
4. Update requirements and documentation

## 📊 Performance

- **Latency**: 200-800ms per request
- **Throughput**: 10-50 requests/second per replica
- **GPU Memory**: 2-8GB depending on models
- **Auto-scaling**: Responds to load automatically

## 🌐 Integration

The TTS service integrates seamlessly with:
- **Web applications** via REST API
- **Real-time applications** via WebSocket
- **Mobile apps** via HTTP streaming
- **Voice assistants** via batch processing
- **Content platforms** via emotion control

## 🔧 Configuration

Service configuration can be adjusted via:
- Environment variables
- Command-line arguments
- Ray Serve deployment config
- Model-specific parameters

See the [detailed documentation](docs/README.md#-configuration) for all options.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Test thoroughly with `tests/tts_client_examples.py`
4. Update documentation as needed
5. Submit pull request

## 📄 License

This project is part of the Ray cluster deployment system and follows the same licensing terms.

---

## 🎉 Ready to Deploy!

Your TTS service is ready for production deployment on the Ray cluster. For complete setup instructions and API documentation, see the [detailed documentation](docs/README.md).

**Service will be available at**: `http://your-ray-head-ip:8000`  
**API Documentation**: `http://your-ray-head-ip:8000/docs`  
**WebSocket Endpoint**: `ws://your-ray-head-ip:8000/ws/tts` 
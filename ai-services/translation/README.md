# 🌐 Translation Service

Enterprise-grade text translation service with 200+ language support, deployed on Ray cluster with redundancy and auto-scaling.

## 🌟 Overview

This translation service provides:
- **200+ languages** supported across three state-of-the-art models
- **Multi-model architecture** with automatic selection and failover
- **Redundancy** with warm replicas across Ray cluster nodes
- **Auto-scaling** from 2-8 replicas based on demand
- **Language detection** with confidence scores
- **High availability** with intelligent failover between models

## 📁 Directory Structure

```
ai-services/translation/
├── deployment/              # Deployment scripts and configurations
│   ├── translation_service.py     # Main translation service (Ray Serve)
│   ├── deploy_translation.sh      # Automated deployment script
│   └── requirements_translation.txt  # Python dependencies
├── tests/                   # Testing and validation
│   └── translation_client_examples.py  # Comprehensive test suite
├── docs/                    # Detailed documentation
│   └── README.md           # Complete API and deployment guide
└── README.md               # This overview (you are here)
```

## 🚀 Quick Start

### 1. Deploy Translation Service
```bash
# Navigate to translation directory
cd ai-services/translation/

# Deploy with dependency installation
./deployment/deploy_translation.sh --install-deps --port 8001

# Check deployment status
./deployment/deploy_translation.sh --status
```

### 2. Test Translation Service
```bash
# Run comprehensive test suite
python3 tests/translation_client_examples.py

# Quick health check
curl http://192.168.40.240:8001/health

# Test basic translation
curl -X POST http://192.168.40.240:8001/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you today?",
    "source_lang": "en",
    "target_lang": "es"
  }'
```

## 🤖 Available Models

### 1. **NLLB-200** (Meta)
- **200+ languages** including low-resource languages
- **2-4 replicas** with auto-scaling
- **Best for**: Maximum language coverage, rare language pairs

### 2. **UMT5-XXL** (Google)  
- **107 languages** with excellent quality
- **1-3 replicas** with auto-scaling
- **Best for**: Balanced performance and quality

### 3. **Babel-83B** (Tower)
- **25 languages** with highest quality
- **1-2 replicas** with auto-scaling  
- **Best for**: Premium quality for supported languages

## 🔗 Key Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `POST /translate` | Translate text between languages | `{"text": "Hello", "source_lang": "en", "target_lang": "es"}` |
| `POST /detect-language` | Detect language of input text | `{"text": "Bonjour le monde"}` |
| `GET /languages` | List supported languages by model | Returns language codes and counts |
| `GET /models` | Get model information and capabilities | Returns model details and specializations |
| `GET /health` | Service health and performance metrics | Returns status and statistics |

## 📊 Performance Characteristics

**Expected Latency (95th percentile):**
- NLLB-200: 200-500ms
- UMT5-XXL: 300-800ms  
- Babel-83B: 500-1200ms
- Language Detection: 50-150ms

**Throughput (per replica):**
- NLLB-200: 10-25 RPS
- UMT5-XXL: 5-15 RPS
- Babel-83B: 2-8 RPS

**Resource Requirements:**
- **Minimum**: 16 CPUs, 4 GB GPU memory, 32 GB RAM
- **Optimal**: 32+ CPUs, 8+ GB GPU memory, 64+ GB RAM

## 🌍 Language Support Examples

**Major Languages**: English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, and 180+ more

**Regional Languages**: Bengali, Gujarati, Tamil, Telugu, Swahili, Yoruba, Hausa, Indonesian, Vietnamese, Thai, and many others

**Low-Resource Languages**: Over 50 languages with limited digital resources, supported by NLLB-200

## 🛡️ Redundancy & Failover

The service implements multi-level redundancy:

1. **Model-Level**: Multiple replicas per model across different nodes
2. **Service-Level**: Automatic failover between models if primary fails
3. **Cluster-Level**: Ray handles node failures and replica redistribution

**Failover Order**: Optimal Model → Alternative Model → Fallback Model → Error Response

## 🔧 Management Commands

```bash
# Service management
./deployment/deploy_translation.sh --status      # Check status
./deployment/deploy_translation.sh --logs        # View logs  
./deployment/deploy_translation.sh --stop        # Stop service
./deployment/deploy_translation.sh --restart     # Restart service

# Testing
python3 tests/translation_client_examples.py --quick        # Quick tests
python3 tests/translation_client_examples.py --benchmark-only  # Performance only
```

## 📚 Documentation

- **Complete Documentation**: [`docs/README.md`](docs/README.md)
- **API Reference**: `http://192.168.40.240:8001/docs`
- **Model Details**: `http://192.168.40.240:8001/models`
- **Service Health**: `http://192.168.40.240:8001/health`

## 🔗 Integration with Other Services

This translation service is designed to integrate with other AI services:

- **TTS Service**: Translate → Text-to-Speech pipeline
- **Future ASR Service**: Speech → Translation → Speech pipeline
- **Future Vision Service**: Image text translation
- **Enterprise APIs**: Multi-language content processing

## ⚡ Quick Examples

### Python
```python
import requests

response = requests.post("http://192.168.40.240:8001/translate", json={
    "text": "Artificial intelligence is transforming the world",
    "source_lang": "en",
    "target_lang": "zh",
    "model": "auto"
})
print(response.json()["translated_text"])
```

### cURL
```bash
curl -X POST http://192.168.40.240:8001/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "source_lang": "en", "target_lang": "fr"}'
```

### JavaScript
```javascript
const response = await fetch("http://192.168.40.240:8001/translate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        text: "Good morning!",
        source_lang: "en", 
        target_lang: "de"
    })
});
const result = await response.json();
console.log(result.translated_text);
```

---

**🚀 Ready to translate the world!** For detailed documentation, deployment guides, and advanced features, see [`docs/README.md`](docs/README.md). 
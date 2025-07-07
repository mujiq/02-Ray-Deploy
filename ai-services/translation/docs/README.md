# 🌐 Enterprise Translation Service Documentation

**Multi-model translation service with 200+ language support, redundancy, and auto-scaling**

---

## 🌟 Overview

The Enterprise Translation Service provides state-of-the-art text translation capabilities using three powerful models deployed on Ray cluster infrastructure. The service offers automatic model selection, redundancy, failover, and supports over 200 languages with real-time processing.

### 🎯 Key Features

- **200+ Language Support**: Comprehensive coverage from major world languages to low-resource languages
- **Multi-Model Architecture**: Three specialized models optimized for different use cases
- **Automatic Model Selection**: Intelligent routing based on language pairs and quality requirements
- **Redundancy & Failover**: Warm replicas across cluster nodes with automatic failover
- **Auto-Scaling**: Dynamic scaling from 2-8 replicas based on load
- **Language Detection**: Automatic language identification with confidence scores
- **Quality Control**: Multiple quality levels (fast, balanced, high)
- **Performance Monitoring**: Real-time health checks and performance metrics

---

## 🤖 Translation Models

### 1. **NLLB-200** (Meta)
- **Languages**: 200+ languages including low-resource languages
- **Best For**: Maximum language coverage, rare language pairs
- **Specialization**: State-of-the-art quality for multilingual translation
- **Resource Usage**: 2 CPUs, 0.5 GPU per replica
- **Replicas**: 2-4 (auto-scaling)

### 2. **UMT5-XXL** (Google)
- **Languages**: 107 languages with excellent coverage
- **Best For**: Balanced quality and performance for common languages
- **Specialization**: Excellent multilingual capabilities with good speed
- **Resource Usage**: 4 CPUs, 1 GPU per replica
- **Replicas**: 1-3 (auto-scaling)

### 3. **Babel-83B** (Tower)
- **Languages**: 25 languages (highest quality subset)
- **Best For**: Maximum translation quality for supported languages
- **Specialization**: Highest quality translations with advanced reasoning
- **Resource Usage**: 6 CPUs, 1 GPU per replica
- **Replicas**: 1-2 (auto-scaling)

---

## 📚 API Reference

### Base URL
```
http://192.168.40.240:8001
```

### Authentication
Currently no authentication required. For production deployment, implement API keys or OAuth.

---

## 🔗 Endpoints

### 1. **Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": ["nllb-200", "umt5-xxl", "babel-83b"],
  "total_requests": 1547,
  "average_latency": 0.743,
  "error_rate": 0.02
}
```

### 2. **Text Translation**
```http
POST /translate
```

**Request Body:**
```json
{
  "text": "Hello, how are you today?",
  "source_lang": "en",
  "target_lang": "es",
  "model": "auto",
  "quality": "balanced"
}
```

**Parameters:**
- `text` (string, required): Text to translate (max 10,000 characters)
- `source_lang` (string, required): Source language code (ISO 639-1)
- `target_lang` (string, required): Target language code (ISO 639-1)
- `model` (string, optional): Model selection (`auto`, `nllb-200`, `umt5-xxl`, `babel-83b`)
- `quality` (string, optional): Quality level (`fast`, `balanced`, `high`)

**Response:**
```json
{
  "translated_text": "Hola, ¿cómo estás hoy?",
  "source_lang": "en",
  "target_lang": "es",
  "model_used": "nllb-200",
  "confidence": 0.95,
  "processing_time": 0.234
}
```

### 3. **Language Detection**
```http
POST /detect-language
```

**Request Body:**
```json
{
  "text": "Bonjour, comment allez-vous?"
}
```

**Response:**
```json
{
  "detected_language": "fr",
  "confidence": 0.98,
  "alternatives": [
    {"language": "fr", "confidence": 0.98},
    {"language": "it", "confidence": 0.15},
    {"language": "es", "confidence": 0.08}
  ]
}
```

### 4. **Supported Languages**
```http
GET /languages
```

**Response:**
```json
{
  "nllb_200": {
    "count": 200,
    "languages": ["en", "es", "fr", "de", "zh", "ar", "hi", "..."]
  },
  "umt5_xxl": {
    "count": 107,
    "languages": ["en", "es", "fr", "de", "zh", "ar", "..."]
  },
  "babel_83b": {
    "count": 25,
    "languages": ["en", "zh", "hi", "es", "ar", "fr", "..."]
  }
}
```

### 5. **Model Information**
```http
GET /models
```

**Response:**
```json
{
  "models": [
    {
      "name": "nllb-200",
      "description": "Meta NLLB-200: 200+ languages, state-of-the-art quality",
      "languages": 200,
      "best_for": "Maximum language coverage, low-resource languages"
    },
    {
      "name": "umt5-xxl",
      "description": "Google UMT5-XXL: 107 languages, excellent multilingual capabilities",
      "languages": 107,
      "best_for": "Balanced quality and coverage"
    },
    {
      "name": "babel-83b",
      "description": "Tower Babel-83B: 25 languages, highest quality translations",
      "languages": 25,
      "best_for": "Maximum quality for supported languages"
    }
  ]
}
```

---

## 🚀 Quick Start Guide

### 1. **Deploy the Service**
```bash
cd ai-services/translation/
./deployment/deploy_translation.sh --install-deps --port 8001
```

### 2. **Basic Translation**
```bash
curl -X POST http://192.168.40.240:8001/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "source_lang": "en",
    "target_lang": "es"
  }'
```

### 3. **Language Detection**
```bash
curl -X POST http://192.168.40.240:8001/detect-language \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour le monde!"}'
```

### 4. **Health Check**
```bash
curl http://192.168.40.240:8001/health
```

---

## 💻 Code Examples

### Python Client
```python
import requests

class TranslationClient:
    def __init__(self, base_url="http://192.168.40.240:8001"):
        self.base_url = base_url
    
    def translate(self, text, source_lang, target_lang, model="auto", quality="balanced"):
        response = requests.post(f"{self.base_url}/translate", json={
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "model": model,
            "quality": quality
        })
        return response.json()
    
    def detect_language(self, text):
        response = requests.post(f"{self.base_url}/detect-language", json={
            "text": text
        })
        return response.json()

# Usage
client = TranslationClient()

# Translate text
result = client.translate("Hello world", "en", "es")
print(f"Translation: {result['translated_text']}")

# Detect language
detection = client.detect_language("Hola mundo")
print(f"Detected: {detection['detected_language']}")
```

### JavaScript/Node.js Client
```javascript
class TranslationClient {
    constructor(baseUrl = "http://192.168.40.240:8001") {
        this.baseUrl = baseUrl;
    }
    
    async translate(text, sourceLang, targetLang, model = "auto", quality = "balanced") {
        const response = await fetch(`${this.baseUrl}/translate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                source_lang: sourceLang,
                target_lang: targetLang,
                model,
                quality
            })
        });
        return response.json();
    }
    
    async detectLanguage(text) {
        const response = await fetch(`${this.baseUrl}/detect-language`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        return response.json();
    }
}

// Usage
const client = new TranslationClient();

client.translate("Hello world", "en", "fr")
    .then(result => console.log(`Translation: ${result.translated_text}`));
```

### cURL Examples
```bash
# High-quality translation with specific model
curl -X POST http://192.168.40.240:8001/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The future of artificial intelligence is bright.",
    "source_lang": "en",
    "target_lang": "zh",
    "model": "babel-83b",
    "quality": "high"
  }'

# Batch language detection
curl -X POST http://192.168.40.240:8001/detect-language \
  -H "Content-Type: application/json" \
  -d '{"text": "Machine learning is revolutionizing industries worldwide."}'

# Get supported languages for specific model
curl http://192.168.40.240:8001/languages | jq '.nllb_200.languages'
```

---

## 🏗️ Architecture & Deployment

### Cluster Resource Allocation

**Recommended Cluster Setup:**
- **Minimum**: 16 CPUs, 4 GB GPU memory, 32 GB RAM
- **Optimal**: 32+ CPUs, 8+ GB GPU memory, 64+ GB RAM
- **Nodes**: 3+ worker nodes for redundancy

**Resource Distribution:**
```
NLLB-200:    2 CPUs × 2-4 replicas = 4-8 CPUs
UMT5-XXL:    4 CPUs × 1-3 replicas = 4-12 CPUs  
Babel-83B:   6 CPUs × 1-2 replicas = 6-12 CPUs
Language Detection: 1 CPU × 1-2 replicas = 1-2 CPUs
Service Controller: 1 CPU × 1 replica = 1 CPU
----------------------------------------------------
Total: 16-35 CPUs, 2-6 GPUs
```

### Auto-Scaling Configuration

The service implements intelligent auto-scaling based on:
- **Request Queue Length**: Scales up when queue exceeds target per replica
- **CPU/GPU Utilization**: Scales when resource usage > 80%
- **Response Time**: Scales up when latency > SLA thresholds
- **Model Performance**: Adjusts replica count per model based on usage patterns

**Scaling Parameters:**
```python
# NLLB-200 (High throughput, moderate resources)
target_requests_per_replica: 3
min_replicas: 2
max_replicas: 4
upscale_delay: 10s
downscale_delay: 30s

# UMT5-XXL (Balanced throughput and quality)
target_requests_per_replica: 2
min_replicas: 1
max_replicas: 3
upscale_delay: 15s
downscale_delay: 45s

# Babel-83B (Lower throughput, highest quality)
target_requests_per_replica: 1
min_replicas: 1
max_replicas: 2
upscale_delay: 20s
downscale_delay: 60s
```

### Redundancy & Failover

**Multi-Level Redundancy:**
1. **Model-Level**: Each model has multiple replicas across different nodes
2. **Service-Level**: Automatic failover between models if primary fails
3. **Cluster-Level**: Ray handles node failures and replica redistribution

**Failover Strategy:**
```
Primary Request → NLLB-200 (if optimal for language pair)
      ↓ (if fails)
Fallback 1 → UMT5-XXL (if supports language pair)
      ↓ (if fails)  
Fallback 2 → Babel-83B (if supports language pair)
      ↓ (if fails)
Error Response with detailed failure information
```

---

## 🎯 Performance & Optimization

### Expected Performance Metrics

**Latency (95th percentile):**
- **NLLB-200**: 200-500ms per request
- **UMT5-XXL**: 300-800ms per request
- **Babel-83B**: 500-1200ms per request
- **Language Detection**: 50-150ms per request

**Throughput (per replica):**
- **NLLB-200**: 10-25 RPS
- **UMT5-XXL**: 5-15 RPS
- **Babel-83B**: 2-8 RPS
- **Language Detection**: 50-100 RPS

**Memory Usage:**
- **NLLB-200**: ~4-6 GB per replica
- **UMT5-XXL**: ~8-12 GB per replica
- **Babel-83B**: ~15-25 GB per replica

### Optimization Strategies

**1. Quality vs Speed Trade-offs:**
```json
{
  "quality": "fast",     // Faster inference, good quality
  "quality": "balanced", // Default, balanced speed/quality
  "quality": "high"      // Slower inference, best quality
}
```

**2. Model Selection:**
- Use `babel-83b` for critical translations requiring highest quality
- Use `umt5-xxl` for balanced performance across many languages
- Use `nllb-200` for maximum language coverage including rare languages
- Use `auto` for intelligent selection based on language pair

**3. Batch Processing:**
```python
# Process multiple translations efficiently
def batch_translate(texts, source_lang, target_lang):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(client.translate, text, source_lang, target_lang)
            for text in texts
        ]
        return [future.result() for future in futures]
```

---

## 🌍 Language Support

### Comprehensive Language Coverage

**Major Language Families Supported:**
- **Indo-European**: English, Spanish, French, German, Italian, Portuguese, Russian, Hindi, etc.
- **Sino-Tibetan**: Chinese (Simplified/Traditional), Burmese, Tibetan
- **Afroasiatic**: Arabic, Hebrew, Amharic, Hausa
- **Niger-Congo**: Swahili, Yoruba, Igbo, Zulu
- **Austronesian**: Indonesian, Malay, Tagalog, Javanese
- **Trans-New Guinea**: Over 300 Papua New Guinea languages
- **And Many More**: Including constructed languages, historical languages, and regional dialects

### Language Code Standards

The service uses **ISO 639-1** two-letter codes where available, falling back to **ISO 639-3** for languages without two-letter codes.

**Common Language Codes:**
```
en - English          es - Spanish          fr - French
de - German           it - Italian          pt - Portuguese  
ru - Russian          ja - Japanese         ko - Korean
zh - Chinese          ar - Arabic           hi - Hindi
tr - Turkish          pl - Polish           nl - Dutch
sv - Swedish          da - Danish           no - Norwegian
fi - Finnish          el - Greek            cs - Czech
hu - Hungarian        ro - Romanian         bg - Bulgarian
hr - Croatian         sk - Slovak           sl - Slovenian
et - Estonian         lv - Latvian          lt - Lithuanian
uk - Ukrainian        be - Belarusian       mk - Macedonian
sq - Albanian         sr - Serbian          bs - Bosnian
mt - Maltese          is - Icelandic        ga - Irish
cy - Welsh            eu - Basque           ca - Catalan
gl - Galician         th - Thai             vi - Vietnamese
id - Indonesian       ms - Malay            tl - Tagalog
sw - Swahili          am - Amharic          yo - Yoruba
ig - Igbo             ha - Hausa            zu - Zulu
af - Afrikaans        bn - Bengali          gu - Gujarati
kn - Kannada          ml - Malayalam        mr - Marathi
ne - Nepali           or - Odia             pa - Punjabi
si - Sinhala          ta - Tamil            te - Telugu
ur - Urdu             fa - Persian          ps - Pashto
uz - Uzbek            ky - Kyrgyz           kk - Kazakh
tg - Tajik            mn - Mongolian        my - Burmese
km - Khmer            lo - Lao              ka - Georgian
az - Azerbaijani      hy - Armenian         he - Hebrew
```

---

## 🔧 Configuration & Customization

### Environment Variables

```bash
# Service Configuration
TRANSLATION_SERVICE_PORT=8001
TRANSLATION_SERVICE_HOST=0.0.0.0
RAY_CLUSTER_ADDRESS=ray://192.168.40.240:10001

# Model Configuration
NLLB_MODEL_PATH=facebook/nllb-200-3.3B
UMT5_MODEL_PATH=google/umt5-xxl
BABEL_MODEL_PATH=Tower-Babel/Babel-83B

# Performance Tuning
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
MODEL_CACHE_SIZE=5
GPU_MEMORY_FRACTION=0.8

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/translation-service.log
METRICS_ENABLED=true
```

### Custom Model Configuration

```python
# Add custom model configuration
CUSTOM_MODEL_CONFIG = {
    "name": "custom-translator",
    "model_path": "path/to/custom/model",
    "languages": ["en", "custom_lang"],
    "max_length": 512,
    "device": "cuda",
    "load_in_8bit": True,
    "torch_dtype": "float16"
}
```

---

## 📊 Monitoring & Observability

### Health Monitoring

**Health Check Endpoint**: `/health`
- Service status (healthy/degraded/unhealthy)
- Model loading status
- Request statistics
- Performance metrics
- Error rates

**Metrics Collection:**
- Request count and rate
- Response time percentiles
- Error rate by endpoint
- Model utilization
- Resource usage (CPU/GPU/Memory)
- Queue depth and processing time

### Logging

**Log Levels:**
- `ERROR`: Service errors, model failures
- `WARN`: Degraded performance, fallback usage
- `INFO`: Service lifecycle, model loading, request summaries
- `DEBUG`: Detailed request/response data

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "service": "translation-service",
  "model": "nllb-200",
  "request_id": "req_123456",
  "source_lang": "en",
  "target_lang": "es",
  "processing_time": 0.245,
  "text_length": 156,
  "confidence": 0.95
}
```

### Integration with Monitoring Stack

**Prometheus Metrics:**
```
# Counter metrics
translation_requests_total{model="nllb-200", source_lang="en", target_lang="es"}
translation_errors_total{model="nllb-200", error_type="timeout"}

# Histogram metrics  
translation_duration_seconds{model="nllb-200"}
translation_text_length_chars{model="nllb-200"}

# Gauge metrics
translation_active_replicas{model="nllb-200"}
translation_queue_depth{model="nllb-200"}
```

**Grafana Dashboard Queries:**
```promql
# Average response time
rate(translation_duration_seconds_sum[5m]) / rate(translation_duration_seconds_count[5m])

# Request rate by model
sum(rate(translation_requests_total[5m])) by (model)

# Error rate
sum(rate(translation_errors_total[5m])) / sum(rate(translation_requests_total[5m]))
```

---

## 🚨 Troubleshooting

### Common Issues

**1. Service Not Responding**
```bash
# Check service status
./deployment/deploy_translation.sh --status

# Check logs
./deployment/deploy_translation.sh --logs

# Restart service
./deployment/deploy_translation.sh --restart
```

**2. High Latency**
```bash
# Check cluster resources
curl http://192.168.40.240:8001/health

# Increase replicas by redeploying
./deployment/deploy_translation.sh --install-deps
```

**3. Translation Quality Issues**
```python
# Try different model
{
  "text": "Your text here",
  "source_lang": "en", 
  "target_lang": "es",
  "model": "babel-83b",  # Use highest quality model
  "quality": "high"      # Use highest quality setting
}
```

**4. Memory Issues**
```bash
# Monitor GPU memory
nvidia-smi

# Check Ray cluster resources  
ray status

# Restart with memory optimization
export GPU_MEMORY_FRACTION=0.6
./deployment/deploy_translation.sh --restart
```

### Error Codes

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `422`: Validation Error (invalid input format)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error
- `503`: Service Unavailable (overloaded)
- `504`: Gateway Timeout (request timeout)

**Custom Error Codes:**
```json
{
  "error_code": "TRANSLATION_001",
  "error_type": "UnsupportedLanguagePair", 
  "message": "Language pair 'xyz' to 'abc' not supported by any model",
  "suggested_action": "Check /languages endpoint for supported language codes"
}
```

### Performance Tuning

**1. Optimize for Latency:**
```json
{
  "quality": "fast",
  "model": "nllb-200"  // Fastest model
}
```

**2. Optimize for Quality:**
```json
{
  "quality": "high",
  "model": "babel-83b"  // Highest quality model
}
```

**3. Optimize for Throughput:**
- Increase replica count
- Use async/batch processing
- Enable connection pooling
- Optimize text length

---

## 🔮 Future Enhancements

### Planned Features

**Q1 2024:**
- [ ] Real-time streaming translation
- [ ] Document translation with formatting preservation
- [ ] Translation memory and caching
- [ ] Custom model fine-tuning API

**Q2 2024:**
- [ ] Multi-modal translation (image + text)
- [ ] Voice translation pipeline integration
- [ ] Advanced quality metrics and BLEU scoring
- [ ] A/B testing framework for models

**Q3 2024:**
- [ ] Federated learning for custom domains
- [ ] Edge deployment for low-latency use cases
- [ ] Advanced security and privacy features
- [ ] Cost optimization and model compression

### Integration Roadmap

**Planned Integrations:**
- **Existing TTS Service**: Voice translation pipeline
- **Future Vision Service**: Image text translation
- **Future ASR Service**: Speech-to-speech translation
- **Enterprise Systems**: SAP, Salesforce, etc.

---

## 📞 Support & Contact

### Getting Help

**Documentation**: This README and `/docs` endpoint
**API Documentation**: `http://192.168.40.240:8001/docs`
**Health Monitoring**: `http://192.168.40.240:8001/health`

### Reporting Issues

**Performance Issues**: Include `/health` response and request details
**Quality Issues**: Include source text, target text, and expected output
**Service Issues**: Include logs from `./deployment/deploy_translation.sh --logs`

---

## 📄 License & Attribution

**Service License**: Enterprise internal use
**Model Licenses**: 
- NLLB-200: MIT License (Meta)
- UMT5-XXL: Apache 2.0 (Google) 
- Babel-83B: Apache 2.0 (Tower)

**Dependencies**: See `requirements_translation.txt` for full dependency list

---

*Built with ❤️ for the Ray cluster ecosystem* 
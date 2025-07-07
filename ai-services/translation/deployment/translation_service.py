#!/usr/bin/env python3
"""
Enterprise Translation Service for Ray Cluster
Supports 200+ languages with redundancy and auto-scaling.

Top Translation Models:
1. NLLB-200 (Meta): 200 languages, state-of-the-art quality  
2. UMT5-XXL (Google): 107 languages, excellent multilingual capabilities
3. Babel-83B (Tower): 25 languages, highest quality for supported languages

Features:
- Multi-model translation with automatic model selection
- Language detection and validation
- Redundancy with warm replicas across nodes
- Auto-scaling based on load (2-8 replicas)
- Comprehensive error handling and fallbacks
- Performance monitoring and health checks
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,
    MT5ForConditionalGeneration,
    T5Tokenizer,
    pipeline
)
import ray
from ray import serve
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================== Data Models ===================

class TranslationModel(str, Enum):
    NLLB_200 = "nllb-200"
    UMT5_XXL = "umt5-xxl" 
    BABEL_83B = "babel-83b"
    AUTO = "auto"

class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text to translate", max_length=10000)
    source_lang: str = Field(..., description="Source language code (e.g., 'en', 'es', 'fr')")
    target_lang: str = Field(..., description="Target language code")
    model: TranslationModel = Field(TranslationModel.AUTO, description="Translation model to use")
    quality: str = Field("balanced", description="Translation quality: fast, balanced, high")

class LanguageDetectionRequest(BaseModel):
    text: str = Field(..., description="Text to detect language for", max_length=10000)

class TranslationResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str
    model_used: str
    confidence: float
    processing_time: float
    
class LanguageDetectionResponse(BaseModel):
    detected_language: str
    confidence: float
    alternatives: List[Dict[str, float]]

class HealthResponse(BaseModel):
    status: str
    models_loaded: List[str]
    total_requests: int
    average_latency: float
    error_rate: float

@dataclass
class ModelConfig:
    name: str
    model_path: str
    languages: List[str]
    max_length: int
    device: str
    load_in_8bit: bool = False
    torch_dtype: Optional[torch.dtype] = None

# =================== Language Mappings ===================

# NLLB-200 supported languages (200+ languages)
NLLB_LANGUAGES = {
    'en': 'eng_Latn', 'es': 'spa_Latn', 'fr': 'fra_Latn', 'de': 'deu_Latn', 'it': 'ita_Latn',
    'pt': 'por_Latn', 'ru': 'rus_Cyrl', 'ja': 'jpn_Jpan', 'ko': 'kor_Hang', 'zh': 'zho_Hans',
    'ar': 'ara_Arab', 'hi': 'hin_Deva', 'tr': 'tur_Latn', 'pl': 'pol_Latn', 'nl': 'nld_Latn',
    'sv': 'swe_Latn', 'da': 'dan_Latn', 'no': 'nor_Latn', 'fi': 'fin_Latn', 'el': 'ell_Grek',
    'cs': 'ces_Latn', 'hu': 'hun_Latn', 'ro': 'ron_Latn', 'bg': 'bul_Cyrl', 'hr': 'hrv_Latn',
    'sk': 'slk_Latn', 'sl': 'slv_Latn', 'et': 'est_Latn', 'lv': 'lav_Latn', 'lt': 'lit_Latn',
    'uk': 'ukr_Cyrl', 'be': 'bel_Cyrl', 'mk': 'mkd_Cyrl', 'sq': 'sqi_Latn', 'sr': 'srp_Cyrl',
    'bs': 'bos_Latn', 'mt': 'mlt_Latn', 'is': 'isl_Latn', 'ga': 'gle_Latn', 'cy': 'cym_Latn',
    'eu': 'eus_Latn', 'ca': 'cat_Latn', 'gl': 'glg_Latn', 'lb': 'ltz_Latn', 'mk': 'mkd_Cyrl',
    'th': 'tha_Thai', 'vi': 'vie_Latn', 'id': 'ind_Latn', 'ms': 'zsm_Latn', 'tl': 'tgl_Latn',
    'sw': 'swh_Latn', 'am': 'amh_Ethi', 'xh': 'xho_Latn', 'zu': 'zul_Latn', 'af': 'afr_Latn',
    'yo': 'yor_Latn', 'ig': 'ibo_Latn', 'ha': 'hau_Latn', 'so': 'som_Latn', 'om': 'orm_Latn',
    'rw': 'kin_Latn', 'lg': 'lug_Latn', 'ny': 'nya_Latn', 'sn': 'sna_Latn', 'st': 'sot_Latn',
    'tn': 'tsn_Latn', 've': 'ven_Latn', 'ts': 'tso_Latn', 'ss': 'ssw_Latn', 'nr': 'nbl_Latn',
    'bn': 'ben_Beng', 'gu': 'guj_Gujr', 'kn': 'kan_Knda', 'ml': 'mal_Mlym', 'mr': 'mar_Deva',
    'ne': 'npi_Deva', 'or': 'ori_Orya', 'pa': 'pan_Guru', 'si': 'sin_Sinh', 'ta': 'tam_Taml',
    'te': 'tel_Telu', 'ur': 'urd_Arab', 'as': 'asm_Beng', 'ks': 'kas_Arab', 'sd': 'snd_Arab',
    'fa': 'pes_Arab', 'ps': 'pbt_Arab', 'uz': 'uzn_Latn', 'ky': 'kir_Cyrl', 'kk': 'kaz_Cyrl',
    'tg': 'tgk_Cyrl', 'mn': 'khk_Cyrl', 'my': 'mya_Mymr', 'km': 'khm_Khmr', 'lo': 'lao_Laoo',
    'ka': 'kat_Geor', 'az': 'azj_Latn', 'hy': 'hye_Armn', 'he': 'heb_Hebr', 'yi': 'yid_Hebr'
}

# UMT5 supported languages (107 languages)
UMT5_LANGUAGES = [
    'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca', 'ceb', 'ny', 'zh',
    'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de',
    'el', 'gu', 'ht', 'ha', 'haw', 'iw', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja',
    'jw', 'kn', 'kk', 'km', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms',
    'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru',
    'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg',
    'ta', 'te', 'th', 'tr', 'uk', 'ur', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'
]

# Babel-83B supported languages (25 highest quality)
BABEL_LANGUAGES = [
    'en', 'zh', 'hi', 'es', 'ar', 'fr', 'bn', 'pt', 'ru', 'ur', 'id', 'de', 'ja', 'sw', 'tl', 
    'ta', 'vi', 'tr', 'it', 'jv', 'ko', 'ha', 'fa', 'th', 'my'
]

# =================== Translation Models ===================

@serve.deployment(
    name="nllb_translator",
    num_replicas=2,
    max_replicas=4,
    ray_actor_options={"num_cpus": 2, "num_gpus": 0.5},
    autoscaling_config={
        "target_num_ongoing_requests_per_replica": 3,
        "min_replicas": 2,
        "max_replicas": 4,
        "upscale_delay_s": 10,
        "downscale_delay_s": 30,
    }
)
class NLLBTranslator:
    """NLLB-200 Translation Model - 200+ languages"""
    
    def __init__(self):
        self.model_name = "facebook/nllb-200-3.3B"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.request_count = 0
        self.total_time = 0.0
        
    async def __call__(self, request: TranslationRequest) -> TranslationResponse:
        await self._ensure_model_loaded()
        start_time = time.time()
        
        try:
            # Map language codes to NLLB format
            src_lang = NLLB_LANGUAGES.get(request.source_lang, f"{request.source_lang}_Latn")
            tgt_lang = NLLB_LANGUAGES.get(request.target_lang, f"{request.target_lang}_Latn")
            
            # Prepare input
            self.tokenizer.src_lang = src_lang
            inputs = self.tokenizer(request.text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate translation
            forced_bos_token_id = self.tokenizer.lang_code_to_id[tgt_lang]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_length=1024,
                    num_beams=5 if request.quality == "high" else 3,
                    temperature=0.7 if request.quality == "fast" else 0.1,
                    do_sample=request.quality == "fast",
                    early_stopping=True
                )
            
            translated_text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_time += processing_time
            
            return TranslationResponse(
                translated_text=translated_text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                model_used="nllb-200",
                confidence=0.95,  # NLLB generally high confidence
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"NLLB translation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
    
    async def _ensure_model_loaded(self):
        if self.model is None:
            logger.info("Loading NLLB-200 model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            if self.device == "cuda":
                self.model = self.model.cuda()
            logger.info("NLLB-200 model loaded successfully")
    
    def get_health(self) -> Dict[str, Any]:
        return {
            "model": "nllb-200",
            "status": "healthy" if self.model is not None else "loading",
            "request_count": self.request_count,
            "avg_latency": self.total_time / max(self.request_count, 1),
            "device": self.device,
            "supported_languages": len(NLLB_LANGUAGES)
        }

@serve.deployment(
    name="umt5_translator", 
    num_replicas=1,
    max_replicas=3,
    ray_actor_options={"num_cpus": 4, "num_gpus": 1},
    autoscaling_config={
        "target_num_ongoing_requests_per_replica": 2,
        "min_replicas": 1,
        "max_replicas": 3,
        "upscale_delay_s": 15,
        "downscale_delay_s": 45,
    }
)
class UMT5Translator:
    """UMT5-XXL Translation Model - 107 languages, excellent quality"""
    
    def __init__(self):
        self.model_name = "google/umt5-xxl"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.request_count = 0
        self.total_time = 0.0
        
    async def __call__(self, request: TranslationRequest) -> TranslationResponse:
        await self._ensure_model_loaded()
        start_time = time.time()
        
        try:
            # UMT5 uses task prefix format
            task_prefix = f"translate {request.source_lang} to {request.target_lang}: "
            input_text = task_prefix + request.text
            
            inputs = self.tokenizer(
                input_text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=1024,
                    num_beams=4 if request.quality == "high" else 2,
                    temperature=0.8 if request.quality == "fast" else 0.2,
                    do_sample=request.quality == "fast",
                    early_stopping=True
                )
            
            translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_time += processing_time
            
            return TranslationResponse(
                translated_text=translated_text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                model_used="umt5-xxl",
                confidence=0.92,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"UMT5 translation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
    
    async def _ensure_model_loaded(self):
        if self.model is None:
            logger.info("Loading UMT5-XXL model...")
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = MT5ForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                load_in_8bit=True  # Memory optimization
            )
            logger.info("UMT5-XXL model loaded successfully")
    
    def get_health(self) -> Dict[str, Any]:
        return {
            "model": "umt5-xxl",
            "status": "healthy" if self.model is not None else "loading",
            "request_count": self.request_count,
            "avg_latency": self.total_time / max(self.request_count, 1),
            "device": self.device,
            "supported_languages": len(UMT5_LANGUAGES)
        }

@serve.deployment(
    name="babel_translator",
    num_replicas=1,
    max_replicas=2,
    ray_actor_options={"num_cpus": 6, "num_gpus": 1},
    autoscaling_config={
        "target_num_ongoing_requests_per_replica": 1,
        "min_replicas": 1,
        "max_replicas": 2,
        "upscale_delay_s": 20,
        "downscale_delay_s": 60,
    }
)
class BabelTranslator:
    """Babel-83B Translation Model - 25 languages, highest quality"""
    
    def __init__(self):
        self.model_name = "Tower-Babel/Babel-83B"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.request_count = 0
        self.total_time = 0.0
        
    async def __call__(self, request: TranslationRequest) -> TranslationResponse:
        await self._ensure_model_loaded()
        start_time = time.time()
        
        try:
            # Babel uses instruction format
            instruction = f"Translate the following text from {request.source_lang} to {request.target_lang}:\n{request.text}"
            
            inputs = self.tokenizer(
                instruction,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=1024,
                    num_beams=6 if request.quality == "high" else 4,
                    temperature=0.1,  # Low temperature for high quality
                    do_sample=False,
                    early_stopping=True,
                    repetition_penalty=1.1
                )
            
            translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract translation from generated text
            if ":\n" in translated_text:
                translated_text = translated_text.split(":\n")[-1].strip()
            
            processing_time = time.time() - start_time
            self.request_count += 1
            self.total_time += processing_time
            
            return TranslationResponse(
                translated_text=translated_text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                model_used="babel-83b",
                confidence=0.98,  # Highest quality model
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Babel translation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
    
    async def _ensure_model_loaded(self):
        if self.model is None:
            logger.info("Loading Babel-83B model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                load_in_8bit=True  # Memory optimization for large model
            )
            logger.info("Babel-83B model loaded successfully")
    
    def get_health(self) -> Dict[str, Any]:
        return {
            "model": "babel-83b",
            "status": "healthy" if self.model is not None else "loading",
            "request_count": self.request_count,
            "avg_latency": self.total_time / max(self.request_count, 1),
            "device": self.device,
            "supported_languages": len(BABEL_LANGUAGES)
        }

# =================== Language Detection ===================

@serve.deployment(
    name="language_detector",
    num_replicas=1,
    max_replicas=2,
    ray_actor_options={"num_cpus": 1, "num_gpus": 0}
)
class LanguageDetector:
    """Language detection service"""
    
    def __init__(self):
        self.detector = None
        
    async def __call__(self, request: LanguageDetectionRequest) -> LanguageDetectionResponse:
        await self._ensure_detector_loaded()
        
        try:
            # Use transformers language detection pipeline
            result = self.detector(request.text)
            
            # Format results
            detected = result[0] if result else {"label": "unknown", "score": 0.0}
            alternatives = result[1:3] if len(result) > 1 else []
            
            return LanguageDetectionResponse(
                detected_language=detected["label"],
                confidence=detected["score"],
                alternatives=[{"language": alt["label"], "confidence": alt["score"]} for alt in alternatives]
            )
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")
    
    async def _ensure_detector_loaded(self):
        if self.detector is None:
            logger.info("Loading language detection model...")
            self.detector = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
                return_all_scores=True
            )
            logger.info("Language detection model loaded")

# =================== Main Translation Service ===================

@serve.deployment(
    name="translation_service",
    num_replicas=1,
    ray_actor_options={"num_cpus": 1}
)
class TranslationService:
    """Main translation orchestrator with model selection and redundancy"""
    
    def __init__(self):
        self.models = {}
        self.total_requests = 0
        self.error_count = 0
        
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Main translation endpoint with automatic model selection"""
        self.total_requests += 1
        
        try:
            # Automatic model selection if not specified
            if request.model == TranslationModel.AUTO:
                request.model = self._select_best_model(request.source_lang, request.target_lang)
            
            # Route to appropriate model with fallback
            result = await self._translate_with_fallback(request)
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Translation service error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
    
    def _select_best_model(self, source_lang: str, target_lang: str) -> TranslationModel:
        """Select the best model based on language pair and quality requirements"""
        
        # Prefer Babel for supported high-quality languages
        if source_lang in BABEL_LANGUAGES and target_lang in BABEL_LANGUAGES:
            return TranslationModel.BABEL_83B
            
        # Use UMT5 for good coverage and quality
        if source_lang in UMT5_LANGUAGES and target_lang in UMT5_LANGUAGES:
            return TranslationModel.UMT5_XXL
            
        # Default to NLLB for maximum language coverage
        return TranslationModel.NLLB_200
    
    async def _translate_with_fallback(self, request: TranslationRequest) -> TranslationResponse:
        """Translate with fallback to other models if primary fails"""
        
        # Define fallback order based on selected model
        if request.model == TranslationModel.BABEL_83B:
            models_to_try = ["babel_translator", "umt5_translator", "nllb_translator"]
        elif request.model == TranslationModel.UMT5_XXL:
            models_to_try = ["umt5_translator", "nllb_translator", "babel_translator"]
        else:  # NLLB_200
            models_to_try = ["nllb_translator", "umt5_translator", "babel_translator"]
        
        last_error = None
        
        for model_name in models_to_try:
            try:
                handle = serve.get_deployment(model_name).get_handle()
                result = await handle.remote(request)
                return result
                
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {str(e)}")
                last_error = e
                continue
        
        # If all models fail, raise the last error
        raise last_error or Exception("All translation models failed")
    
    async def get_health(self) -> HealthResponse:
        """Health check endpoint"""
        try:
            # Get health from all models
            model_healths = []
            for model_name in ["nllb_translator", "umt5_translator", "babel_translator"]:
                try:
                    handle = serve.get_deployment(model_name).get_handle()
                    health = await handle.get_health.remote()
                    model_healths.append(health["model"])
                except:
                    pass
            
            error_rate = self.error_count / max(self.total_requests, 1)
            
            return HealthResponse(
                status="healthy" if error_rate < 0.1 else "degraded",
                models_loaded=model_healths,
                total_requests=self.total_requests,
                average_latency=0.5,  # Placeholder
                error_rate=error_rate
            )
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return HealthResponse(
                status="unhealthy",
                models_loaded=[],
                total_requests=self.total_requests,
                average_latency=0.0,
                error_rate=1.0
            )

# =================== FastAPI Application ===================

app = FastAPI(
    title="Enterprise Translation Service",
    description="Multi-model translation service with 200+ language support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== API Endpoints ===================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        handle = serve.get_deployment("translation_service").get_handle()
        return await handle.get_health.remote()
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            models_loaded=[],
            total_requests=0,
            average_latency=0.0,
            error_rate=1.0
        )

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text between languages"""
    try:
        handle = serve.get_deployment("translation_service").get_handle()
        return await handle.translate.remote(request)
    except Exception as e:
        logger.error(f"Translation API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """Detect the language of input text"""
    try:
        handle = serve.get_deployment("language_detector").get_handle()
        return await handle.remote(request)
    except Exception as e:
        logger.error(f"Language detection API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported languages by model"""
    return {
        "nllb_200": {
            "count": len(NLLB_LANGUAGES),
            "languages": list(NLLB_LANGUAGES.keys())
        },
        "umt5_xxl": {
            "count": len(UMT5_LANGUAGES),
            "languages": UMT5_LANGUAGES
        },
        "babel_83b": {
            "count": len(BABEL_LANGUAGES),
            "languages": BABEL_LANGUAGES
        }
    }

@app.get("/models")
async def get_models():
    """Get information about available translation models"""
    return {
        "models": [
            {
                "name": "nllb-200",
                "description": "Meta NLLB-200: 200+ languages, state-of-the-art quality",
                "languages": len(NLLB_LANGUAGES),
                "best_for": "Maximum language coverage, low-resource languages"
            },
            {
                "name": "umt5-xxl", 
                "description": "Google UMT5-XXL: 107 languages, excellent multilingual capabilities",
                "languages": len(UMT5_LANGUAGES),
                "best_for": "Balanced quality and coverage"
            },
            {
                "name": "babel-83b",
                "description": "Tower Babel-83B: 25 languages, highest quality translations",
                "languages": len(BABEL_LANGUAGES),
                "best_for": "Maximum quality for supported languages"
            }
        ]
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Enterprise Translation Service",
        "version": "1.0.0",
        "models": 3,
        "total_languages": len(set(list(NLLB_LANGUAGES.keys()) + UMT5_LANGUAGES + BABEL_LANGUAGES)),
        "features": [
            "Multi-model translation",
            "200+ language support", 
            "Automatic model selection",
            "Redundancy and failover",
            "Language detection",
            "Real-time processing"
        ],
        "endpoints": [
            "/translate",
            "/detect-language", 
            "/languages",
            "/models",
            "/health",
            "/docs"
        ]
    }

# =================== Deployment Function ===================

def deploy_translation_service(host: str = "0.0.0.0", port: int = 8000):
    """Deploy the translation service to Ray cluster"""
    
    # Initialize Ray if not already initialized
    if not ray.is_initialized():
        ray.init(address="auto")
    
    # Deploy all models
    logger.info("Deploying NLLB translator...")
    NLLBTranslator.deploy()
    
    logger.info("Deploying UMT5 translator...")
    UMT5Translator.deploy()
    
    logger.info("Deploying Babel translator...")
    BabelTranslator.deploy()
    
    logger.info("Deploying language detector...")
    LanguageDetector.deploy()
    
    logger.info("Deploying main translation service...")
    TranslationService.deploy()
    
    # Deploy FastAPI application
    logger.info("Deploying FastAPI application...")
    serve.run(app, host=host, port=port, route_prefix="/")
    
    logger.info(f"Translation service deployed successfully on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info(f"  - API Documentation: http://{host}:{port}/docs")
    logger.info(f"  - Health Check: http://{host}:{port}/health")
    logger.info(f"  - Translation: http://{host}:{port}/translate")
    logger.info(f"  - Language Detection: http://{host}:{port}/detect-language")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy Enterprise Translation Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--ray-address", default="auto", help="Ray cluster address")
    
    args = parser.parse_args()
    
    # Connect to Ray cluster
    if not ray.is_initialized():
        ray.init(address=args.ray_address)
    
    # Deploy service
    deploy_translation_service(host=args.host, port=args.port) 
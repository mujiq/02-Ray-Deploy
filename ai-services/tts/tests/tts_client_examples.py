#!/usr/bin/env python3
"""
TTS Service Client Examples

This script provides various examples of how to interact with the deployed TTS service.
"""

import asyncio
import json
import base64
import time
try:
    import websockets
except ImportError:
    websockets = None
    print("Warning: websockets not installed. WebSocket examples will be skipped.")
import requests
from pathlib import Path

class TTSClient:
    """Client for interacting with the TTS service"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check service health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return None
    
    def synthesize_text(self, text: str, voice_id: str = "default", 
                       emotion: str = "neutral", speed: float = 1.0,
                       output_format: str = "wav"):
        """Synthesize speech from text"""
        payload = {
            "text": text,
            "voice_id": voice_id,
            "emotion": emotion,
            "speed": speed,
            "output_format": output_format
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/synthesize",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Synthesis failed: {e}")
            return None
    
    def synthesize_streaming(self, text: str, output_file: str = "output.wav",
                           voice_id: str = "default", emotion: str = "neutral"):
        """Download streaming synthesis"""
        payload = {
            "text": text,
            "voice_id": voice_id,
            "emotion": emotion,
            "streaming": True
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/synthesize/stream",
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Audio saved to {output_file}")
            return output_file
        except Exception as e:
            print(f"Streaming synthesis failed: {e}")
            return None
    
    def list_models(self):
        """List available models"""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to list models: {e}")
            return None

async def websocket_streaming_example(text: str, ws_url: str = "ws://localhost:8000/ws/tts"):
    """Example of real-time WebSocket streaming"""
    
    if websockets is None:
        print("WebSocket streaming skipped - websockets package not installed")
        return
    
    payload = {
        "text": text,
        "voice_id": "default",
        "emotion": "happy",
        "streaming": True,
        "output_format": "wav"
    }
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("Connected to WebSocket")
            
            # Send request
            await websocket.send(json.dumps(payload))
            print(f"Sent: {text}")
            
            # Receive streaming audio
            audio_chunks = []
            while True:
                try:
                    chunk = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    if isinstance(chunk, bytes):
                        audio_chunks.append(chunk)
                        print(f"Received audio chunk: {len(chunk)} bytes")
                    else:
                        print(f"Received message: {chunk}")
                except asyncio.TimeoutError:
                    break
            
            # Save received audio
            if audio_chunks:
                output_file = "websocket_output.wav"
                with open(output_file, 'wb') as f:
                    for chunk in audio_chunks:
                        f.write(chunk)
                print(f"WebSocket audio saved to {output_file}")
            
    except Exception as e:
        print(f"WebSocket streaming failed: {e}")

def batch_synthesis_example(client: TTSClient):
    """Example of batch processing multiple texts"""
    
    texts = [
        "Hello, this is the first test sentence.",
        "This is the second sentence with a happy emotion.",
        "And this is the third sentence spoken slowly.",
        "Finally, this is the last sentence with normal settings."
    ]
    
    emotions = ["neutral", "happy", "neutral", "neutral"]
    speeds = [1.0, 1.2, 0.8, 1.0]
    
    results = []
    
    print("Starting batch synthesis...")
    start_time = time.time()
    
    for i, (text, emotion, speed) in enumerate(zip(texts, emotions, speeds)):
        print(f"Processing text {i+1}/{len(texts)}")
        
        result = client.synthesize_text(
            text=text,
            emotion=emotion,
            speed=speed,
            voice_id=f"voice_{i+1}"
        )
        
        if result:
            results.append(result)
            print(f"  ✅ Success: {result['duration']:.2f}s audio, "
                  f"processed in {result['processing_time']:.2f}s")
        else:
            print(f"  ❌ Failed")
    
    total_time = time.time() - start_time
    print(f"\nBatch completed in {total_time:.2f}s")
    print(f"Successfully processed {len(results)}/{len(texts)} texts")
    
    return results

def voice_cloning_example(client: TTSClient, reference_audio_path: str = None):
    """Example of voice cloning (if supported)"""
    
    # For this example, we'll use the regular synthesis endpoint
    # In a real implementation, you would upload reference audio
    
    clone_text = "This is a test of voice cloning capabilities."
    
    result = client.synthesize_text(
        text=clone_text,
        voice_id="cloned_voice",
        emotion="neutral"
    )
    
    if result:
        print(f"Voice cloning test successful!")
        print(f"Audio duration: {result['duration']:.2f}s")
        print(f"Model used: {result['model_used']}")
    else:
        print("Voice cloning test failed")
    
    return result

def emotion_testing_example(client: TTSClient):
    """Test different emotions"""
    
    base_text = "This is a test of emotional speech synthesis."
    emotions = ["neutral", "happy", "sad", "angry"]
    
    results = []
    
    print("Testing different emotions...")
    
    for emotion in emotions:
        print(f"Testing emotion: {emotion}")
        
        result = client.synthesize_text(
            text=f"[{emotion.upper()}] {base_text}",
            emotion=emotion,
            voice_id=f"emotion_{emotion}"
        )
        
        if result:
            results.append((emotion, result))
            print(f"  ✅ {emotion}: {result['duration']:.2f}s")
        else:
            print(f"  ❌ {emotion}: Failed")
    
    return results

def performance_benchmark(client: TTSClient, num_requests: int = 10):
    """Benchmark the TTS service performance"""
    
    test_text = "This is a performance benchmark test for the TTS service."
    
    print(f"Running performance benchmark with {num_requests} requests...")
    
    times = []
    successes = 0
    
    for i in range(num_requests):
        start_time = time.time()
        
        result = client.synthesize_text(
            text=f"{test_text} Request number {i+1}.",
            voice_id=f"perf_test_{i}"
        )
        
        end_time = time.time()
        request_time = end_time - start_time
        times.append(request_time)
        
        if result:
            successes += 1
            print(f"Request {i+1}: ✅ {request_time:.2f}s "
                  f"(processing: {result['processing_time']:.2f}s)")
        else:
            print(f"Request {i+1}: ❌ {request_time:.2f}s")
    
    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    success_rate = successes / num_requests * 100
    
    print(f"\n📊 Performance Results:")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Time: {avg_time:.2f}s")
    print(f"Min Time: {min_time:.2f}s")
    print(f"Max Time: {max_time:.2f}s")
    print(f"Requests/second: {1/avg_time:.2f}")
    
    return {
        "success_rate": success_rate,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "rps": 1/avg_time
    }

async def main():
    """Run all examples"""
    
    print("🎵 TTS Service Client Examples 🎵")
    print("=" * 50)
    
    # Initialize client
    client = TTSClient()
    
    # Health check
    print("\n1. Health Check")
    print("-" * 20)
    health = client.health_check()
    if health:
        print(f"✅ Service is healthy")
        print(f"Models loaded: {health['models_loaded']}")
        print(f"GPU memory: {health['gpu_memory_used']:.2f} GB")
        print(f"Uptime: {health['uptime']:.1f}s")
    else:
        print("❌ Service is not healthy - exiting")
        return
    
    # List models
    print("\n2. Available Models")
    print("-" * 20)
    models = client.list_models()
    if models:
        print(f"Primary: {models['primary_model']}")
        print(f"Available: {models['available_models']}")
    
    # Basic synthesis
    print("\n3. Basic Text Synthesis")
    print("-" * 25)
    result = client.synthesize_text(
        text="Hello! This is a test of the TTS service.",
        emotion="happy"
    )
    if result:
        print(f"✅ Synthesis successful!")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Model: {result['model_used']}")
    
    # Streaming synthesis
    print("\n4. Streaming Synthesis")
    print("-" * 22)
    output_file = client.synthesize_streaming(
        text="This is a streaming synthesis test with longer text content.",
        emotion="neutral"
    )
    if output_file:
        print(f"✅ Streaming successful: {output_file}")
    
    # WebSocket streaming
    print("\n5. WebSocket Streaming")
    print("-" * 22)
    await websocket_streaming_example(
        "This is a WebSocket streaming test for real-time audio."
    )
    
    # Batch processing
    print("\n6. Batch Processing")
    print("-" * 19)
    batch_results = batch_synthesis_example(client)
    
    # Emotion testing
    print("\n7. Emotion Testing")
    print("-" * 18)
    emotion_results = emotion_testing_example(client)
    
    # Voice cloning
    print("\n8. Voice Cloning Test")
    print("-" * 21)
    clone_result = voice_cloning_example(client)
    
    # Performance benchmark
    print("\n9. Performance Benchmark")
    print("-" * 24)
    perf_results = performance_benchmark(client, num_requests=5)
    
    print("\n🎉 All examples completed!")
    print("Check the generated audio files:")
    print("- output.wav (streaming)")
    print("- websocket_output.wav (WebSocket)")

if __name__ == "__main__":
    asyncio.run(main()) 
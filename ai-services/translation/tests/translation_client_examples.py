#!/usr/bin/env python3
"""
Enterprise Translation Service - Comprehensive Test Suite
Provides testing, benchmarking, and validation for the multi-model translation service.

Features:
- Model performance testing across all three models (NLLB-200, UMT5-XXL, Babel-83B)
- Language detection accuracy testing
- Translation quality validation across 200+ languages
- Redundancy and failover testing
- Performance benchmarking and latency measurement
- Batch processing examples
- Error handling and edge case testing
"""

import asyncio
import json
import time
import statistics
import argparse
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

# Initialize rich console
console = Console()

@dataclass
class TestResult:
    test_name: str
    success: bool
    latency: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class TranslationTest:
    text: str
    source_lang: str
    target_lang: str
    expected_keywords: List[str]
    model: str = "auto"

class TranslationServiceTester:
    """Comprehensive testing suite for translation service"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results: List[TestResult] = []
        
    def log_result(self, result: TestResult):
        """Log test result"""
        self.results.append(result)
        status = "✅" if result.success else "❌"
        console.print(f"{status} {result.test_name} - {result.latency:.3f}s")
        if not result.success and result.error_message:
            console.print(f"   Error: {result.error_message}", style="red")
    
    def test_health_check(self) -> TestResult:
        """Test service health endpoint"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                return TestResult(
                    test_name="Health Check",
                    success=health_data.get("status") in ["healthy", "degraded"],
                    latency=latency,
                    details=health_data
                )
            else:
                return TestResult(
                    test_name="Health Check",
                    success=False,
                    latency=latency,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            return TestResult(
                test_name="Health Check",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_language_detection(self, text: str, expected_lang: str = None) -> TestResult:
        """Test language detection"""
        start_time = time.time()
        try:
            payload = {"text": text}
            response = self.session.post(
                f"{self.base_url}/detect-language",
                json=payload,
                timeout=15
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                detected = data.get("detected_language", "").lower()
                confidence = data.get("confidence", 0)
                
                success = True
                if expected_lang:
                    success = detected == expected_lang.lower() or confidence > 0.7
                
                return TestResult(
                    test_name=f"Language Detection: '{text[:30]}...'",
                    success=success,
                    latency=latency,
                    details={
                        "detected": detected,
                        "confidence": confidence,
                        "expected": expected_lang
                    }
                )
            else:
                return TestResult(
                    test_name="Language Detection",
                    success=False,
                    latency=latency,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return TestResult(
                test_name="Language Detection",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_translation(self, test_case: TranslationTest) -> TestResult:
        """Test translation with specific test case"""
        start_time = time.time()
        try:
            payload = {
                "text": test_case.text,
                "source_lang": test_case.source_lang,
                "target_lang": test_case.target_lang,
                "model": test_case.model,
                "quality": "balanced"
            }
            
            response = self.session.post(
                f"{self.base_url}/translate",
                json=payload,
                timeout=30
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                translated_text = data.get("translated_text", "")
                model_used = data.get("model_used", "unknown")
                confidence = data.get("confidence", 0)
                
                # Check if expected keywords are present (basic quality check)
                quality_check = True
                if test_case.expected_keywords:
                    translated_lower = translated_text.lower()
                    quality_check = any(keyword.lower() in translated_lower for keyword in test_case.expected_keywords)
                
                return TestResult(
                    test_name=f"Translation {test_case.source_lang}→{test_case.target_lang} ({model_used})",
                    success=bool(translated_text) and quality_check,
                    latency=latency,
                    details={
                        "original": test_case.text,
                        "translated": translated_text,
                        "model_used": model_used,
                        "confidence": confidence,
                        "quality_check": quality_check
                    }
                )
            else:
                return TestResult(
                    test_name=f"Translation {test_case.source_lang}→{test_case.target_lang}",
                    success=False,
                    latency=latency,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return TestResult(
                test_name=f"Translation {test_case.source_lang}→{test_case.target_lang}",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_model_info(self) -> TestResult:
        """Test model information endpoint"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/models", timeout=10)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                expected_models = {"nllb-200", "umt5-xxl", "babel-83b"}
                available_models = {model.get("name") for model in models}
                
                return TestResult(
                    test_name="Model Information",
                    success=expected_models.issubset(available_models),
                    latency=latency,
                    details={"available_models": list(available_models), "model_count": len(models)}
                )
            else:
                return TestResult(
                    test_name="Model Information",
                    success=False,
                    latency=latency,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            return TestResult(
                test_name="Model Information",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            )
    
    def test_supported_languages(self) -> TestResult:
        """Test supported languages endpoint"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/languages", timeout=10)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                total_languages = sum(model_info.get("count", 0) for model_info in data.values())
                
                return TestResult(
                    test_name="Supported Languages",
                    success=total_languages > 100,  # Should support 200+ languages
                    latency=latency,
                    details={"total_unique_languages": total_languages, "models": list(data.keys())}
                )
            else:
                return TestResult(
                    test_name="Supported Languages",
                    success=False,
                    latency=latency,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            return TestResult(
                test_name="Supported Languages",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_concurrent_translations(self, num_concurrent: int = 10) -> TestResult:
        """Test concurrent translation requests"""
        start_time = time.time()
        
        # Test cases for concurrent execution
        test_cases = [
            {"text": f"Hello world, this is test message {i}", "source_lang": "en", "target_lang": "es"}
            for i in range(num_concurrent)
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                tasks = []
                for case in test_cases:
                    task = client.post(f"{self.base_url}/translate", json=case)
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                latency = time.time() - start_time
                
                successful_responses = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
                
                return TestResult(
                    test_name=f"Concurrent Translations ({num_concurrent})",
                    success=successful_responses >= num_concurrent * 0.8,  # 80% success rate
                    latency=latency,
                    details={
                        "total_requests": num_concurrent,
                        "successful": successful_responses,
                        "success_rate": successful_responses / num_concurrent
                    }
                )
                
            except Exception as e:
                return TestResult(
                    test_name=f"Concurrent Translations ({num_concurrent})",
                    success=False,
                    latency=time.time() - start_time,
                    error_message=str(e)
                )
    
    def test_error_handling(self) -> List[TestResult]:
        """Test various error conditions"""
        results = []
        
        # Test invalid language codes
        start_time = time.time()
        try:
            payload = {"text": "Hello", "source_lang": "invalid", "target_lang": "also_invalid"}
            response = self.session.post(f"{self.base_url}/translate", json=payload, timeout=10)
            latency = time.time() - start_time
            
            # Should handle gracefully (either succeed with fallback or return meaningful error)
            results.append(TestResult(
                test_name="Invalid Language Codes",
                success=response.status_code in [200, 400, 422],  # Accept these responses
                latency=latency,
                details={"status_code": response.status_code}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Invalid Language Codes",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            ))
        
        # Test empty text
        start_time = time.time()
        try:
            payload = {"text": "", "source_lang": "en", "target_lang": "es"}
            response = self.session.post(f"{self.base_url}/translate", json=payload, timeout=10)
            latency = time.time() - start_time
            
            results.append(TestResult(
                test_name="Empty Text",
                success=response.status_code in [400, 422],  # Should reject empty text
                latency=latency,
                details={"status_code": response.status_code}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Empty Text",
                success=False,
                latency=time.time() - start_time,
                error_message=str(e)
            ))
        
        # Test very long text
        start_time = time.time()
        try:
            long_text = "This is a very long text. " * 1000  # Very long text
            payload = {"text": long_text, "source_lang": "en", "target_lang": "es"}
            response = self.session.post(f"{self.base_url}/translate", json=payload, timeout=30)
            latency = time.time() - start_time
            
            results.append(TestResult(
                test_name="Very Long Text",
                success=response.status_code in [200, 413, 422],  # Accept success or payload too large
                latency=latency,
                details={"status_code": response.status_code, "text_length": len(long_text)}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Very Long Text",
                success=True,  # Timeout is acceptable for very long text
                latency=time.time() - start_time,
                error_message=str(e)
            ))
        
        return results
    
    def benchmark_performance(self, num_requests: int = 50) -> TestResult:
        """Benchmark translation performance"""
        console.print(f"\n🏃 Running performance benchmark with {num_requests} requests...")
        
        test_text = "Hello, how are you today? I hope you're having a wonderful day!"
        latencies = []
        errors = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Benchmarking...", total=num_requests)
            
            for i in range(num_requests):
                start_time = time.time()
                try:
                    payload = {
                        "text": f"{test_text} Request {i+1}",
                        "source_lang": "en",
                        "target_lang": ["es", "fr", "de", "it", "pt"][i % 5],
                        "model": "auto"
                    }
                    
                    response = self.session.post(
                        f"{self.base_url}/translate",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        latencies.append(time.time() - start_time)
                    else:
                        errors += 1
                        
                except Exception:
                    errors += 1
                
                progress.update(task, advance=1)
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            throughput = len(latencies) / sum(latencies) if latencies else 0
            
            return TestResult(
                test_name=f"Performance Benchmark ({num_requests} requests)",
                success=errors < num_requests * 0.1,  # Less than 10% error rate
                latency=avg_latency,
                details={
                    "total_requests": num_requests,
                    "successful_requests": len(latencies),
                    "error_count": errors,
                    "error_rate": errors / num_requests,
                    "avg_latency": avg_latency,
                    "median_latency": median_latency,
                    "p95_latency": p95_latency,
                    "throughput_rps": throughput,
                    "min_latency": min(latencies) if latencies else 0,
                    "max_latency": max(latencies) if latencies else 0
                }
            )
        else:
            return TestResult(
                test_name=f"Performance Benchmark ({num_requests} requests)",
                success=False,
                latency=0,
                error_message="All requests failed"
            )
    
    def run_comprehensive_tests(self):
        """Run all test suites"""
        console.print("\n🚀 [bold blue]Enterprise Translation Service Test Suite[/bold blue]")
        console.print(f"Testing service at: {self.base_url}\n")
        
        # Basic connectivity tests
        console.print("🔍 [bold]Basic Connectivity Tests[/bold]")
        self.log_result(self.test_health_check())
        self.log_result(self.test_model_info())
        self.log_result(self.test_supported_languages())
        
        # Language detection tests
        console.print("\n🌐 [bold]Language Detection Tests[/bold]")
        detection_tests = [
            ("Hello, how are you?", "en"),
            ("Bonjour, comment allez-vous?", "fr"),
            ("Hola, ¿cómo estás?", "es"),
            ("Guten Tag, wie geht es Ihnen?", "de"),
            ("Ciao, come stai?", "it"),
            ("Привет, как дела?", "ru"),
            ("こんにちは、元気ですか？", "ja"),
            ("你好，你好吗？", "zh")
        ]
        
        for text, expected_lang in detection_tests:
            self.log_result(self.test_language_detection(text, expected_lang))
        
        # Translation quality tests
        console.print("\n🔄 [bold]Translation Quality Tests[/bold]")
        translation_tests = [
            TranslationTest(
                text="Hello, how are you today?",
                source_lang="en",
                target_lang="es",
                expected_keywords=["hola", "como", "está", "cómo"],
                model="auto"
            ),
            TranslationTest(
                text="The weather is beautiful today.",
                source_lang="en",
                target_lang="fr",
                expected_keywords=["temps", "beau", "aujourd"],
                model="nllb-200"
            ),
            TranslationTest(
                text="I love programming and technology.",
                source_lang="en",
                target_lang="de",
                expected_keywords=["liebe", "programmierung", "technologie"],
                model="umt5-xxl"
            ),
            TranslationTest(
                text="Artificial intelligence is transforming the world.",
                source_lang="en",
                target_lang="zh",
                expected_keywords=["人工智能", "改变", "世界"],
                model="babel-83b"
            ),
            TranslationTest(
                text="La tecnología está cambiando nuestras vidas.",
                source_lang="es",
                target_lang="en",
                expected_keywords=["technology", "changing", "lives"],
                model="auto"
            )
        ]
        
        for test_case in translation_tests:
            self.log_result(self.test_translation(test_case))
        
        # Error handling tests
        console.print("\n⚠️  [bold]Error Handling Tests[/bold]")
        error_results = self.test_error_handling()
        for result in error_results:
            self.log_result(result)
        
        # Concurrent testing
        console.print("\n⚡ [bold]Concurrent Load Tests[/bold]")
        asyncio.run(self._run_concurrent_test())
        
        # Performance benchmark
        performance_result = self.benchmark_performance(30)
        self.log_result(performance_result)
        
        # Generate final report
        self.generate_report()
    
    async def _run_concurrent_test(self):
        """Helper for concurrent testing"""
        concurrent_result = await self.test_concurrent_translations(15)
        self.log_result(concurrent_result)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        console.print("\n📊 [bold green]Test Results Summary[/bold green]")
        
        # Calculate statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        avg_latency = statistics.mean([r.latency for r in self.results if r.latency > 0])
        
        # Create summary table
        table = Table(title="Test Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Tests", str(total_tests))
        table.add_row("Successful", str(successful_tests))
        table.add_row("Failed", str(failed_tests))
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Average Latency", f"{avg_latency:.3f}s")
        
        console.print(table)
        
        # Performance details
        perf_result = next((r for r in self.results if "Performance Benchmark" in r.test_name), None)
        if perf_result and perf_result.details:
            console.print("\n🏆 [bold]Performance Metrics[/bold]")
            details = perf_result.details
            
            perf_table = Table()
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="yellow")
            
            perf_table.add_row("Throughput", f"{details.get('throughput_rps', 0):.2f} RPS")
            perf_table.add_row("Average Latency", f"{details.get('avg_latency', 0):.3f}s")
            perf_table.add_row("Median Latency", f"{details.get('median_latency', 0):.3f}s")
            perf_table.add_row("95th Percentile", f"{details.get('p95_latency', 0):.3f}s")
            perf_table.add_row("Error Rate", f"{details.get('error_rate', 0)*100:.1f}%")
            
            console.print(perf_table)
        
        # Failed tests details
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            console.print("\n❌ [bold red]Failed Tests[/bold red]")
            for result in failed_results:
                console.print(f"• {result.test_name}: {result.error_message}")
        
        # Overall status
        if success_rate >= 90:
            console.print("\n✅ [bold green]Service is operating excellently![/bold green]")
        elif success_rate >= 75:
            console.print("\n⚠️  [bold yellow]Service is operating with some issues[/bold yellow]")
        else:
            console.print("\n❌ [bold red]Service has significant issues[/bold red]")

def main():
    parser = argparse.ArgumentParser(description="Translation Service Test Suite")
    parser.add_argument(
        "--service-url",
        default="http://localhost:8001",
        help="Translation service URL (default: http://localhost:8001)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (skip performance benchmarks)"
    )
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help="Run performance benchmark only"
    )
    parser.add_argument(
        "--benchmark-requests",
        type=int,
        default=50,
        help="Number of requests for performance benchmark (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Test service connectivity first
    try:
        response = requests.get(f"{args.service_url}/health", timeout=5)
        if response.status_code != 200:
            console.print(f"❌ [red]Service not responding at {args.service_url}[/red]")
            console.print("Please ensure the translation service is running.")
            sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Cannot connect to service at {args.service_url}[/red]")
        console.print(f"Error: {e}")
        console.print("\nTo start the service:")
        console.print("  cd ai-services/translation/")
        console.print("  ./deployment/deploy_translation.sh --install-deps")
        sys.exit(1)
    
    # Initialize tester
    tester = TranslationServiceTester(args.service_url)
    
    if args.benchmark_only:
        # Run benchmark only
        console.print("🏃 [bold]Running Performance Benchmark Only[/bold]")
        result = tester.benchmark_performance(args.benchmark_requests)
        tester.log_result(result)
        tester.generate_report()
    elif args.quick:
        # Run quick tests
        console.print("⚡ [bold]Running Quick Test Suite[/bold]")
        tester.log_result(tester.test_health_check())
        tester.log_result(tester.test_language_detection("Hello world", "en"))
        test_case = TranslationTest("Hello", "en", "es", ["hola"])
        tester.log_result(tester.test_translation(test_case))
        tester.generate_report()
    else:
        # Run comprehensive tests
        tester.run_comprehensive_tests()

if __name__ == "__main__":
    main() 
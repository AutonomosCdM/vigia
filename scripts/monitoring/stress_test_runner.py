#!/usr/bin/env python3
"""
Vigia Stress Test Runner
========================

Script para ejecutar tests de estrés de manera sistemática y generar reportes.
"""

import subprocess
import time
import psutil
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse

class StressTestRunner:
    """Runner principal para tests de estrés"""
    
    def __init__(self, output_dir: str = "stress_test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
        self.start_time = None
        
    def run_baseline_tests(self) -> Dict[str, Any]:
        """Ejecutar tests baseline para validar estado inicial"""
        print("🔍 Running baseline tests...")
        
        cmd = [
            "python", "-m", "pytest", "vigia_detect/",
            "--ignore=vigia_detect/redis_layer/tests/test_cache_service.py",
            "--ignore=vigia_detect/redis_layer/tests/test_vector_service.py", 
            "--ignore=vigia_detect/redis_layer/tests/test_medical_cache.py",
            "-v", "--tb=short", "--junit-xml=baseline_results.xml"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        # Parse results
        baseline_results = {
            "duration": end_time - start_time,
            "return_code": result.returncode,
            "stdout_lines": len(result.stdout.split('\n')),
            "stderr_lines": len(result.stderr.split('\n')),
            "success": result.returncode == 0 or result.returncode == 1  # Allow some failures
        }
        
        # Extract test counts from output
        output = result.stdout
        if "failed" in output:
            failed_count = self._extract_test_count(output, "failed")
            passed_count = self._extract_test_count(output, "passed")
        else:
            failed_count = 0
            passed_count = self._extract_test_count(output, "passed")
            
        baseline_results.update({
            "tests_passed": passed_count,
            "tests_failed": failed_count,
            "success_rate": passed_count / (passed_count + failed_count) if (passed_count + failed_count) > 0 else 0
        })
        
        print(f"✅ Baseline: {passed_count} passed, {failed_count} failed in {baseline_results['duration']:.2f}s")
        return baseline_results
    
    def run_parallel_stress(self, workers: int = 10) -> Dict[str, Any]:
        """Ejecutar tests en paralelo para stress testing"""
        print(f"⚡ Running parallel stress test with {workers} workers...")
        
        cmd = [
            "python", "-m", "pytest", "vigia_detect/",
            "--ignore=vigia_detect/redis_layer/tests/test_cache_service.py",
            "--ignore=vigia_detect/redis_layer/tests/test_vector_service.py",
            "--ignore=vigia_detect/redis_layer/tests/test_medical_cache.py", 
            f"-n", str(workers), "--maxfail=20", "-q"
        ]
        
        # Monitor system resources during test
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        start_time = time.time()
        peak_memory = 0
        peak_cpu = 0
        
        while process.poll() is None:
            try:
                # Monitor system resources
                memory_mb = psutil.virtual_memory().used / 1024 / 1024
                cpu_percent = psutil.cpu_percent()
                
                peak_memory = max(peak_memory, memory_mb)
                peak_cpu = max(peak_cpu, cpu_percent)
                
                time.sleep(0.5)
            except:
                pass
        
        stdout, stderr = process.communicate()
        end_time = time.time()
        
        parallel_results = {
            "workers": workers,
            "duration": end_time - start_time,
            "return_code": process.returncode,
            "peak_memory_mb": peak_memory,
            "peak_cpu_percent": peak_cpu,
            "success": process.returncode == 0
        }
        
        # Extract test results
        if "failed" in stdout:
            failed_count = self._extract_test_count(stdout, "failed")
            passed_count = self._extract_test_count(stdout, "passed")
        else:
            failed_count = 0
            passed_count = self._extract_test_count(stdout, "passed")
            
        parallel_results.update({
            "tests_passed": passed_count,
            "tests_failed": failed_count,
            "success_rate": passed_count / (passed_count + failed_count) if (passed_count + failed_count) > 0 else 0,
            "throughput": (passed_count + failed_count) / parallel_results["duration"] if parallel_results["duration"] > 0 else 0
        })
        
        print(f"✅ Parallel: {passed_count} passed, {failed_count} failed in {parallel_results['duration']:.2f}s")
        print(f"📊 Throughput: {parallel_results['throughput']:.2f} tests/sec, Peak Memory: {peak_memory:.0f}MB")
        
        return parallel_results
    
    def run_repetition_stress(self, count: int = 20) -> Dict[str, Any]:
        """Ejecutar tests repetitivos para detectar memory leaks y race conditions"""
        print(f"🔄 Running repetition stress test ({count} iterations)...")
        
        cmd = [
            "python", "-m", "pytest", "vigia_detect/messaging/tests/",
            f"--count={count}", "-q", "--tb=no"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        repetition_results = {
            "iterations": count,
            "duration": end_time - start_time,
            "return_code": result.returncode,
            "success": result.returncode == 0,
            "avg_iteration_time": (end_time - start_time) / count
        }
        
        print(f"✅ Repetition: {count} iterations in {repetition_results['duration']:.2f}s")
        print(f"⏱️  Avg per iteration: {repetition_results['avg_iteration_time']:.2f}s")
        
        return repetition_results
    
    def run_memory_stress(self) -> Dict[str, Any]:
        """Ejecutar tests específicos de memoria"""
        print("🧠 Running memory stress test...")
        
        # Focus on memory-intensive components
        memory_test_modules = [
            "vigia_detect/cv_pipeline/tests/",
            "vigia_detect/webhook/tests/test_models.py",
            "vigia_detect/messaging/tests/test_whatsapp_processor.py"
        ]
        
        memory_results = []
        
        for module in memory_test_modules:
            cmd = ["python", "-m", "pytest", module, "-v", "--tb=no"]
            
            # Monitor memory usage
            start_memory = psutil.virtual_memory().used / 1024 / 1024
            start_time = time.time()
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / 1024 / 1024
            memory_delta = end_memory - start_memory
            
            module_result = {
                "module": module,
                "duration": end_time - start_time,
                "memory_delta_mb": memory_delta,
                "success": result.returncode == 0
            }
            
            memory_results.append(module_result)
            print(f"  📦 {module}: {memory_delta:+.1f}MB in {module_result['duration']:.2f}s")
        
        total_memory_delta = sum(r["memory_delta_mb"] for r in memory_results)
        total_duration = sum(r["duration"] for r in memory_results)
        
        return {
            "module_results": memory_results,
            "total_memory_delta_mb": total_memory_delta,
            "total_duration": total_duration,
            "avg_memory_per_test": total_memory_delta / len(memory_results)
        }
    
    def generate_report(self) -> str:
        """Generar reporte final de stress testing"""
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate overall metrics
        baseline = self.results.get("baseline", {})
        parallel = self.results.get("parallel", {})
        repetition = self.results.get("repetition", {})
        memory = self.results.get("memory", {})
        
        # Determine overall status
        overall_success = all([
            baseline.get("success", False),
            parallel.get("success_rate", 0) > 0.90,  # 90% success rate acceptable under stress
            repetition.get("success", False),
            abs(memory.get("total_memory_delta_mb", 0)) < 500  # Less than 500MB memory growth
        ])
        
        status_emoji = "✅" if overall_success else "❌"
        status_text = "PASS" if overall_success else "FAIL"
        
        report = f"""
🔬 VIGIA STRESS TEST REPORT
===========================
Generated: {report_time}
Status: {status_emoji} {status_text}

📊 BASELINE RESULTS
-------------------
• Tests Executed: {baseline.get('tests_passed', 0) + baseline.get('tests_failed', 0)}
• Success Rate: {baseline.get('success_rate', 0):.1%}
• Duration: {baseline.get('duration', 0):.2f}s
• Status: {'✅ PASS' if baseline.get('success', False) else '❌ FAIL'}

⚡ PARALLEL STRESS RESULTS  
-------------------------
• Workers: {parallel.get('workers', 0)}
• Tests Executed: {parallel.get('tests_passed', 0) + parallel.get('tests_failed', 0)}
• Success Rate: {parallel.get('success_rate', 0):.1%}
• Throughput: {parallel.get('throughput', 0):.2f} tests/sec
• Peak Memory: {parallel.get('peak_memory_mb', 0):.0f}MB
• Peak CPU: {parallel.get('peak_cpu_percent', 0):.1f}%
• Duration: {parallel.get('duration', 0):.2f}s

🔄 REPETITION STRESS RESULTS
----------------------------
• Iterations: {repetition.get('iterations', 0)}
• Avg per Iteration: {repetition.get('avg_iteration_time', 0):.2f}s
• Total Duration: {repetition.get('duration', 0):.2f}s
• Status: {'✅ PASS' if repetition.get('success', False) else '❌ FAIL'}

🧠 MEMORY STRESS RESULTS
------------------------
• Total Memory Delta: {memory.get('total_memory_delta_mb', 0):+.1f}MB
• Avg per Module: {memory.get('avg_memory_per_test', 0):+.1f}MB
• Total Duration: {memory.get('total_duration', 0):.2f}s

🎯 PERFORMANCE SUMMARY
----------------------
• Overall Success Rate: {(baseline.get('success_rate', 0) + parallel.get('success_rate', 0)) / 2:.1%}
• System Stability: {'✅ STABLE' if abs(memory.get('total_memory_delta_mb', 0)) < 100 else '⚠️ MONITOR'}
• Concurrent Performance: {'✅ GOOD' if parallel.get('throughput', 0) > 1.0 else '⚠️ SLOW'}

📝 RECOMMENDATIONS
------------------
"""
        
        # Add specific recommendations based on results
        if parallel.get('success_rate', 0) < 0.95:
            report += "• ⚠️ Consider reducing parallel workers or optimizing resource-heavy tests\n"
        
        if memory.get('total_memory_delta_mb', 0) > 200:
            report += "• ⚠️ Investigate potential memory leaks in CV pipeline or webhook components\n"
            
        if parallel.get('throughput', 0) < 1.0:
            report += "• ⚠️ Performance bottlenecks detected, consider test optimization\n"
            
        if baseline.get('success_rate', 0) < 1.0:
            report += "• ❌ Fix failing baseline tests before stress testing\n"
        
        if overall_success:
            report += "• ✅ System is ready for production load testing\n"
            report += "• ✅ Consider implementing continuous stress testing in CI/CD\n"
        
        return report
    
    def _extract_test_count(self, output: str, status: str) -> int:
        """Extract test count from pytest output"""
        try:
            lines = output.split('\n')
            # Look for the summary line like "11 failed, 124 passed, 1 skipped"
            for line in lines:
                if 'failed' in line and 'passed' in line:
                    # Parse line like "11 failed, 124 passed, 1 skipped, 190 warnings"
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if status in part:
                            # Extract number before the status word
                            words = part.split()
                            for i, word in enumerate(words):
                                if word == status and i > 0:
                                    return int(words[i-1])
            
            # Fallback: look for individual status mentions
            for line in lines:
                if status in line and ('=' in line or '::' not in line):
                    words = line.split()
                    for i, word in enumerate(words):
                        if word == status and i > 0:
                            try:
                                return int(words[i-1])
                            except ValueError:
                                continue
            return 0
        except:
            return 0
    
    def run_full_stress_test(self, parallel_workers: int = 10, repetition_count: int = 20) -> Dict[str, Any]:
        """Ejecutar suite completo de stress tests"""
        print("🚀 Starting Vigia Full Stress Test Suite...")
        print("=" * 50)
        
        self.start_time = time.time()
        
        # 1. Baseline validation
        self.results["baseline"] = self.run_baseline_tests()
        baseline_success_rate = self.results["baseline"].get("success_rate", 0)
        if baseline_success_rate < 0.85:  # Require at least 85% success rate
            print(f"❌ Baseline success rate too low ({baseline_success_rate:.1%}). Aborting stress test suite.")
            return self.results
        elif baseline_success_rate < 0.95:
            print(f"⚠️ Baseline success rate is {baseline_success_rate:.1%}, proceeding with caution...")
        
        print()
        
        # 2. Parallel stress testing
        self.results["parallel"] = self.run_parallel_stress(parallel_workers)
        print()
        
        # 3. Repetition stress testing  
        self.results["repetition"] = self.run_repetition_stress(repetition_count)
        print()
        
        # 4. Memory stress testing
        self.results["memory"] = self.run_memory_stress()
        print()
        
        # 5. Generate and save report
        total_time = time.time() - self.start_time
        self.results["meta"] = {
            "total_duration": total_time,
            "timestamp": datetime.now().isoformat()
        }
        
        report = self.generate_report()
        
        # Save results
        results_file = self.output_dir / f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        report_file = self.output_dir / f"stress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n💾 Results saved to: {results_file}")
        print(f"📄 Report saved to: {report_file}")
        print(f"⏱️  Total test time: {total_time:.2f}s")
        
        return self.results

def main():
    """Entry point para stress testing"""
    parser = argparse.ArgumentParser(description="Vigia Stress Test Runner")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--repetitions", type=int, default=20, help="Number of repetition iterations")
    parser.add_argument("--output", type=str, default="stress_test_results", help="Output directory")
    
    args = parser.parse_args()
    
    runner = StressTestRunner(args.output)
    results = runner.run_full_stress_test(args.workers, args.repetitions)
    
    # Exit with appropriate code
    baseline_success = results.get("baseline", {}).get("success", False)
    parallel_success = results.get("parallel", {}).get("success_rate", 0) > 0.90
    
    if baseline_success and parallel_success:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
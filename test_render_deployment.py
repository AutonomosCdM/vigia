#!/usr/bin/env python3
"""
Test script for Render deployment
Tests the unified server functionality
"""

import requests
import time
import subprocess
import sys
import os
from pathlib import Path

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test the health endpoint."""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Health data: {data}")
            return True
        else:
            print(f"Health check failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Health check failed with exception: {e}")
        return False

def test_root_endpoint(base_url="http://localhost:8000"):
    """Test the root endpoint."""
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Root endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("Root endpoint working correctly")
            return True
        else:
            print(f"Root endpoint failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Root endpoint failed with exception: {e}")
        return False

def test_api_endpoints(base_url="http://localhost:8000"):
    """Test various API endpoints."""
    endpoints = ["/webhook", "/whatsapp", "/detect"]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"{endpoint} status: {response.status_code}")
            
            if response.status_code in [200, 405]:  # 405 is OK for POST-only endpoints
                print(f"{endpoint} is accessible")
            else:
                print(f"{endpoint} failed: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"{endpoint} failed with exception: {e}")

def test_docker_build():
    """Test Docker build process."""
    print("Testing Docker build...")
    
    try:
        # Build the Docker image
        result = subprocess.run([
            "docker", "build", "-f", "Dockerfile.render", "-t", "vigia-render-test", "."
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            return True
        else:
            print(f"❌ Docker build failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker build timed out (>10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Docker build error: {e}")
        return False

def test_docker_run():
    """Test running the Docker container."""
    print("Testing Docker container...")
    
    try:
        # Stop any existing container
        subprocess.run(["docker", "stop", "vigia-test"], capture_output=True)
        subprocess.run(["docker", "rm", "vigia-test"], capture_output=True)
        
        # Run the container
        result = subprocess.run([
            "docker", "run", "-d", "--name", "vigia-test", 
            "-p", "8000:8000", 
            "-e", "PORT=8000",
            "vigia-render-test"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker container started")
            
            # Wait for container to be ready
            print("Waiting for container to be ready...")
            time.sleep(10)
            
            # Test the endpoints
            success = test_health_endpoint()
            if success:
                test_root_endpoint()
                test_api_endpoints()
            
            # Clean up
            subprocess.run(["docker", "stop", "vigia-test"], capture_output=True)
            subprocess.run(["docker", "rm", "vigia-test"], capture_output=True)
            
            return success
        else:
            print(f"❌ Docker container failed to start:")
            print(f"STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker run error: {e}")
        return False

def test_unified_server_direct():
    """Test the unified server directly without Docker."""
    print("Testing unified server directly...")
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    try:
        # Import and test the unified server
        from vigia_detect.web.unified_server import UnifiedServer
        
        print("✅ Unified server module imports successfully")
        
        # Create server instance (don't run it)
        server = UnifiedServer(port=8001, redis_available=False, database_available=False)
        print("✅ Unified server instance created successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import unified server: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to create unified server: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Vigia Render Deployment")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    tests = [
        ("Unified Server Import", test_unified_server_direct),
        ("Docker Build", test_docker_build),
        ("Docker Run", test_docker_run),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for Render deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
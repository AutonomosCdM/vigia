#!/usr/bin/env python3
"""
Script to run webhook integration tests with proper environment setup.
"""

import subprocess
import sys
import os
from pathlib import Path


def setup_test_environment():
    """Setup environment for webhook tests."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Set environment variables for testing
    os.environ['WEBHOOK_TEST_MODE'] = 'true'
    os.environ['PYTHONPATH'] = str(project_root)


def run_tests(test_type="all", verbose=False):
    """
    Run webhook tests.
    
    Args:
        test_type: Type of tests to run ("unit", "integration", "all")
        verbose: Whether to run in verbose mode
    """
    setup_test_environment()
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Test directory
    test_dir = Path(__file__).parent.parent / "vigia_detect" / "webhook" / "tests"
    cmd.append(str(test_dir))
    
    # Add markers based on test type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    # "all" runs everything
    
    # Verbose output
    if verbose:
        cmd.append("-v")
    
    # Additional pytest options
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker validation
        "-W", "ignore::DeprecationWarning",  # Ignore deprecation warnings
    ])
    
    print("🧪 Running Webhook Tests")
    print("=" * 50)
    print(f"Test type: {test_type}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 50)
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def check_dependencies():
    """Check if required test dependencies are available."""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "aiohttp",
        "fastapi",
        "uvicorn",
        "requests"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run webhook tests")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("✅ All dependencies are available")
            return 0
        else:
            return 1
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    # Run tests
    success = run_tests(args.type, args.verbose)
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
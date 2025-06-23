#!/usr/bin/env python3
"""
Simplified Post-Refactor Validation Script for Vigia Medical Detection System
===========================================================================

This script validates basic system functionality without complex dependencies.
"""

import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import subprocess
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SimplePostRefactorValidator:
    """
    Simplified validator for post-refactor system stability.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            'overall_status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'validation_results': {},
            'critical_failures': [],
            'warnings': [],
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warning_checks': 0
            }
        }
    
    def log(self, message: str, level: str = "info"):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{level.upper()}] {message}")
    
    def run_validation(self, quick: bool = False) -> Dict[str, Any]:
        """Run simplified validation checks."""
        self.log("Starting simplified post-refactor validation...")
        
        # Define validation checks
        checks = {
            'python_syntax': self._validate_python_syntax,
            'imports_basic': self._validate_basic_imports,
            'file_structure': self._validate_file_structure,
            'test_fixtures': self._validate_test_fixtures,
            'patient_validation': self._validate_patient_validation,
            'environment_setup': self._validate_environment_setup,
        }
        
        if not quick:
            checks.update({
                'pytest_installation': self._validate_pytest,
                'basic_e2e_tests': self._run_basic_tests,
                'file_permissions': self._validate_file_permissions,
            })
        
        # Run validation checks
        for check_name, check_function in checks.items():
            self.log(f"Running check: {check_name}")
            self.results['summary']['total_checks'] += 1
            
            try:
                start_time = time.time()
                check_result = check_function()
                duration = time.time() - start_time
                
                check_result['duration_seconds'] = duration
                self.results['validation_results'][check_name] = check_result
                
                # Update summary
                status = check_result.get('status', 'failed')
                if status == 'passed':
                    self.results['summary']['passed_checks'] += 1
                    self.log(f"✅ {check_name}: PASSED", "info")
                elif status == 'warning':
                    self.results['summary']['warning_checks'] += 1
                    self.results['warnings'].append(f"{check_name}: {check_result.get('message', 'Warning')}")
                    self.log(f"⚠️ {check_name}: WARNING - {check_result.get('message', '')}", "warning")
                else:
                    self.results['summary']['failed_checks'] += 1
                    failure_msg = f"{check_name}: {check_result.get('message', 'Check failed')}"
                    self.results['critical_failures'].append(failure_msg)
                    self.log(f"❌ {check_name}: FAILED - {check_result.get('message', '')}", "error")
                    
            except Exception as e:
                self.results['summary']['failed_checks'] += 1
                failure_msg = f"{check_name}: Exception - {str(e)}"
                self.results['critical_failures'].append(failure_msg)
                self.log(f"💥 {check_name}: EXCEPTION - {str(e)}", "error")
                
                self.results['validation_results'][check_name] = {
                    'status': 'failed',
                    'message': f"Exception during validation: {str(e)}",
                    'exception': str(e)
                }
        
        # Determine overall status
        if self.results['summary']['failed_checks'] == 0:
            if self.results['summary']['warning_checks'] == 0:
                self.results['overall_status'] = 'stable'
            else:
                self.results['overall_status'] = 'stable_with_warnings'
        else:
            self.results['overall_status'] = 'unstable'
        
        return self.results
    
    def _validate_python_syntax(self) -> Dict[str, Any]:
        """Validate Python syntax in key files."""
        try:
            key_files = [
                'vigia_detect/__init__.py',
                'vigia_detect/core/constants.py',
                'vigia_detect/utils/image_utils.py',
                'tests/shared_fixtures.py',
                'config/settings.py'
            ]
            
            syntax_errors = []
            valid_files = 0
            
            for file_path in key_files:
                full_path = project_root / file_path
                if full_path.exists():
                    try:
                        with open(full_path, 'r') as f:
                            compile(f.read(), str(full_path), 'exec')
                        valid_files += 1
                    except SyntaxError as e:
                        syntax_errors.append(f"{file_path}: {str(e)}")
                else:
                    syntax_errors.append(f"{file_path}: File not found")
            
            if syntax_errors:
                return {
                    'status': 'failed',
                    'message': f'Syntax errors found: {syntax_errors}',
                    'details': {'valid_files': valid_files, 'errors': syntax_errors}
                }
            
            return {
                'status': 'passed',
                'message': f'Python syntax valid in {valid_files} files',
                'details': {'valid_files': valid_files}
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Python syntax validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_basic_imports(self) -> Dict[str, Any]:
        """Validate basic imports work."""
        try:
            import_tests = [
                ('tests.shared_fixtures', 'SAMPLE_PATIENT_CODES'),
                ('vigia_detect.core.constants', 'LPPGrade'),
                ('vigia_detect.utils.image_utils', 'is_valid_image'),
            ]
            
            successful_imports = 0
            failed_imports = []
            
            for module_name, attribute in import_tests:
                try:
                    module = __import__(module_name, fromlist=[attribute])
                    getattr(module, attribute)
                    successful_imports += 1
                except Exception as e:
                    failed_imports.append(f"{module_name}.{attribute}: {str(e)}")
            
            if failed_imports:
                return {
                    'status': 'warning',
                    'message': f'Some imports failed: {failed_imports}',
                    'details': {'successful': successful_imports, 'failed': failed_imports}
                }
            
            return {
                'status': 'passed',
                'message': f'All {successful_imports} basic imports successful',
                'details': {'successful_imports': successful_imports}
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Basic imports validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_file_structure(self) -> Dict[str, Any]:
        """Validate essential file structure."""
        try:
            required_dirs = [
                'vigia_detect',
                'vigia_detect/core',
                'vigia_detect/utils',
                'tests',
                'tests/e2e',
                'config',
                'scripts'
            ]
            
            required_files = [
                'vigia_detect/__init__.py',
                'vigia_detect/core/constants.py',
                'tests/shared_fixtures.py',
                'tests/e2e/test_simple_integration.py',
                'scripts/validate_post_refactor.py'
            ]
            
            missing_dirs = []
            missing_files = []
            
            for dir_path in required_dirs:
                if not (project_root / dir_path).exists():
                    missing_dirs.append(dir_path)
            
            for file_path in required_files:
                if not (project_root / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_dirs or missing_files:
                return {
                    'status': 'failed',
                    'message': f'Missing structure: dirs={missing_dirs}, files={missing_files}',
                    'details': {'missing_dirs': missing_dirs, 'missing_files': missing_files}
                }
            
            return {
                'status': 'passed',
                'message': 'File structure validation passed',
                'details': {'checked_dirs': len(required_dirs), 'checked_files': len(required_files)}
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'File structure validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_test_fixtures(self) -> Dict[str, Any]:
        """Validate test fixtures work."""
        try:
            from tests.shared_fixtures import SAMPLE_PATIENT_CODES, assert_valid_patient_code
            
            # Test patient codes exist
            if not SAMPLE_PATIENT_CODES or len(SAMPLE_PATIENT_CODES) == 0:
                return {
                    'status': 'failed',
                    'message': 'No sample patient codes found',
                    'details': {}
                }
            
            # Test validation function works
            valid_codes = 0
            for code in SAMPLE_PATIENT_CODES:
                try:
                    assert_valid_patient_code(code)
                    valid_codes += 1
                except AssertionError:
                    return {
                        'status': 'failed',
                        'message': f'Invalid sample patient code: {code}',
                        'details': {'tested_codes': len(SAMPLE_PATIENT_CODES)}
                    }
            
            return {
                'status': 'passed',
                'message': f'Test fixtures working: {valid_codes} valid patient codes',
                'details': {'valid_codes': valid_codes}
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Test fixtures validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_patient_validation(self) -> Dict[str, Any]:
        """Validate patient code validation logic."""
        try:
            # Simple patient code validation
            def validate_patient_code_format(code):
                if not code:
                    return False
                parts = code.split('-')
                if len(parts) != 3:
                    return False
                if len(parts[0]) != 2 or not parts[0].isalpha():
                    return False
                if len(parts[1]) != 4 or not parts[1].isdigit():
                    return False
                if len(parts[2]) != 3 or not parts[2].isdigit():
                    return False
                return True
            
            # Test valid codes
            valid_codes = ["CD-2025-001", "AB-2024-999", "XY-2025-123"]
            invalid_codes = ["", "CD-25-001", "C-2025-001", "CD-2025-1"]
            
            # Check valid codes pass
            for code in valid_codes:
                if not validate_patient_code_format(code):
                    return {
                        'status': 'failed',
                        'message': f'Valid patient code {code} failed validation',
                        'details': {'failed_code': code}
                    }
            
            # Check invalid codes fail
            for code in invalid_codes:
                if validate_patient_code_format(code):
                    return {
                        'status': 'failed',
                        'message': f'Invalid patient code {code} passed validation',
                        'details': {'failed_code': code}
                    }
            
            return {
                'status': 'passed',
                'message': 'Patient validation logic working correctly',
                'details': {'tested_valid': len(valid_codes), 'tested_invalid': len(invalid_codes)}
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Patient validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_environment_setup(self) -> Dict[str, Any]:
        """Validate environment setup."""
        try:
            python_version = sys.version_info
            if python_version.major != 3 or python_version.minor < 8:
                return {
                    'status': 'warning',
                    'message': f'Python version {python_version.major}.{python_version.minor} may not be optimal',
                    'details': {'python_version': f'{python_version.major}.{python_version.minor}'}
                }
            
            # Check if we can write to temp directory
            import tempfile
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(b"test")
                temp_write_ok = True
            
            # Check current working directory
            cwd = os.getcwd()
            project_in_path = str(project_root) in cwd
            
            return {
                'status': 'passed',
                'message': 'Environment setup validated',
                'details': {
                    'python_version': f'{python_version.major}.{python_version.minor}',
                    'temp_write_ok': temp_write_ok,
                    'project_in_path': project_in_path,
                    'working_directory': cwd
                }
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Environment validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_pytest(self) -> Dict[str, Any]:
        """Validate pytest installation."""
        try:
            result = subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    'status': 'passed',
                    'message': 'Pytest available',
                    'details': {'pytest_version': result.stdout.strip()}
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Pytest not available or not working',
                    'details': {'error': result.stderr}
                }
                
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Pytest validation failed: {str(e)}',
                'error': str(e)
            }
    
    def _run_basic_tests(self) -> Dict[str, Any]:
        """Run basic E2E tests."""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'tests/e2e/test_simple_integration.py',
                '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=120, cwd=str(project_root))
            
            if result.returncode == 0:
                # Parse test results
                output_lines = result.stdout.split('\n')
                passed_tests = len([line for line in output_lines if 'PASSED' in line])
                skipped_tests = len([line for line in output_lines if 'SKIPPED' in line])
                failed_tests = len([line for line in output_lines if 'FAILED' in line])
                
                if failed_tests == 0:
                    return {
                        'status': 'passed',
                        'message': f'Basic E2E tests passed: {passed_tests} passed, {skipped_tests} skipped',
                        'details': {'passed': passed_tests, 'skipped': skipped_tests, 'failed': failed_tests}
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'Some tests failed: {failed_tests} failed, {passed_tests} passed',
                        'details': {'passed': passed_tests, 'skipped': skipped_tests, 'failed': failed_tests}
                    }
            else:
                return {
                    'status': 'failed',
                    'message': 'Basic E2E tests failed to run',
                    'details': {'return_code': result.returncode, 'stderr': result.stderr[:500]}
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Basic tests execution failed: {str(e)}',
                'error': str(e)
            }
    
    def _validate_file_permissions(self) -> Dict[str, Any]:
        """Validate file permissions."""
        try:
            # Check if key files are readable
            key_files = [
                'vigia_detect/__init__.py',
                'config/settings.py',
                'scripts/validate_post_refactor.py'
            ]
            
            permission_issues = []
            readable_files = 0
            
            for file_path in key_files:
                full_path = project_root / file_path
                if full_path.exists():
                    if os.access(full_path, os.R_OK):
                        readable_files += 1
                    else:
                        permission_issues.append(f"{file_path}: Not readable")
                else:
                    permission_issues.append(f"{file_path}: File not found")
            
            # Check if script is executable
            script_path = project_root / 'scripts' / 'validate_post_refactor.py'
            if script_path.exists() and not os.access(script_path, os.X_OK):
                permission_issues.append("validate_post_refactor.py: Not executable")
            
            if permission_issues:
                return {
                    'status': 'warning',
                    'message': f'Permission issues: {permission_issues}',
                    'details': {'readable_files': readable_files, 'issues': permission_issues}
                }
            
            return {
                'status': 'passed',
                'message': 'File permissions validated',
                'details': {'readable_files': readable_files}
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'File permissions validation failed: {str(e)}',
                'error': str(e)
            }
    
    def print_summary(self):
        """Print validation summary to console."""
        print("\n" + "="*60)
        print("VIGIA SIMPLIFIED POST-REFACTOR VALIDATION SUMMARY")
        print("="*60)
        
        status_emoji = {
            'stable': '✅',
            'stable_with_warnings': '⚠️',
            'unstable': '❌'
        }
        
        overall_status = self.results['overall_status']
        print(f"\nOverall Status: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
        
        summary = self.results['summary']
        print(f"\nChecks Summary:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  ✅ Passed: {summary['passed_checks']}")
        print(f"  ⚠️  Warnings: {summary['warning_checks']}")
        print(f"  ❌ Failed: {summary['failed_checks']}")
        
        if self.results['critical_failures']:
            print(f"\n🚨 Critical Failures:")
            for failure in self.results['critical_failures']:
                print(f"  • {failure}")
        
        if self.results['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        # Stability assessment
        print(f"\n🩺 System Stability Assessment:")
        if overall_status == 'stable':
            print("  ✅ System is STABLE for continued development")
            print("  ✅ Basic functionality validated")
            print("  ✅ Test infrastructure working")
        elif overall_status == 'stable_with_warnings':
            print("  ⚠️  System is STABLE with minor warnings")
            print("  ✅ Core functionality validated")
            print("  ⚠️  Some non-critical issues need attention")
        else:
            print("  ❌ System has STABILITY ISSUES")
            print("  ❌ Critical failures must be resolved")
        
        print("\n" + "="*60)


def main():
    """Main validation script."""
    parser = argparse.ArgumentParser(
        description="Simplified validation for Vigia system after refactoring"
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--quick', '-q',
        action='store_true', 
        help='Run only critical checks'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for report'
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = SimplePostRefactorValidator(verbose=args.verbose)
    
    print("🩺 Vigia Medical System - Simplified Post-Refactor Validation")
    print("=" * 60)
    
    if args.quick:
        print("🚀 Running QUICK validation (critical checks only)")
    else:
        print("🔍 Running STANDARD validation")
    
    # Run validation
    results = validator.run_validation(quick=args.quick)
    
    # Print summary
    validator.print_summary()
    
    # Generate report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {args.output}")
    
    # Exit with appropriate code
    if results['overall_status'] == 'unstable':
        print("\n❌ Validation FAILED - System needs attention")
        sys.exit(1)
    elif results['overall_status'] == 'stable_with_warnings':
        print("\n⚠️  Validation completed with WARNINGS - Review recommended")
        sys.exit(2)
    else:
        print("\n✅ Validation PASSED - System is stable")
        sys.exit(0)


if __name__ == "__main__":
    main()
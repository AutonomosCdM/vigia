#!/usr/bin/env python3
"""
Comprehensive Security Audit Script for Vigia Medical AI System
Automated security assessment with medical compliance validation
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from vigia_detect.utils.security_validator import SecurityValidator
    from vigia_detect.utils.secrets_manager import VigiaSecretsManager
    HAS_VIGIA_SECURITY = True
except ImportError:
    HAS_VIGIA_SECURITY = False

logger = logging.getLogger(__name__)


class VigiaSecurityAuditor:
    """Comprehensive security auditor for Vigia Medical AI"""
    
    def __init__(self, project_root: Path):
        """Initialize security auditor"""
        self.project_root = project_root
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "project": "Vigia Medical AI System",
            "version": "1.4.1",
            "compliance_target": "HIPAA/ISO13485",
            "audits": {}
        }
        
        if HAS_VIGIA_SECURITY:
            self.security_validator = SecurityValidator()
            self.secrets_manager = VigiaSecretsManager()
        else:
            self.security_validator = None
            self.secrets_manager = None
    
    def audit_dependencies(self) -> Dict[str, Any]:
        """Audit Python dependencies for vulnerabilities"""
        print("🔍 Auditing dependencies for vulnerabilities...")
        
        result = {
            "status": "unknown",
            "vulnerabilities": [],
            "total_packages": 0,
            "tools_used": []
        }
        
        # Check if requirements file exists
        req_files = [
            "requirements-cloudrun.txt",
            "requirements.txt",
            "config/requirements.txt"
        ]
        
        requirements_file = None
        for req_file in req_files:
            if (self.project_root / req_file).exists():
                requirements_file = self.project_root / req_file
                break
        
        if not requirements_file:
            result["status"] = "error"
            result["error"] = "No requirements file found"
            return result
        
        # Run safety check
        try:
            safety_cmd = ["safety", "check", "-r", str(requirements_file), "--json"]
            safety_result = subprocess.run(
                safety_cmd, capture_output=True, text=True, timeout=60
            )
            
            if safety_result.returncode == 0:
                result["status"] = "clean"
                result["vulnerabilities"] = []
            else:
                try:
                    safety_data = json.loads(safety_result.stdout)
                    result["vulnerabilities"] = safety_data
                    result["status"] = "vulnerabilities_found"
                except json.JSONDecodeError:
                    result["status"] = "error"
                    result["error"] = "Failed to parse safety output"
            
            result["tools_used"].append("safety")
            
        except subprocess.TimeoutExpired:
            result["status"] = "error"
            result["error"] = "Safety check timed out"
        except FileNotFoundError:
            result["status"] = "error"
            result["error"] = "Safety tool not installed"
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Safety check failed: {str(e)}"
        
        # Count packages
        try:
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
                result["total_packages"] = len([
                    line for line in lines 
                    if line.strip() and not line.strip().startswith('#')
                ])
        except Exception:
            pass
        
        return result
    
    def audit_secrets(self) -> Dict[str, Any]:
        """Audit for hardcoded secrets and credentials"""
        print("🔍 Scanning for hardcoded secrets...")
        
        result = {
            "status": "unknown",
            "secrets_found": [],
            "files_scanned": 0,
            "patterns_checked": []
        }
        
        # Secret patterns to check
        secret_patterns = [
            (r'[Pp]assword\s*[:=]\s*[\'"][^\'"]+[\'"]', "Password"),
            (r'[Aa]pi[_-]?[Kk]ey\s*[:=]\s*[\'"][^\'"]+[\'"]', "API Key"),
            (r'[Ss]ecret[_-]?[Kk]ey\s*[:=]\s*[\'"][^\'"]+[\'"]', "Secret Key"),
            (r'[Tt]oken\s*[:=]\s*[\'"][^\'"]+[\'"]', "Token"),
            (r'[Aa]ccess[_-]?[Tt]oken\s*[:=]\s*[\'"][^\'"]+[\'"]', "Access Token"),
            (r'[Dd]atabase[_-]?[Uu]rl\s*[:=]\s*[\'"][^\'"]+[\'"]', "Database URL"),
            (r'redis://[^\s\'"]+', "Redis URL"),
            (r'postgresql://[^\s\'"]+', "PostgreSQL URL"),
            (r'mysql://[^\s\'"]+', "MySQL URL"),
            (r'mongodb://[^\s\'"]+', "MongoDB URL"),
            (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key"),
            (r'xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+', "Slack Bot Token"),
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
        ]
        
        result["patterns_checked"] = [pattern[1] for pattern in secret_patterns]
        
        # Files to scan
        python_files = list(self.project_root.glob("**/*.py"))
        config_files = list(self.project_root.glob("**/*.env*"))
        yaml_files = list(self.project_root.glob("**/*.yml")) + list(self.project_root.glob("**/*.yaml"))
        
        all_files = python_files + config_files + yaml_files
        
        # Exclude certain paths
        excluded_paths = [
            "__pycache__",
            ".git",
            "node_modules",
            ".env.example",
            "test_",
            "tests/"
        ]
        
        files_to_scan = []
        for file_path in all_files:
            if not any(excluded in str(file_path) for excluded in excluded_paths):
                files_to_scan.append(file_path)
        
        result["files_scanned"] = len(files_to_scan)
        
        # Scan files
        secrets_found = []
        for file_path in files_to_scan:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern, pattern_name in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip obvious examples/templates
                        matched_text = match.group(0)
                        if any(placeholder in matched_text.lower() for placeholder in [
                            "your-", "example", "placeholder", "xxxx", "****", 
                            "replace", "insert", "change", "update"
                        ]):
                            continue
                        
                        secrets_found.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "pattern": pattern_name,
                            "line": content[:match.start()].count('\n') + 1,
                            "match": matched_text[:50] + "..." if len(matched_text) > 50 else matched_text
                        })
            
            except Exception as e:
                logger.warning(f"Could not scan {file_path}: {e}")
        
        result["secrets_found"] = secrets_found
        result["status"] = "secrets_found" if secrets_found else "clean"
        
        return result
    
    def audit_configurations(self) -> Dict[str, Any]:
        """Audit configuration files for security issues"""
        print("🔍 Auditing configuration security...")
        
        result = {
            "status": "unknown",
            "issues": [],
            "configurations_checked": []
        }
        
        # Configuration files to check
        config_files = [
            ".env.example",
            "config/.env.example", 
            "config/.env.hospital",
            "deploy/docker/docker-compose.hospital.yml",
            "deploy/docker/docker-compose.yml",
            "requirements-cloudrun.txt"
        ]
        
        issues = []
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                result["configurations_checked"].append(config_file)
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check for insecure configurations
                    if "DEBUG=True" in content or "DEBUG=true" in content:
                        issues.append({
                            "file": config_file,
                            "issue": "Debug mode enabled",
                            "severity": "medium",
                            "description": "Debug mode should be disabled in production"
                        })
                    
                    if "allow_origins=['*']" in content or 'allow_origins=["*"]' in content:
                        issues.append({
                            "file": config_file,
                            "issue": "Permissive CORS configuration",
                            "severity": "medium",
                            "description": "CORS should restrict origins in production"
                        })
                    
                    if "SSL_VERIFY=False" in content or "ssl_verify=false" in content:
                        issues.append({
                            "file": config_file,
                            "issue": "SSL verification disabled",
                            "severity": "high",
                            "description": "SSL verification should be enabled for security"
                        })
                    
                    if "LOG_LEVEL=DEBUG" in content:
                        issues.append({
                            "file": config_file,
                            "issue": "Debug logging enabled",
                            "severity": "low",
                            "description": "Debug logging may expose sensitive information"
                        })
                
                except Exception as e:
                    logger.warning(f"Could not check {config_file}: {e}")
        
        result["issues"] = issues
        result["status"] = "issues_found" if issues else "clean"
        
        return result
    
    def audit_medical_compliance(self) -> Dict[str, Any]:
        """Audit medical compliance requirements"""
        print("🏥 Auditing medical compliance...")
        
        result = {
            "status": "unknown",
            "compliance_checks": {},
            "medical_grade": False
        }
        
        compliance_checks = {}
        
        # Check for HIPAA compliance markers
        hipaa_files = list(self.project_root.glob("**/*.py"))
        hipaa_mentions = 0
        for file_path in hipaa_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if "HIPAA" in content or "hipaa" in content:
                    hipaa_mentions += 1
            except Exception:
                pass
        
        compliance_checks["hipaa_compliance"] = {
            "implemented": hipaa_mentions > 0,
            "files_with_hipaa": hipaa_mentions,
            "description": "HIPAA compliance markers in code"
        }
        
        # Check for PHI protection
        phi_mentions = 0
        for file_path in hipaa_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if "PHI" in content or "phi" in content.lower():
                    phi_mentions += 1
            except Exception:
                pass
        
        compliance_checks["phi_protection"] = {
            "implemented": phi_mentions > 0,
            "files_with_phi": phi_mentions,
            "description": "Protected Health Information handling"
        }
        
        # Check for audit logging
        audit_files = [
            "vigia_detect/utils/audit_service.py",
            "vigia_detect/utils/secure_logger.py"
        ]
        
        audit_implemented = any(
            (self.project_root / audit_file).exists() 
            for audit_file in audit_files
        )
        
        compliance_checks["audit_logging"] = {
            "implemented": audit_implemented,
            "files_found": [f for f in audit_files if (self.project_root / f).exists()],
            "description": "Comprehensive audit trail implementation"
        }
        
        # Check for encryption
        encryption_patterns = ["encrypt", "Fernet", "AES", "cipher"]
        encryption_mentions = 0
        for file_path in hipaa_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                for pattern in encryption_patterns:
                    if pattern in content:
                        encryption_mentions += 1
                        break
            except Exception:
                pass
        
        compliance_checks["encryption"] = {
            "implemented": encryption_mentions > 0,
            "files_with_encryption": encryption_mentions,
            "description": "Data encryption implementation"
        }
        
        # Check for access control
        access_control_file = "vigia_detect/utils/access_control_matrix.py"
        access_control_implemented = (self.project_root / access_control_file).exists()
        
        compliance_checks["access_control"] = {
            "implemented": access_control_implemented,
            "description": "Role-based access control matrix"
        }
        
        # Determine overall medical grade compliance
        required_checks = ["hipaa_compliance", "phi_protection", "audit_logging", "encryption"]
        medical_grade = all(
            compliance_checks[check]["implemented"] 
            for check in required_checks
        )
        
        result["compliance_checks"] = compliance_checks
        result["medical_grade"] = medical_grade
        result["status"] = "compliant" if medical_grade else "non_compliant"
        
        return result
    
    def audit_permissions(self) -> Dict[str, Any]:
        """Audit file and directory permissions"""
        print("🔍 Auditing file permissions...")
        
        result = {
            "status": "unknown",
            "permission_issues": [],
            "files_checked": 0
        }
        
        permission_issues = []
        files_checked = 0
        
        # Check for overly permissive files
        sensitive_files = [
            "secrets/",
            ".env",
            "*.key",
            "*.pem", 
            "*.p12",
            "*.jks"
        ]
        
        for pattern in sensitive_files:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                files_checked += 1
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]
                    
                    # Check if file is readable by others
                    if mode[-1] in ['4', '5', '6', '7']:
                        permission_issues.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "mode": mode,
                            "issue": "File readable by others",
                            "severity": "high"
                        })
                    
                    # Check if file is writable by group/others
                    if mode[-2] in ['2', '3', '6', '7'] or mode[-1] in ['2', '3', '6', '7']:
                        permission_issues.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "mode": mode,
                            "issue": "File writable by group/others",
                            "severity": "medium"
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not check permissions for {file_path}: {e}")
        
        result["permission_issues"] = permission_issues
        result["files_checked"] = files_checked
        result["status"] = "issues_found" if permission_issues else "clean"
        
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security audit report"""
        print("📊 Generating security audit report...")
        
        # Run all audits
        self.results["audits"]["dependencies"] = self.audit_dependencies()
        self.results["audits"]["secrets"] = self.audit_secrets()
        self.results["audits"]["configurations"] = self.audit_configurations()
        self.results["audits"]["medical_compliance"] = self.audit_medical_compliance()
        self.results["audits"]["permissions"] = self.audit_permissions()
        
        # Calculate overall security score
        scores = []
        
        for audit_name, audit_result in self.results["audits"].items():
            if audit_result["status"] == "clean" or audit_result["status"] == "compliant":
                scores.append(100)
            elif audit_result["status"] == "issues_found" or audit_result["status"] == "non_compliant":
                # Score based on severity of issues
                if audit_name == "medical_compliance":
                    scores.append(50)  # Medical compliance is critical
                else:
                    scores.append(70)
            elif audit_result["status"] == "vulnerabilities_found":
                scores.append(30)
            else:
                scores.append(80)  # Unknown status
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Determine overall status
        if overall_score >= 90:
            overall_status = "excellent"
        elif overall_score >= 80:
            overall_status = "good"
        elif overall_score >= 70:
            overall_status = "fair"
        elif overall_score >= 60:
            overall_status = "poor"
        else:
            overall_status = "critical"
        
        self.results["summary"] = {
            "overall_score": round(overall_score, 1),
            "overall_status": overall_status,
            "medical_grade_compliant": self.results["audits"]["medical_compliance"]["medical_grade"],
            "critical_issues": sum(
                1 for audit in self.results["audits"].values()
                if audit["status"] in ["vulnerabilities_found", "secrets_found", "non_compliant"]
            ),
            "recommendations": self._generate_recommendations()
        }
        
        return self.results
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on audit results"""
        recommendations = []
        
        # Dependency recommendations
        deps = self.results["audits"]["dependencies"]
        if deps["status"] == "vulnerabilities_found":
            recommendations.append("Update vulnerable dependencies immediately")
        elif deps["status"] == "error":
            recommendations.append("Set up automated dependency vulnerability scanning")
        
        # Secrets recommendations
        secrets = self.results["audits"]["secrets"]
        if secrets["status"] == "secrets_found":
            recommendations.append("Remove hardcoded secrets and use environment variables")
            recommendations.append("Implement proper secrets management system")
        
        # Configuration recommendations
        configs = self.results["audits"]["configurations"]
        if configs["status"] == "issues_found":
            recommendations.append("Review and secure configuration files")
            recommendations.append("Disable debug mode in production")
        
        # Medical compliance recommendations
        medical = self.results["audits"]["medical_compliance"]
        if not medical["medical_grade"]:
            recommendations.append("Implement comprehensive HIPAA compliance measures")
            recommendations.append("Add PHI protection and encryption")
            recommendations.append("Set up audit logging for all medical operations")
        
        # Permission recommendations
        perms = self.results["audits"]["permissions"]
        if perms["status"] == "issues_found":
            recommendations.append("Restrict file permissions for sensitive files")
            recommendations.append("Review and update file access controls")
        
        # General recommendations
        recommendations.extend([
            "Set up automated security scanning in CI/CD pipeline",
            "Implement regular security audits and penetration testing",
            "Train development team on secure coding practices",
            "Establish incident response procedures"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def save_report(self, output_file: Optional[str] = None) -> str:
        """Save audit report to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"security_audit_report_{timestamp}.json"
        
        output_path = self.project_root / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Security audit report saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print audit summary to console"""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("🔒 VIGIA MEDICAL AI SECURITY AUDIT SUMMARY")
        print("="*60)
        print(f"Overall Security Score: {summary['overall_score']}/100 ({summary['overall_status'].upper()})")
        print(f"Medical Grade Compliant: {'✅ YES' if summary['medical_grade_compliant'] else '❌ NO'}")
        print(f"Critical Issues Found: {summary['critical_issues']}")
        
        print("\n📋 AUDIT RESULTS:")
        for audit_name, audit_result in self.results["audits"].items():
            status = audit_result["status"]
            icon = "✅" if status in ["clean", "compliant"] else "⚠️" if status in ["issues_found", "non_compliant"] else "❌"
            print(f"  {icon} {audit_name.replace('_', ' ').title()}: {status}")
        
        print("\n🔧 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(summary["recommendations"][:5], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive security audit for Vigia Medical AI System"
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for detailed report (JSON format)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--medical-only',
        action='store_true',
        help='Only run medical compliance checks'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Run audit
    auditor = VigiaSecurityAuditor(project_root)
    
    if args.medical_only:
        print("🏥 Running medical compliance audit only...")
        medical_result = auditor.audit_medical_compliance()
        print(f"Medical Grade Compliant: {'✅ YES' if medical_result['medical_grade'] else '❌ NO'}")
        
        for check_name, check_result in medical_result['compliance_checks'].items():
            status = "✅" if check_result['implemented'] else "❌"
            print(f"  {status} {check_name.replace('_', ' ').title()}")
        
        return 0 if medical_result['medical_grade'] else 1
    
    # Full audit
    print("🔒 Starting comprehensive security audit...")
    results = auditor.generate_report()
    
    # Save detailed report
    if args.output:
        auditor.save_report(args.output)
    else:
        auditor.save_report()
    
    # Print summary
    auditor.print_summary()
    
    # Return appropriate exit code
    if results["summary"]["overall_status"] in ["excellent", "good"]:
        return 0
    elif results["summary"]["overall_status"] == "fair":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
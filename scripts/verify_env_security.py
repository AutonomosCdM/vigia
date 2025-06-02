#!/usr/bin/env python3
"""
Verify environment variables security
Checks for exposed secrets and validates configuration
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns that might indicate secrets
SECRET_PATTERNS = [
    (r'[A-Za-z0-9+/]{40,}', 'Possible base64 encoded secret'),
    (r'[0-9a-f]{64}', 'Possible SHA256 hash or API key'),
    (r'[0-9a-f]{32}', 'Possible MD5 hash or token'),
    (r'sk_[A-Za-z0-9]{32,}', 'Possible Stripe key'),
    (r'pk_[A-Za-z0-9]{32,}', 'Possible public key'),
    (r'AC[0-9a-f]{32}', 'Possible Twilio Account SID'),
    (r'[0-9a-f]{32}', 'Possible auth token'),
]

# Files to check
CHECK_FILES = [
    '.env.template',
    'docker-compose.yml',
    'Dockerfile',
    'README.md',
    'RELEASE_NOTES_v1.0.0-rc1.md',
]

# Known safe patterns (to reduce false positives)
SAFE_PATTERNS = [
    'your_',
    'example',
    'placeholder',
    'template',
    '${',  # Environment variable reference
    'xxx',
    '...',
    'admin',  # Common default
]


def check_file_for_secrets(filepath: Path) -> List[Tuple[str, int, str, str]]:
    """
    Check a file for potential secrets
    
    Returns:
        List of (filename, line_number, content, warning)
    """
    findings = []
    
    if not filepath.exists():
        return findings
    
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Check if line contains any safe patterns
                if any(safe in line.lower() for safe in SAFE_PATTERNS):
                    continue
                
                # Check against secret patterns
                for pattern, description in SECRET_PATTERNS:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # Additional validation
                        if len(match) > 10 and not match.isdigit():
                            findings.append((
                                str(filepath),
                                line_num,
                                line[:80] + '...' if len(line) > 80 else line,
                                description
                            ))
                            break
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return findings


def check_env_files():
    """Check for .env files that shouldn't exist"""
    env_files = [
        '.env',
        '.env.production',
        '.env.local',
        '.env.development'
    ]
    
    found_env_files = []
    for env_file in env_files:
        if Path(env_file).exists():
            found_env_files.append(env_file)
    
    return found_env_files


def check_gitignore():
    """Verify .gitignore properly excludes sensitive files"""
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        return False, "No .gitignore file found!"
    
    required_patterns = [
        '.env',
        '.env.production',
        '.env.local',
        'credentials/',
        'secrets/',
    ]
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    return len(missing_patterns) == 0, missing_patterns


def main():
    """Main verification function"""
    print("🔒 Vigia Environment Security Check")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    issues_found = 0
    
    # Check for exposed .env files
    print("\n1. Checking for exposed .env files...")
    env_files = check_env_files()
    if env_files:
        print("❌ Found .env files that should not be committed:")
        for env_file in env_files:
            print(f"   - {env_file}")
        issues_found += len(env_files)
    else:
        print("✅ No exposed .env files found")
    
    # Check gitignore
    print("\n2. Checking .gitignore configuration...")
    gitignore_ok, missing = check_gitignore()
    if gitignore_ok:
        print("✅ .gitignore properly configured")
    else:
        print("❌ .gitignore missing important patterns:")
        for pattern in missing:
            print(f"   - {pattern}")
        issues_found += 1
    
    # Check files for secrets
    print("\n3. Checking files for potential secrets...")
    all_findings = []
    
    for file_pattern in CHECK_FILES:
        for filepath in Path('.').glob(file_pattern):
            findings = check_file_for_secrets(filepath)
            all_findings.extend(findings)
    
    if all_findings:
        print(f"⚠️  Found {len(all_findings)} potential security issues:")
        for filename, line_num, content, warning in all_findings:
            print(f"\n   File: {filename}:{line_num}")
            print(f"   Warning: {warning}")
            print(f"   Content: {content}")
        issues_found += len(all_findings)
    else:
        print("✅ No potential secrets found in checked files")
    
    # Check for hardcoded credentials in Python files
    print("\n4. Checking Python files for hardcoded credentials...")
    py_findings = []
    
    credential_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token'),
    ]
    
    for py_file in Path('vigia_detect').rglob('*.py'):
        # Skip test files
        if 'test' in str(py_file) or 'tests' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                for pattern, description in credential_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's actually hardcoded (not from env)
                        if 'os.environ' not in content and 'getenv' not in content:
                            py_findings.append((str(py_file), description))
                            break
        except:
            pass
    
    if py_findings:
        print(f"❌ Found hardcoded credentials in Python files:")
        for filename, issue in py_findings:
            print(f"   - {filename}: {issue}")
        issues_found += len(py_findings)
    else:
        print("✅ No hardcoded credentials found in Python files")
    
    # Summary
    print("\n" + "=" * 50)
    if issues_found == 0:
        print("✅ All security checks passed!")
        return 0
    else:
        print(f"❌ Found {issues_found} security issues. Please fix before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
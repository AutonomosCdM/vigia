#!/bin/bash
# Security analysis script for Vigia v1.0.0-rc1

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔒 Vigia Security Analysis${NC}"
echo "================================"

# Install security tools if not present
echo -e "\n${YELLOW}Installing security analysis tools...${NC}"
pip install -q bandit safety semgrep pip-audit pylint-security 2>/dev/null || true

# Create reports directory
mkdir -p security_reports

# Run Bandit for Python security
echo -e "\n${YELLOW}1. Running Bandit (Python Security Linter)...${NC}"
if command -v bandit &> /dev/null; then
    bandit -r vigia_detect/ -f json -o security_reports/bandit_report.json || true
    bandit -r vigia_detect/ -ll -i || true
else
    echo -e "${RED}Bandit not installed${NC}"
fi

# Run Safety for dependency vulnerabilities
echo -e "\n${YELLOW}2. Running Safety (Dependency Scanner)...${NC}"
if command -v safety &> /dev/null; then
    safety check --json --output security_reports/safety_report.json || true
    safety check || true
else
    echo -e "${RED}Safety not installed${NC}"
fi

# Run pip-audit
echo -e "\n${YELLOW}3. Running pip-audit (Vulnerability Scanner)...${NC}"
if command -v pip-audit &> /dev/null; then
    pip-audit --desc --format json --output security_reports/pip_audit_report.json || true
    pip-audit --desc || true
else
    echo -e "${RED}pip-audit not installed${NC}"
fi

# Run semgrep with OWASP rules
echo -e "\n${YELLOW}4. Running Semgrep (OWASP Security Patterns)...${NC}"
if command -v semgrep &> /dev/null; then
    semgrep --config=auto --json --output=security_reports/semgrep_report.json vigia_detect/ || true
    semgrep --config=auto vigia_detect/ || true
else
    echo -e "${RED}Semgrep not installed${NC}"
fi

# Check for common security issues
echo -e "\n${YELLOW}5. Custom Security Checks...${NC}"

# Check for hardcoded IPs
echo -e "\n  Checking for hardcoded IPs..."
grep -r -E '\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b' vigia_detect/ --include="*.py" | grep -v test | grep -v "127.0.0.1" | grep -v "0.0.0.0" || echo "  ✅ No hardcoded IPs found"

# Check for eval usage
echo -e "\n  Checking for eval() usage..."
grep -r "eval(" vigia_detect/ --include="*.py" | grep -v test || echo "  ✅ No eval() usage found"

# Check for pickle usage (can be insecure)
echo -e "\n  Checking for pickle usage..."
grep -r "pickle" vigia_detect/ --include="*.py" | grep -v test || echo "  ✅ No pickle usage found"

# Check for subprocess with shell=True
echo -e "\n  Checking for unsafe subprocess usage..."
grep -r "shell=True" vigia_detect/ --include="*.py" || echo "  ✅ No shell=True found"

# Check for SQL construction
echo -e "\n  Checking for potential SQL injection..."
grep -r -E "SELECT.*\+|INSERT.*\+|UPDATE.*\+|DELETE.*\+" vigia_detect/ --include="*.py" || echo "  ✅ No string concatenation in SQL found"

# Summary
echo -e "\n${GREEN}Security Analysis Complete!${NC}"
echo -e "Reports saved in: security_reports/"
echo -e "\nRecommended actions:"
echo -e "1. Review all findings in security_reports/"
echo -e "2. Fix any HIGH or CRITICAL issues before deployment"
echo -e "3. Document any false positives"
echo -e "4. Re-run this script after fixes"
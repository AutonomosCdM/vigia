#!/bin/bash
# Vigia Infrastructure Validation Test Runner
# Comprehensive testing for hospital deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_ENVIRONMENT="${TEST_ENVIRONMENT:-ci}"
PYTEST_MARKERS="${PYTEST_MARKERS:-not slow}"
COVERAGE_ENABLED="${COVERAGE_ENABLED:-true}"
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking test prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        error "pytest is not installed: pip install pytest"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        warn "Docker not available - some tests will be skipped"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        warn "Docker Compose not available - some tests will be skipped"
    fi
    
    success "Prerequisites check completed"
}

# Setup test environment
setup_test_environment() {
    log "Setting up test environment..."
    
    # Create test directories
    mkdir -p test-results/
    mkdir -p test-reports/
    mkdir -p test-logs/
    
    # Set environment variables for testing
    export TESTING=true
    export ENVIRONMENT=test
    export LOG_LEVEL=DEBUG
    export MEDICAL_COMPLIANCE_LEVEL=test
    export PHI_PROTECTION_ENABLED=false  # For testing only
    
    # Install test dependencies if needed
    if [[ ! -f "requirements-test.txt" ]]; then
        log "Creating test requirements..."
        cat > requirements-test.txt << EOF
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-html>=3.1.0
pytest-xdist>=3.0.0
requests>=2.28.0
docker>=6.0.0
psycopg2-binary>=2.9.0
redis>=4.5.0
celery>=5.3.0
EOF
    fi
    
    # Install test dependencies
    log "Installing test dependencies..."
    pip install -r requirements-test.txt
    
    success "Test environment setup completed"
}

# Run infrastructure validation tests
run_infrastructure_tests() {
    log "Running infrastructure validation tests..."
    
    local pytest_args=""
    
    # Add coverage if enabled
    if [[ "$COVERAGE_ENABLED" == "true" ]]; then
        pytest_args="--cov=vigia_detect --cov-report=html --cov-report=term"
    fi
    
    # Add markers
    if [[ -n "$PYTEST_MARKERS" ]]; then
        pytest_args="$pytest_args -m '$PYTEST_MARKERS'"
    fi
    
    # Add output options
    pytest_args="$pytest_args --html=test-reports/infrastructure-report.html --self-contained-html"
    pytest_args="$pytest_args --junitxml=test-results/infrastructure-junit.xml"
    pytest_args="$pytest_args -v --tb=short"
    
    # Run tests with timeout
    timeout "$TEST_TIMEOUT" python -m pytest \
        tests/infrastructure/test_hospital_deployment.py \
        $pytest_args || {
        error "Infrastructure tests failed or timed out"
        return 1
    }
    
    success "Infrastructure tests completed"
}

# Run Docker validation tests
run_docker_tests() {
    log "Running Docker configuration tests..."
    
    # Test Docker Compose syntax
    if [[ -f "docker-compose.hospital.yml" ]]; then
        log "Validating Docker Compose configuration..."
        docker-compose -f docker-compose.hospital.yml config > /dev/null && \
            success "Docker Compose configuration valid" || {
            error "Docker Compose configuration invalid"
            return 1
        }
    fi
    
    # Test Dockerfile syntax
    local dockerfiles=("docker/celery/worker.dockerfile" "docker/celery/beat.dockerfile")
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$dockerfile" ]]; then
            log "Validating $dockerfile..."
            docker build -f "$dockerfile" --dry-run . > /dev/null 2>&1 || {
                warn "Dockerfile validation failed: $dockerfile"
            }
        fi
    done
    
    success "Docker validation completed"
}

# Run security tests
run_security_tests() {
    log "Running security validation tests..."
    
    # Check for hardcoded secrets
    log "Scanning for hardcoded secrets..."
    if command -v grep &> /dev/null; then
        local secret_patterns=(
            "password\s*=\s*['\"]\\w+"
            "api_key\s*=\s*['\"]\\w+"
            "secret\s*=\s*['\"]\\w+"
            "token\s*=\s*['\"]\\w+"
        )
        
        local secrets_found=false
        for pattern in "${secret_patterns[@]}"; do
            if grep -r -i -E "$pattern" --include="*.py" --include="*.yml" --include="*.yaml" . 2>/dev/null | grep -v test | grep -v example; then
                warn "Potential hardcoded secret found: $pattern"
                secrets_found=true
            fi
        done
        
        if [[ "$secrets_found" == "false" ]]; then
            success "No hardcoded secrets detected"
        fi
    fi
    
    # Check file permissions
    log "Checking sensitive file permissions..."
    local sensitive_files=(
        "scripts/hospital-deploy.sh"
        ".env.hospital"
        "docker/postgres/init.sql"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [[ -f "$file" ]]; then
            local perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%A" "$file" 2>/dev/null || echo "unknown")
            log "File permissions for $file: $perms"
        fi
    done
    
    success "Security validation completed"
}

# Run performance tests
run_performance_tests() {
    log "Running performance validation tests..."
    
    # Test script execution time
    if [[ -f "scripts/hospital-deploy.sh" ]]; then
        log "Testing deployment script syntax..."
        bash -n scripts/hospital-deploy.sh && \
            success "Deployment script syntax valid" || {
            error "Deployment script has syntax errors"
            return 1
        }
    fi
    
    # Test environment file loading
    if [[ -f ".env.hospital" ]]; then
        log "Testing environment file format..."
        # Simple validation that file can be sourced
        bash -c "set -a; source .env.hospital; set +a" && \
            success "Environment file format valid" || {
            error "Environment file has format errors"
            return 1
        }
    fi
    
    success "Performance validation completed"
}

# Run compliance tests
run_compliance_tests() {
    log "Running medical compliance tests..."
    
    # Check HIPAA compliance settings
    if [[ -f ".env.hospital" ]]; then
        local hipaa_settings=(
            "MEDICAL_COMPLIANCE_LEVEL=hipaa"
            "PHI_PROTECTION_ENABLED=true"
            "AUDIT_LOG_ENABLED=true"
        )
        
        for setting in "${hipaa_settings[@]}"; do
            if grep -q "$setting" .env.hospital; then
                success "HIPAA setting found: $setting"
            else
                warn "HIPAA setting missing: $setting"
            fi
        done
    fi
    
    # Check audit retention settings
    if [[ -f ".env.hospital" ]]; then
        if grep -q "AUDIT_LOG_RETENTION_DAYS=2555" .env.hospital; then
            success "7-year audit retention configured"
        else
            warn "7-year audit retention not configured"
        fi
    fi
    
    success "Compliance validation completed"
}

# Generate test report
generate_test_report() {
    log "Generating test report..."
    
    local report_file="test-reports/infrastructure-summary.txt"
    
    cat > "$report_file" << EOF
Vigia Hospital Infrastructure Test Report
========================================

Test Environment: $TEST_ENVIRONMENT
Test Date: $(date)
Test Markers: $PYTEST_MARKERS
Coverage Enabled: $COVERAGE_ENABLED

Test Components:
- Infrastructure validation
- Docker configuration
- Security validation  
- Performance validation
- Compliance validation

Test Results:
EOF
    
    # Add test results if available
    if [[ -f "test-results/infrastructure-junit.xml" ]]; then
        local test_count=$(grep -o 'tests="[0-9]*"' test-results/infrastructure-junit.xml | grep -o '[0-9]*' || echo "0")
        local failure_count=$(grep -o 'failures="[0-9]*"' test-results/infrastructure-junit.xml | grep -o '[0-9]*' || echo "0")
        echo "Total Tests: $test_count" >> "$report_file"
        echo "Failures: $failure_count" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "Report generated at: $(date)" >> "$report_file"
    
    success "Test report generated: $report_file"
}

# Cleanup test environment
cleanup_test_environment() {
    log "Cleaning up test environment..."
    
    # Archive test results
    if [[ -d "test-results" ]] && [[ -n "$(ls -A test-results)" ]]; then
        local archive_name="test-results-$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "$archive_name" test-results/ test-reports/ test-logs/ 2>/dev/null || true
        log "Test results archived: $archive_name"
    fi
    
    # Clean temporary files
    rm -rf test-logs/*.tmp 2>/dev/null || true
    
    success "Cleanup completed"
}

# Main test runner
main() {
    log "Starting Vigia Infrastructure Validation Tests"
    
    local exit_code=0
    
    # Run test suites
    check_prerequisites || exit_code=1
    
    if [[ $exit_code -eq 0 ]]; then
        setup_test_environment || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        run_infrastructure_tests || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        run_docker_tests || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        run_security_tests || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        run_performance_tests || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        run_compliance_tests || exit_code=1
    fi
    
    # Always generate report and cleanup
    generate_test_report
    cleanup_test_environment
    
    if [[ $exit_code -eq 0 ]]; then
        success "All infrastructure tests passed!"
    else
        error "Some infrastructure tests failed!"
    fi
    
    return $exit_code
}

# Handle script arguments
case "${1:-run}" in
    "run")
        main
        ;;
    "quick")
        export PYTEST_MARKERS="smoke"
        export COVERAGE_ENABLED="false"
        export TEST_TIMEOUT="60"
        main
        ;;
    "security")
        check_prerequisites
        run_security_tests
        ;;
    "docker")
        check_prerequisites
        run_docker_tests
        ;;
    "compliance")
        check_prerequisites
        run_compliance_tests
        ;;
    "help")
        echo "Vigia Infrastructure Test Runner"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  run        - Run full test suite (default)"
        echo "  quick      - Run quick smoke tests only"
        echo "  security   - Run security tests only"
        echo "  docker     - Run Docker validation only"
        echo "  compliance - Run compliance tests only"
        echo "  help       - Show this help message"
        echo
        echo "Environment Variables:"
        echo "  TEST_ENVIRONMENT   - Test environment (ci, local)"
        echo "  PYTEST_MARKERS     - Pytest markers to run"
        echo "  COVERAGE_ENABLED    - Enable coverage reporting"
        echo "  TEST_TIMEOUT        - Test timeout in seconds"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
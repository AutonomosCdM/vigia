#!/bin/bash
# Vigia MCP Test Suite Runner
# Comprehensive testing for hybrid MCP deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
TEST_ENV="${TEST_ENV:-testing}"
COVERAGE_ENABLED="${COVERAGE_ENABLED:-true}"
PARALLEL_TESTS="${PARALLEL_TESTS:-true}"
TIMEOUT="${TIMEOUT:-600}"
REPORTS_DIR="${REPORTS_DIR:-test-reports}"

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

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

section() {
    echo -e "${CYAN}[SECTION]${NC} $1"
}

# Setup test environment
setup_test_environment() {
    log "Setting up MCP test environment..."
    
    # Create test directories
    mkdir -p "$REPORTS_DIR"/{infrastructure,integration,clinical}
    mkdir -p test-logs
    mkdir -p test-coverage
    
    # Set environment variables
    export TESTING=true
    export ENVIRONMENT=test
    export MCP_MODE=testing
    export MEDICAL_COMPLIANCE_LEVEL=test
    export PHI_PROTECTION_ENABLED=false  # For testing only
    export AUDIT_LOG_ENABLED=true
    
    # Install test dependencies
    if [[ ! -f "requirements-test.txt" ]]; then
        log "Creating test requirements..."
        cat > requirements-test.txt << 'EOF'
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-html>=3.1.0
pytest-xdist>=3.0.0
pytest-timeout>=2.1.0
pytest-mock>=3.10.0
aiohttp>=3.8.0
requests>=2.28.0
docker>=6.0.0
mock>=4.0.3
EOF
    fi
    
    # Install dependencies
    pip install -r requirements-test.txt >/dev/null 2>&1 || {
        warn "Could not install test dependencies automatically"
    }
    
    success "Test environment setup completed"
}

# 🧪 1. Infrastructure Tests (DevOps)
run_infrastructure_tests() {
    section "🧪 1. INFRASTRUCTURE TESTS (DevOps)"
    log "Running infrastructure and deployment tests..."
    
    local test_file="tests/infrastructure/test_mcp_deployment.py"
    local report_file="$REPORTS_DIR/infrastructure/infrastructure-report.html"
    local coverage_file="$REPORTS_DIR/infrastructure/coverage.xml"
    
    if [[ ! -f "$test_file" ]]; then
        error "Infrastructure test file not found: $test_file"
        return 1
    fi
    
    local pytest_args=(
        "$test_file"
        "-v"
        "--tb=short"
        "--html=$report_file"
        "--self-contained-html"
        "--timeout=$TIMEOUT"
        "-m" "not cleanup"  # Skip cleanup tests by default
    )
    
    if [[ "$COVERAGE_ENABLED" == "true" ]]; then
        pytest_args+=(
            "--cov=vigia_detect.mcp"
            "--cov-report=xml:$coverage_file"
            "--cov-report=term-missing"
        )
    fi
    
    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        pytest_args+=("-n" "auto")
    fi
    
    log "Test command: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        success "✅ Infrastructure tests PASSED"
        
        # Show key results
        if [[ -f "$report_file" ]]; then
            info "📊 Infrastructure report: $report_file"
        fi
        
        return 0
    else
        error "❌ Infrastructure tests FAILED"
        return 1
    fi
}

# 🧪 2. Integration Tests (MCP Tooling)
run_integration_tests() {
    section "🧪 2. INTEGRATION TESTS (MCP Tooling)"
    log "Running MCP integration and tooling tests..."
    
    local test_file="tests/integration/test_mcp_tooling.py"
    local report_file="$REPORTS_DIR/integration/integration-report.html"
    local coverage_file="$REPORTS_DIR/integration/coverage.xml"
    
    if [[ ! -f "$test_file" ]]; then
        error "Integration test file not found: $test_file"
        return 1
    fi
    
    local pytest_args=(
        "$test_file"
        "-v"
        "--tb=short"
        "--html=$report_file"
        "--self-contained-html"
        "--timeout=$TIMEOUT"
    )
    
    if [[ "$COVERAGE_ENABLED" == "true" ]]; then
        pytest_args+=(
            "--cov=vigia_detect.mcp"
            "--cov-report=xml:$coverage_file"
            "--cov-report=term-missing"
        )
    fi
    
    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        pytest_args+=("-n" "auto")
    fi
    
    log "Test command: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        success "✅ Integration tests PASSED"
        
        # Show key results
        if [[ -f "$report_file" ]]; then
            info "📊 Integration report: $report_file"
        fi
        
        return 0
    else
        error "❌ Integration tests FAILED"
        return 1
    fi
}

# 🧪 3. Clinical Tests (Custom MCPs)
run_clinical_tests() {
    section "🧪 3. CLINICAL TESTS (Custom MCPs)"
    log "Running clinical and functional tests for medical MCP servers..."
    
    local test_file="tests/clinical/test_mcp_medical_functions.py"
    local report_file="$REPORTS_DIR/clinical/clinical-report.html"
    local coverage_file="$REPORTS_DIR/clinical/coverage.xml"
    
    if [[ ! -f "$test_file" ]]; then
        error "Clinical test file not found: $test_file"
        return 1
    fi
    
    local pytest_args=(
        "$test_file"
        "-v"
        "--tb=short"
        "--html=$report_file"
        "--self-contained-html"
        "--timeout=$TIMEOUT"
    )
    
    if [[ "$COVERAGE_ENABLED" == "true" ]]; then
        pytest_args+=(
            "--cov=vigia_detect.mcp"
            "--cov-report=xml:$coverage_file"
            "--cov-report=term-missing"
        )
    fi
    
    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        pytest_args+=("-n" "auto")
    fi
    
    log "Test command: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        success "✅ Clinical tests PASSED"
        
        # Show key results
        if [[ -f "$report_file" ]]; then
            info "📊 Clinical report: $report_file"
        fi
        
        return 0
    else
        error "❌ Clinical tests FAILED"
        return 1
    fi
}

# Performance tests
run_performance_tests() {
    section "⚡ PERFORMANCE TESTS"
    log "Running performance tests for MCP services..."
    
    local pytest_args=(
        "tests/"
        "-v"
        "-m" "performance"
        "--tb=short"
        "--html=$REPORTS_DIR/performance-report.html"
        "--self-contained-html"
        "--timeout=$TIMEOUT"
    )
    
    if python -m pytest "${pytest_args[@]}"; then
        success "✅ Performance tests PASSED"
        return 0
    else
        warn "⚠️ Performance tests had issues (non-critical)"
        return 0  # Don't fail on performance issues
    fi
}

# Security tests
run_security_tests() {
    section "🔒 SECURITY TESTS"
    log "Running security and compliance tests..."
    
    # Run specific security test markers
    local pytest_args=(
        "tests/"
        "-v"
        "-m" "security or compliance"
        "--tb=short"
        "--html=$REPORTS_DIR/security-report.html"
        "--self-contained-html"
        "--timeout=$TIMEOUT"
    )
    
    if python -m pytest "${pytest_args[@]}"; then
        success "✅ Security tests PASSED"
        return 0
    else
        error "❌ Security tests FAILED"
        return 1
    fi
}

# Quick smoke tests
run_smoke_tests() {
    section "💨 SMOKE TESTS"
    log "Running quick smoke tests..."
    
    local pytest_args=(
        "tests/"
        "-v"
        "-m" "smoke"
        "--tb=line"
        "--timeout=60"
    )
    
    if python -m pytest "${pytest_args[@]}"; then
        success "✅ Smoke tests PASSED"
        return 0
    else
        error "❌ Smoke tests FAILED"
        return 1
    fi
}

# Generate comprehensive test report
generate_test_report() {
    log "Generating comprehensive test report..."
    
    local report_file="$REPORTS_DIR/mcp-test-summary.html"
    
    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Vigia MCP Test Suite Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f8ff; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; }
        .pass { color: #28a745; font-weight: bold; }
        .fail { color: #dc3545; font-weight: bold; }
        .warn { color: #ffc107; font-weight: bold; }
        .test-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 20px 0; }
        .test-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .links { margin: 10px 0; }
        .links a { margin-right: 15px; color: #007acc; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Vigia MCP Test Suite Results</h1>
        <p><strong>Test Run:</strong> TIMESTAMP_PLACEHOLDER</p>
        <p><strong>Environment:</strong> ENVIRONMENT_PLACEHOLDER</p>
        <p><strong>Coverage Enabled:</strong> COVERAGE_PLACEHOLDER</p>
    </div>

    <div class="test-grid">
        <div class="test-card">
            <h3>🧪 1. Infrastructure Tests</h3>
            <p><strong>Status:</strong> <span class="STATUS_INFRA">STATUS_INFRA_PLACEHOLDER</span></p>
            <p><strong>Focus:</strong> Docker deployment, networks, secrets, health checks</p>
            <div class="links">
                <a href="infrastructure/infrastructure-report.html">📊 Detailed Report</a>
                <a href="infrastructure/coverage.xml">📈 Coverage</a>
            </div>
        </div>

        <div class="test-card">
            <h3>🧪 2. Integration Tests</h3>
            <p><strong>Status:</strong> <span class="STATUS_INTEGRATION">STATUS_INTEGRATION_PLACEHOLDER</span></p>
            <p><strong>Focus:</strong> MCP gateway, Hub + Custom service interaction</p>
            <div class="links">
                <a href="integration/integration-report.html">📊 Detailed Report</a>
                <a href="integration/coverage.xml">📈 Coverage</a>
            </div>
        </div>

        <div class="test-card">
            <h3>🧪 3. Clinical Tests</h3>
            <p><strong>Status:</strong> <span class="STATUS_CLINICAL">STATUS_CLINICAL_PLACEHOLDER</span></p>
            <p><strong>Focus:</strong> Medical MCP servers, LPP detection, FHIR integration</p>
            <div class="links">
                <a href="clinical/clinical-report.html">📊 Detailed Report</a>
                <a href="clinical/coverage.xml">📈 Coverage</a>
            </div>
        </div>
    </div>

    <div class="section">
        <h3>🎯 Test Summary</h3>
        <ul>
            <li><strong>Infrastructure:</strong> Docker deployment, secrets, networks, health checks</li>
            <li><strong>Integration:</strong> MCP gateway routing, Hub + Custom service communication</li>
            <li><strong>Clinical:</strong> LPP detection accuracy, FHIR compliance, medical workflows</li>
            <li><strong>Security:</strong> PHI protection, audit trails, compliance validation</li>
            <li><strong>Performance:</strong> Response times, concurrent requests, resource usage</li>
        </ul>
    </div>

    <div class="section">
        <h3>📋 Next Steps</h3>
        <ul>
            <li>Review failed tests and address issues</li>
            <li>Check coverage reports for gaps</li>
            <li>Validate medical compliance requirements</li>
            <li>Test deployment in staging environment</li>
            <li>Schedule regular test runs in CI/CD pipeline</li>
        </ul>
    </div>

    <div class="section">
        <h3>🔗 Additional Resources</h3>
        <div class="links">
            <a href="performance-report.html">⚡ Performance Tests</a>
            <a href="security-report.html">🔒 Security Tests</a>
            <a href="../CLAUDE.md">📚 Documentation</a>
            <a href="../scripts/deploy-mcp-hybrid.sh">🚀 Deployment Script</a>
        </div>
    </div>
</body>
</html>
EOF

    # Replace placeholders
    sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$(date)/" "$report_file"
    sed -i.bak "s/ENVIRONMENT_PLACEHOLDER/$TEST_ENV/" "$report_file"
    sed -i.bak "s/COVERAGE_PLACEHOLDER/$COVERAGE_ENABLED/" "$report_file"
    
    # Clean up backup file
    rm -f "$report_file.bak"
    
    success "📊 Test report generated: $report_file"
}

# Update test status in report
update_test_status() {
    local test_type=$1
    local status=$2
    local report_file="$REPORTS_DIR/mcp-test-summary.html"
    
    if [[ -f "$report_file" ]]; then
        local status_class
        case $status in
            "PASSED") status_class="pass" ;;
            "FAILED") status_class="fail" ;;
            *) status_class="warn" ;;
        esac
        
        sed -i.bak "s/STATUS_${test_type}_PLACEHOLDER/<span class=\"$status_class\">$status<\/span>/" "$report_file"
        sed -i.bak "s/STATUS_${test_type}//" "$report_file"
        rm -f "$report_file.bak"
    fi
}

# Cleanup test environment
cleanup_test_environment() {
    log "Cleaning up test environment..."
    
    # Archive test results if they exist
    if [[ -d "$REPORTS_DIR" ]] && [[ -n "$(ls -A "$REPORTS_DIR")" ]]; then
        local archive_name="mcp-test-results-$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "$archive_name" "$REPORTS_DIR" test-logs 2>/dev/null || true
        log "Test results archived: $archive_name"
    fi
    
    # Clean temporary files
    rm -rf test-logs/*.tmp 2>/dev/null || true
    
    success "Cleanup completed"
}

# Show final test summary
show_test_summary() {
    log "=== VIGIA MCP TEST SUITE SUMMARY ==="
    
    local total_tests=0
    local passed_tests=0
    
    # Count test results
    if [[ $infrastructure_result -eq 0 ]]; then
        ((passed_tests++))
        success "✅ Infrastructure Tests: PASSED"
    else
        error "❌ Infrastructure Tests: FAILED"
    fi
    ((total_tests++))
    
    if [[ $integration_result -eq 0 ]]; then
        ((passed_tests++))
        success "✅ Integration Tests: PASSED"
    else
        error "❌ Integration Tests: FAILED"
    fi
    ((total_tests++))
    
    if [[ $clinical_result -eq 0 ]]; then
        ((passed_tests++))
        success "✅ Clinical Tests: PASSED"
    else
        error "❌ Clinical Tests: FAILED"
    fi
    ((total_tests++))
    
    # Summary
    local success_rate=$((passed_tests * 100 / total_tests))
    
    echo ""
    info "📊 Test Results: $passed_tests/$total_tests passed ($success_rate%)"
    
    if [[ $passed_tests -eq $total_tests ]]; then
        success "🎉 ALL MCP TESTS PASSED! Vigia hybrid MCP system is ready for deployment."
    else
        warn "⚠️ Some tests failed. Please review and fix issues before deployment."
    fi
    
    # Show reports
    echo ""
    info "📋 Test Reports:"
    echo "  📊 Summary Report: $REPORTS_DIR/mcp-test-summary.html"
    echo "  🧪 Infrastructure: $REPORTS_DIR/infrastructure/infrastructure-report.html"
    echo "  🔗 Integration: $REPORTS_DIR/integration/integration-report.html"
    echo "  🏥 Clinical: $REPORTS_DIR/clinical/clinical-report.html"
    
    # Usage examples
    echo ""
    info "🚀 Next Steps:"
    echo "  # Deploy MCP hybrid system"
    echo "  ./scripts/deploy-mcp-hybrid.sh deploy"
    echo ""
    echo "  # Run specific test category"
    echo "  ./scripts/run-mcp-tests.sh infrastructure"
    echo "  ./scripts/run-mcp-tests.sh integration"
    echo "  ./scripts/run-mcp-tests.sh clinical"
}

# Main test runner
main() {
    local test_category="${1:-all}"
    
    # Global result variables
    infrastructure_result=1
    integration_result=1
    clinical_result=1
    
    case $test_category in
        "all")
            log "Running complete MCP test suite..."
            setup_test_environment
            generate_test_report
            
            # Run all test categories
            run_infrastructure_tests && infrastructure_result=0
            update_test_status "INFRA" "$([ $infrastructure_result -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
            
            run_integration_tests && integration_result=0
            update_test_status "INTEGRATION" "$([ $integration_result -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
            
            run_clinical_tests && clinical_result=0
            update_test_status "CLINICAL" "$([ $clinical_result -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
            
            # Optional tests (don't affect main result)
            run_performance_tests || true
            run_security_tests || true
            
            show_test_summary
            cleanup_test_environment
            
            # Return overall result
            if [[ $infrastructure_result -eq 0 && $integration_result -eq 0 && $clinical_result -eq 0 ]]; then
                return 0
            else
                return 1
            fi
            ;;
        "infrastructure"|"infra")
            setup_test_environment
            run_infrastructure_tests
            ;;
        "integration"|"tooling")
            setup_test_environment
            run_integration_tests
            ;;
        "clinical"|"medical")
            setup_test_environment
            run_clinical_tests
            ;;
        "performance"|"perf")
            setup_test_environment
            run_performance_tests
            ;;
        "security"|"sec")
            setup_test_environment
            run_security_tests
            ;;
        "smoke")
            setup_test_environment
            run_smoke_tests
            ;;
        "help")
            echo "Vigia MCP Test Suite Runner"
            echo ""
            echo "Usage: $0 [category]"
            echo ""
            echo "Categories:"
            echo "  all            - Run complete test suite (default)"
            echo "  infrastructure - Run infrastructure/DevOps tests only"
            echo "  integration    - Run MCP tooling integration tests only"
            echo "  clinical       - Run clinical/medical function tests only"
            echo "  performance    - Run performance tests only"
            echo "  security       - Run security/compliance tests only"
            echo "  smoke          - Run quick smoke tests only"
            echo "  help           - Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  TEST_ENV           - Test environment (testing, ci)"
            echo "  COVERAGE_ENABLED   - Enable coverage reporting (true/false)"
            echo "  PARALLEL_TESTS     - Run tests in parallel (true/false)"
            echo "  TIMEOUT            - Test timeout in seconds"
            echo "  REPORTS_DIR        - Directory for test reports"
            ;;
        *)
            error "Unknown test category: $test_category"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup_test_environment INT TERM

# Run main function
main "$@"
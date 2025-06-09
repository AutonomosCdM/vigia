#!/bin/bash

# Medical Test Suite Runner for Vigia
# ===================================
# Runs comprehensive medical testing with 120+ synthetic patients
# Generates detailed medical compliance and accuracy reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DIR="$PROJECT_DIR/tests/medical"
RESULTS_DIR="$TEST_DIR/results"
PYTHON_CMD="python"

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}🏥 VIGIA MEDICAL TEST SUITE${NC}"
echo -e "${BLUE}===========================${NC}"
echo -e "Testing medical decision-making with 120+ synthetic patients"
echo -e "Project: $PROJECT_DIR"
echo -e "Results: $RESULTS_DIR"
echo ""

# Function to run test with timing and error handling
run_test_suite() {
    local test_name="$1"
    local test_file="$2"
    local description="$3"
    
    echo -e "${CYAN}📋 Running: $test_name${NC}"
    echo -e "   $description"
    
    start_time=$(date +%s)
    
    if cd "$PROJECT_DIR" && $PYTHON_CMD -m pytest "$test_file" -v --tb=short -x; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}✅ $test_name completed successfully (${duration}s)${NC}"
        return 0
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${RED}❌ $test_name failed (${duration}s)${NC}"
        return 1
    fi
}

# Function to run comprehensive cohort test
run_cohort_test() {
    echo -e "${PURPLE}🧬 COMPREHENSIVE COHORT ANALYSIS${NC}"
    echo -e "   Testing complete medical workflow with 120+ synthetic patients"
    echo -e "   This may take 5-10 minutes..."
    echo ""
    
    start_time=$(date +%s)
    
    if cd "$PROJECT_DIR" && $PYTHON_CMD -m pytest tests/medical/test_medical_cohort_runner.py::test_comprehensive_medical_cohort -v -s --tb=short; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}✅ Comprehensive cohort test completed successfully (${duration}s)${NC}"
        
        # Show latest results
        latest_report=$(ls -t "$RESULTS_DIR"/medical_cohort_report_*.json 2>/dev/null | head -1)
        if [[ -n "$latest_report" ]]; then
            echo -e "${CYAN}📊 Latest report: $(basename "$latest_report")${NC}"
        fi
        
        return 0
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${RED}❌ Comprehensive cohort test failed (${duration}s)${NC}"
        return 1
    fi
}

# Function to display medical test summary
display_test_summary() {
    local total_tests=$1
    local passed_tests=$2
    local failed_tests=$3
    
    echo ""
    echo -e "${BLUE}📊 MEDICAL TEST SUMMARY${NC}"
    echo -e "${BLUE}======================${NC}"
    echo -e "Total Test Suites: $total_tests"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    
    if [[ $failed_tests -gt 0 ]]; then
        echo -e "${RED}Failed: $failed_tests${NC}"
        echo -e "${YELLOW}⚠️  Some medical tests failed - system may not be ready for clinical use${NC}"
    else
        echo -e "${GREEN}Failed: $failed_tests${NC}"
        echo -e "${GREEN}🎉 All medical tests passed - system meets clinical safety standards${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}📁 Check detailed results in: $RESULTS_DIR${NC}"
}

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python not found${NC}"
        exit 1
    fi
    
    # Check pytest
    if ! $PYTHON_CMD -c "import pytest" 2>/dev/null; then
        echo -e "${RED}❌ pytest not installed${NC}"
        echo -e "Install with: pip install pytest"
        exit 1
    fi
    
    # Check project structure
    if [[ ! -d "$TEST_DIR" ]]; then
        echo -e "${RED}❌ Medical test directory not found: $TEST_DIR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies check passed${NC}"
    echo ""
}

# Main execution
main() {
    local test_mode="${1:-all}"
    
    check_dependencies
    
    # Test counters
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    case "$test_mode" in
        "all")
            echo -e "${YELLOW}Running all medical test suites...${NC}"
            echo ""
            
            # Individual test suites
            if run_test_suite "LPP Medical Agent" "tests/medical/test_lpp_medical_agent.py" "Tests LPP classification and medical recommendations"; then
                ((passed_tests++))
            else
                ((failed_tests++))
            fi
            ((total_tests++))
            echo ""
            
            if run_test_suite "Medical Dispatcher" "tests/medical/test_medical_dispatcher.py" "Tests medical triage and routing decisions"; then
                ((passed_tests++))
            else
                ((failed_tests++))
            fi
            ((total_tests++))
            echo ""
            
            if run_test_suite "Clinical Processing" "tests/medical/test_clinical_processing.py" "Tests end-to-end clinical workflow"; then
                ((passed_tests++))
            else
                ((failed_tests++))
            fi
            ((total_tests++))
            echo ""
            
            # Comprehensive cohort test
            if run_cohort_test; then
                ((passed_tests++))
            else
                ((failed_tests++))
            fi
            ((total_tests++))
            ;;
            
        "cohort")
            echo -e "${YELLOW}Running comprehensive cohort test only...${NC}"
            echo ""
            total_tests=1
            if run_cohort_test; then
                passed_tests=1
            else
                failed_tests=1
            fi
            ;;
            
        "quick")
            echo -e "${YELLOW}Running quick medical tests (no cohort)...${NC}"
            echo ""
            
            if run_test_suite "LPP Medical Agent" "tests/medical/test_lpp_medical_agent.py" "Tests LPP classification logic"; then
                ((passed_tests++))
            else
                ((failed_tests++))
            fi
            ((total_tests++))
            ;;
            
        *)
            echo -e "${RED}❌ Unknown test mode: $test_mode${NC}"
            echo -e "Usage: $0 [all|cohort|quick]"
            echo -e "  all    - Run all medical tests including cohort analysis (default)"
            echo -e "  cohort - Run only comprehensive 120-patient cohort test"
            echo -e "  quick  - Run only essential medical tests (fast)"
            exit 1
            ;;
    esac
    
    display_test_summary $total_tests $passed_tests $failed_tests
    
    # Exit with error if any tests failed
    if [[ $failed_tests -gt 0 ]]; then
        exit 1
    fi
}

# Handle script arguments
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
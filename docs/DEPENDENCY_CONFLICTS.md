# Dependency Conflicts Analysis

## Overview

This document details the dependency conflicts found in the Vigia project and provides recommendations for resolution.

## Conflict Categories

### 1. Critical Conflicts (Affecting Core Functionality)

#### lpp-detection Package
- **Issue**: Outdated version constraints
- **Conflicts**:
  - Requires `fastapi<0.96.0` but have `0.115.12`
  - Requires `pandas<3.0.0,>=2.0.0` but have `1.5.3`
  - Requires `uvicorn<0.22.0` but have `0.34.2`
- **Impact**: HIGH - This is our core detection package
- **Solution**: Update lpp-detection requirements or use compatibility mode

#### Pydantic Version Mismatch
- **Issue**: Multiple packages require `pydantic>=2.10` but have `2.9.2`
- **Affected Packages**:
  - openai-agents
  - pydantic-ai-slim
  - pydantic-graph
  - pydantic-evals
  - mistralai
  - airtrain
  - mcp-agent
- **Impact**: MEDIUM - May cause validation issues
- **Solution**: Upgrade pydantic to 2.10.x

### 2. Minor Conflicts (Low Impact)

#### Rich Terminal Formatting
- **Conflicts**: Multiple packages require `rich<14.0.0` but have `14.0.0`
- **Affected**: instructor, together, embedchain, composio-core
- **Impact**: LOW - Only affects terminal output formatting
- **Solution**: Pin rich to 13.9.x if issues arise

#### OpenCV Version
- **Conflicts**: albumentations requires `opencv-python-headless>=4.9.0.80` but have `4.5.5.64`
- **Impact**: LOW - Only if using advanced image augmentation
- **Solution**: Upgrade opencv-python-headless if needed

### 3. Development Tool Conflicts

#### OpenTelemetry Instrumentation
- **Issue**: Version mismatch in instrumentation packages
- **Impact**: LOW - Only affects observability features
- **Solution**: Align all opentelemetry packages to same version

## Recommended Actions

### Immediate (Before Production)

1. **Update pydantic**:
   ```bash
   pip install "pydantic>=2.10,<3.0"
   ```

2. **Review lpp-detection compatibility**:
   - Check if newer version available
   - Or create compatibility layer for FastAPI/uvicorn

### Short-term (Within 1 Week)

1. **Align package versions**:
   ```bash
   # Create updated requirements
   pip freeze > requirements.current.txt
   # Review and update constraints
   ```

2. **Test with updated dependencies**:
   ```bash
   pytest tests/
   ```

### Long-term (Within 1 Month)

1. **Dependency Management Strategy**:
   - Use pip-tools for better dependency resolution
   - Implement regular dependency audits
   - Set up automated dependency updates

## Resolution Script

```bash
#!/bin/bash
# Fix critical dependencies

# Backup current environment
pip freeze > requirements.backup.txt

# Update critical packages
pip install --upgrade "pydantic>=2.10,<3.0"
pip install --upgrade "rich>=13.7.0,<14.0"

# Test core functionality
python -m pytest tests/unit/test_core.py

# If tests pass, update requirements
pip freeze > requirements.updated.txt
```

## Conflict Resolution Priority

1. **P0 - Critical**: lpp-detection compatibility
2. **P1 - High**: pydantic version alignment
3. **P2 - Medium**: OpenCV for image processing
4. **P3 - Low**: Rich, OpenTelemetry, other formatting tools

## Testing After Resolution

```bash
# Run core tests
pytest tests/unit/
pytest tests/integration/

# Test detection pipeline
python vigia_detect/cli/process_images.py --test

# Test messaging integrations
python vigia_detect/test_slack.py
python vigia_detect/test_workflow.py
```

## Notes

- Most conflicts are version mismatches rather than incompatibilities
- The system currently works despite these conflicts
- Resolution will improve stability and prevent future issues
- Consider using virtual environments for different components
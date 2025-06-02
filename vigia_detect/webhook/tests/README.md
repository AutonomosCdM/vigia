# Webhook Integration Tests

This directory contains comprehensive tests for the Vigia webhook system.

## Test Structure

### Test Files

- **`test_models.py`** - Tests for data models and serialization
- **`test_client.py`** - Tests for webhook client functionality
- **`test_server.py`** - Tests for webhook server functionality  
- **`test_handlers.py`** - Tests for event handlers
- **`test_integration.py`** - End-to-end integration tests

### Test Configuration

- **`conftest.py`** - Pytest fixtures and configuration
- **`pytest.ini`** - Pytest settings and markers

## Running Tests

### Quick Start

```bash
# Run all tests
python scripts/run_webhook_tests.py

# Run only unit tests (fast)
python scripts/run_webhook_tests.py --type unit

# Run only integration tests
python scripts/run_webhook_tests.py --type integration

# Verbose output
python scripts/run_webhook_tests.py -v
```

### Using pytest directly

```bash
# From webhook directory
cd vigia_detect/webhook
pytest tests/

# Run specific test file
pytest tests/test_models.py

# Run with markers
pytest tests/ -m unit
pytest tests/ -m integration
```

## Test Categories

### Unit Tests (`-m unit`)
- Fast tests that don't require external services
- Test individual components in isolation
- Use mocks for dependencies

### Integration Tests (`-m integration`)
- Test complete workflows
- May start real servers on test ports
- Test actual HTTP communication
- Slower but more comprehensive

### Async Tests (`-m async`)
- Tests for async functionality
- Automatically marked by pytest configuration

## Test Coverage

The tests cover:

- ✅ **Models**: Data structures and serialization
- ✅ **Client**: HTTP client with retry logic and authentication
- ✅ **Server**: FastAPI webhook server with routing
- ✅ **Handlers**: Event processing and business logic
- ✅ **Integration**: End-to-end workflows
- ✅ **Error Handling**: Network failures, authentication errors
- ✅ **Concurrency**: Multiple simultaneous requests

## Example Test Scenarios

### Detection Workflow
```python
# 1. Client sends detection event
# 2. Server receives and validates
# 3. Handler processes with business logic
# 4. Response confirms processing
```

### Error Scenarios
```python
# - Invalid authentication
# - Network timeouts
# - Handler exceptions
# - Malformed payloads
```

### Real-world Integration
```python
# - Medical emergency protocols
# - Multi-step workflows
# - External service communication
```

## Mocking Strategy

Tests use mocks for:
- External HTTP services
- Database connections
- Slack/WhatsApp notifications
- Redis caching

This ensures tests:
- Run fast and reliably
- Don't require external dependencies
- Can simulate error conditions

## Test Data

Sample payloads and fixtures are provided for:
- Critical pressure injury detections
- Patient status updates
- Protocol activations
- Analysis completions

## Continuous Integration

Tests are designed to run in CI environments:
- No external service dependencies
- Deterministic results
- Clear pass/fail status
- Detailed error reporting

## Adding New Tests

### For new models:
1. Add to `test_models.py`
2. Test creation, serialization, validation

### For new client features:
1. Add to `test_client.py`
2. Mock HTTP responses
3. Test success and error cases

### For new handlers:
1. Add to `test_handlers.py`
2. Mock external integrations
3. Test business logic

### For new workflows:
1. Add to `test_integration.py`
2. Test complete end-to-end flow
3. Verify all components work together

## Debugging Tests

```bash
# Run with full output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run specific test
pytest tests/test_client.py::TestWebhookClient::test_send_async_success

# Debug with pdb
pytest tests/ --pdb
```

## Performance Testing

Integration tests include:
- Concurrent request handling
- Large payload processing
- Network resilience testing
- Server resource usage

## Dependencies

Required packages:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `aiohttp` - HTTP client testing
- `fastapi` - Server testing
- `requests` - Integration test HTTP calls

Install with:
```bash
pip install pytest pytest-asyncio aiohttp fastapi uvicorn requests
```
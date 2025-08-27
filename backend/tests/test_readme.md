# Story to Image Generator API - Testing Guide

This guide covers how to run and understand the test suite for the Story to Image Generator API.

## 📋 Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_analysis.py         # Script analysis endpoint tests
├── test_generation.py       # Image generation endpoint tests  
├── test_health.py          # Health and status endpoint tests
├── test_utils_unit.py      # Unit tests for utility functions
├── requirements-test.txt   # Testing dependencies
├── run_tests.py           # Test runner script
└── pytest.ini            # Pytest configuration
```

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Run All Tests

```bash
python run_tests.py --all
```

### 3. Run with Coverage

```bash
python run_tests.py --all --coverage
```

## 🔧 Test Runner Commands

The `run_tests.py` script provides convenient commands for different testing scenarios:

### Basic Commands

```bash
# Run all tests
python run_tests.py --all

# Run unit tests only  
python run_tests.py --unit

# Run integration tests only
python run_tests.py --integration

# Run specific tests by pattern
python run_tests.py --specific "test_health"
```

### Advanced Options

```bash
# Run with verbose output
python run_tests.py --all -v

# Run with coverage report
python run_tests.py --all --coverage

# Run tests in parallel (faster)
python run_tests.py --all --parallel

# Generate detailed HTML report
python run_tests.py --report
```

### Maintenance Commands

```bash
# Install/update test dependencies
python run_tests.py --install

# Run code linting
python run_tests.py --lint

# Clean test artifacts
python run_tests.py --clean
```

## 📊 Test Categories

### Unit Tests (`test_utils_unit.py`)
Tests individual utility functions in isolation:
- Script analysis logic
- Prompt generation (with mocked APIs)
- Image generation functions
- Storage utilities
- Data validation

### Integration Tests
Test API endpoints with realistic scenarios:
- **`test_analysis.py`**: Script analysis endpoints
- **`test_generation.py`**: Image generation workflows
- **`test_health.py`**: Health checks and system status

### Health & Monitoring (`test_health.py`)
- API availability tests
- Health endpoint validation
- Performance monitoring
- Resource usage checks

## 🎯 Running Specific Test Types

### By Category
```bash
# Run only script analysis tests
pytest tests/test_analysis.py

# Run only generation tests  
pytest tests/test_generation.py

# Run only health tests
pytest tests/test_health.py
```

### By Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only fast tests (exclude slow ones)
pytest -m "not slow"
```

### By Pattern
```bash
# Test specific functionality
pytest -k "test_analyze_script"
pytest -k "generation"
pytest -k "health"
```

## 🔍 Understanding Test Output

### Successful Test Run
```
========================== test session starts ===========================
collected 45 items

tests/test_analysis.py ................              [ 35%]
tests/test_generation.py ..................          [ 75%]
tests/test_health.py ........                       [ 93%]
tests/test_utils_unit.py ...                         [100%]

========================== 45 passed in 12.34s ============================
```

### Test with Coverage Report
```
========================== test session starts ===========================
collected 45 items

tests/test_analysis.py ................              [ 35%]
tests/test_generation.py ..................          [ 75%]
tests/test_health.py ........                       [ 93%]
tests/test_utils_unit.py ...                         [100%]

----------- coverage: platform linux, python 3.9.7-final-0 -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend/__init__.py                         5      0   100%
backend/config.py                          20      2    90%   45-46
backend/main.py                            85      8    91%   23, 45-52
backend/models/__init__.py                  0      0   100%
backend/models/schemas.py                  35      0   100%
backend/models/session_manager.py          25      1    96%   48
backend/utils/__init__.py                   8      0   100%
backend/utils/script_analysis.py           28      2    93%   52-53
backend/utils/prompt_generation.py         65      5    92%   78-82
backend/utils/image_generation.py          95      8    92%   145-152
backend/utils/storage.py                   58      4    93%   89-92
---------------------------------------------------------------------
TOTAL                                     424     30    93%

========================== 45 passed in 15.67s ============================
```

### Failed Test Example
```
========================== FAILURES ===========================
_______ TestScriptAnalysis.test_analyze_script_basic _______

self = <tests.test_utils_unit.TestScriptAnalysis object at 0x...>

    def test_analyze_script_basic(self):
        script = "The quick brown fox jumps over the lazy dog."
        analysis = analyze_script(script)
        
>       assert analysis.word_count == 9
E       assert 10 == 9
E        +  where 10 = ScriptAnalysis(word_count=10, ...).word_count

tests/test_utils_unit.py:123: AssertionError
========================== short test summary info ============================
FAILED tests/test_utils_unit.py::TestScriptAnalysis::test_analyze_script_basic - assert 10 == 9
========================== 1 failed, 44 passed in 11.23s ============================
```

## 🛠️ Test Configuration

### Environment Variables
Tests automatically set up the following environment variables:
```bash
OPENROUTER_API_KEY=test_openrouter_key
RUNWARE_API_KEY=test_runware_key
TOGETHER_API_KEY=test_together_key
HTTP_TIMEOUT=30
MAX_RETRIES=2
RETRY_DELAY=1
```

### Pytest Markers
Use markers to categorize and run specific test types:

```python
@pytest.mark.unit
def test_analyze_script():
    """Unit test for script analysis"""
    pass

@pytest.mark.integration  
def test_api_endpoint():
    """Integration test for API endpoint"""
    pass

@pytest.mark.slow
def test_long_running_process():
    """Test that takes significant time"""
    pass
```

## 🔧 Fixtures and Mocking

### Key Fixtures Available

#### `client`
FastAPI test client for making HTTP requests:
```python
def test_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
```

#### `temp_projects_dir`
Temporary directory for project storage:
```python
def test_project_creation(temp_projects_dir):
    project_path = temp_projects_dir / "test_project"
    # ... test project operations
```

#### `sample_script`, `sample_analysis`, `sample_scene_prompts`
Pre-built test data for consistent testing:
```python
def test_with_sample_data(sample_script, sample_analysis):
    # Use consistent test data across tests
    pass
```

#### `mock_openrouter_success`, `mock_image_generation_success`
Mocked API responses for external services:
```python
def test_with_mocked_apis(mock_openrouter_success):
    # Test with mocked external API calls
    pass
```

### Common Mock Patterns

#### Mock External API Calls
```python
@patch("requests.post")
def test_api_call(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_post.return_value = mock_response
    
    # Your test code here
```

#### Mock File Operations
```python
@patch("pathlib.Path.write_text")
def test_file_write(mock_write):
    # Test file operations without actual file I/O
    pass
```

## 📈 Coverage Goals

### Current Coverage Targets
- **Overall**: 90%+ coverage
- **Critical paths**: 95%+ coverage
- **Utility functions**: 95%+ coverage
- **API endpoints**: 85%+ coverage

### Viewing Coverage Reports

#### Terminal Report
```bash
python run_tests.py --all --coverage
```

#### HTML Report
```bash
python run_tests.py --all --coverage
# Open htmlcov/index.html in your browser
```

#### JSON Report for CI/CD
```bash
python run_tests.py --report
# Creates reports/coverage.json
```

## 🚨 Troubleshooting Common Issues

### Test Discovery Issues
```bash
# If tests aren't discovered, check:
export PYTHONPATH=$PWD
python -m pytest tests/
```

### Import Errors
```bash
# Ensure backend package is in Python path
pip install -e .
# OR
export PYTHONPATH=$PWD
```

### Fixture Conflicts
```bash
# Clear pytest cache if fixtures behave unexpectedly
python run_tests.py --clean
pytest --cache-clear tests/
```

### Slow Tests
```bash
# Skip slow tests for quick feedback
pytest -m "not slow" tests/

# Run only fast tests
python run_tests.py --specific "not slow"
```

### API Mock Issues
```bash
# If external API mocks aren't working, verify:
# 1. Mock is properly patched
# 2. Return values match expected format
# 3. Mock is called with expected parameters
pytest tests/test_generation.py::test_with_mocked_apis -v -s
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: python run_tests.py --all --coverage --parallel
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: run tests
        entry: python run_tests.py --unit
        language: system
        pass_filenames: false
```

## 📝 Writing New Tests

### Test Structure Template
```python
import pytest
from backend.your_module import your_function

class TestYourModule:
    """Test suite for your module."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = your_function("input")
        assert result == "expected_output"
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        with pytest.raises(ValueError):
            your_function(None)
    
    @pytest.mark.slow
    def test_performance(self):
        """Test performance-critical functionality."""
        # Performance test code
        pass
```

### API Endpoint Test Template
```python
def test_endpoint_success(client, temp_projects_dir):
    """Test successful API endpoint call."""
    payload = {"key": "value"}
    response = client.post("/endpoint", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data

def test_endpoint_validation(client):
    """Test endpoint input validation."""
    response = client.post("/endpoint", json={})
    assert response.status_code == 422  # Validation error
```

## 🎯 Best Practices

### Test Organization
- **One test class per module/feature**
- **Descriptive test names** that explain what is being tested
- **Group related tests** using classes
- **Use fixtures** for common setup/teardown

### Test Writing Guidelines
- **Test one thing at a time**
- **Use descriptive assertions** with custom messages when helpful
- **Mock external dependencies** (APIs, file system, databases)
- **Test both success and failure paths**
- **Include edge cases and boundary conditions**

### Performance Considerations
- **Use `pytest-xdist`** for parallel test execution
- **Mark slow tests** with `@pytest.mark.slow`
- **Mock expensive operations** (network calls, file I/O)
- **Clean up resources** properly in fixtures

### Debugging Tests
```python
# Add debug output
def test_with_debug(caplog):
    with caplog.at_level(logging.DEBUG):
        your_function()
    assert "expected log message" in caplog.text

# Use pytest.set_trace() for debugging
def test_debug():
    result = your_function()
    pytest.set_trace()  # Debugger breakpoint
    assert result == expected
```

## 📊 Test Metrics and Reporting

### Generate Comprehensive Reports
```bash
# Generate all reports
python run_tests.py --report

# This creates:
# - reports/test_report.html      (HTML test report)
# - reports/test_report.json     (JSON test report)  
# - reports/coverage/index.html  (Coverage report)
# - reports/coverage.json        (Coverage JSON)
```

### Key Metrics to Monitor
- **Test execution time**
- **Code coverage percentage**
- **Number of tests per module**
- **Test success/failure rates**
- **Performance regression detection**

---

## 🆘 Getting Help

### Common Commands Quick Reference
```bash
# Quick test run
python run_tests.py --unit

# Full test suite with coverage
python run_tests.py --all --coverage

# Debug failing test
pytest tests/test_file.py::test_name -v -s

# Test specific pattern
python run_tests.py --specific "health"

# Clean and reinstall
python run_tests.py --clean --install
```

### When Tests Fail
1. **Read the error message carefully**
2. **Run the specific failing test** with `-v -s` flags
3. **Check if mocks are properly configured**
4. **Verify test environment setup**
5. **Look for changed dependencies or configuration**

For more detailed debugging, enable debug logging or use `pytest.set_trace()` in your test code.

---

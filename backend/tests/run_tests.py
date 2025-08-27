#!/usr/bin/env python3
"""
Test runner script for Story to Image Generator API
Provides convenient commands for running different types of tests
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def get_python_executable():
    """Get the correct Python executable path."""
    return sys.executable


def run_command(cmd, description=""):
    """Run a command and return the result."""
    if description:
        print(f"\n🔄 {description}")
        print("=" * 60)
    
    # Replace 'python' with the actual Python executable path
    if cmd[0] == 'python':
        cmd[0] = get_python_executable()
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description or 'Command'} completed successfully")
        return True


def check_pytest_installation():
    """Check if pytest is installed."""
    try:
        import pytest
        return True
    except ImportError:
        print("❌ pytest is not installed!")
        print("Please install test dependencies first:")
        print("  python backend/tests/run_tests.py --install")
        print("  OR")
        print("  pip install pytest pytest-cov pytest-html pytest-json-report")
        return False


def setup_test_environment():
    """Setup test environment variables."""
    test_env = {
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "RUNWARE_API_KEY": "test_runware_key", 
        "TOGETHER_API_KEY": "test_together_key",
        "HTTP_TIMEOUT": "30",
        "MAX_RETRIES": "2",
        "RETRY_DELAY": "1",
        "PYTHONPATH": str(Path.cwd())
    }
    
    for key, value in test_env.items():
        os.environ.setdefault(key, value)
    
    print("🔧 Test environment configured")
    print(f"🐍 Using Python: {get_python_executable()}")
    
    # Verify pytest is available
    try:
        result = subprocess.run([get_python_executable(), "-c", "import pytest; print(f'pytest {pytest.__version__}')"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"⚠️  pytest check failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"⚠️  Could not verify pytest: {e}")


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = [get_python_executable(), "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
    
    cmd.extend([
        "backend/tests/test_analysis.py",
        "backend/tests/test_generation.py", 
        "backend/tests/test_health.py",
        "backend/tests/test_utils_unit.py"
    ])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = [get_python_executable(), "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "backend/tests/test_analysis.py::TestScriptAnalysisEndpoint",
        "backend/tests/test_generation.py::TestImageGenerationEndpoint",
        "backend/tests/test_health.py::TestHealthEndpoints"
    ])
    
    return run_command(cmd, "Running integration tests")


def run_all_tests(verbose=False, coverage=False, parallel=False):
    """Run all tests."""
    cmd = [get_python_executable(), "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json"
        ])
    
    if parallel:
        cmd.extend(["-n", "auto"])  # Use pytest-xdist for parallel execution
    
    cmd.append("backend/tests/")
    
    return run_command(cmd, "Running all tests")


def run_specific_test(test_pattern, verbose=False):
    """Run specific test by pattern."""
    cmd = [get_python_executable(), "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["-k", test_pattern])
    cmd.append("backend/tests/")
    
    return run_command(cmd, f"Running tests matching pattern: {test_pattern}")


def run_linting():
    """Run code linting and formatting checks."""
    commands = [
        (["black", "--check", "backend/", "backend/tests/"], "Black formatting check"),
        (["isort", "--check-only", "backend/", "backend/tests/"], "Import sorting check"),
        (["flake8", "backend/", "backend/tests/"], "Flake8 linting"),
    ]
    
    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    return all_passed


def install_test_dependencies():
    """Install test dependencies."""
    cmd = ["pip", "install", "-r", "backend/tests/requirements-test.txt"]
    return run_command(cmd, "Installing test dependencies")


def generate_test_report():
    """Generate detailed test report."""
    cmd = [
        get_python_executable(), "-m", "pytest",
        "--html=reports/test_report.html",
        "--json-report", "--json-report-file=reports/test_report.json",
        "--cov=backend",
        "--cov-report=html:reports/coverage",
        "--cov-report=json:reports/coverage.json",
        "-v",
        "backend/tests/"
    ]
    
    # Create reports directory
    Path("reports").mkdir(exist_ok=True)
    
    return run_command(cmd, "Generating detailed test report")


def clean_test_artifacts():
    """Clean test artifacts and cache."""
    import shutil
    
    artifacts = [
        ".pytest_cache",
        "__pycache__",
        ".coverage",
        "htmlcov",
        "reports",
        "coverage.json"
    ]
    
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"🗑️  Removed directory: {artifact}")
            else:
                path.unlink()
                print(f"🗑️  Removed file: {artifact}")
    
    # Also clean __pycache__ directories recursively
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"🗑️  Removed: {pycache}")
    
    print("✅ Test artifacts cleaned")


def check_test_structure():
    """Check if test structure exists and is valid."""
    required_files = [
        "backend/tests/conftest.py",
        "backend/tests/test_analysis.py",
        "backend/tests/test_generation.py",
        "backend/tests/test_health.py",
        "backend/tests/test_utils_unit.py",
        "backend/tests/requirements-test.txt",
        "backend/tests/pytest.ini"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️  Missing test files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure your test structure is set up correctly.")
        return False
    
    print("✅ Test structure is valid")
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for Story to Image Generator API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/tests/run_tests.py --all                    # Run all tests
  python backend/tests/run_tests.py --unit --coverage        # Run unit tests with coverage
  python backend/tests/run_tests.py --integration -v         # Run integration tests verbosely  
  python backend/tests/run_tests.py --specific "test_health" # Run specific tests
  python backend/tests/run_tests.py --lint                   # Run code linting
  python backend/tests/run_tests.py --report                 # Generate detailed report
  python backend/tests/run_tests.py --install                # Install test dependencies
  python backend/tests/run_tests.py --clean                  # Clean test artifacts
  python backend/tests/run_tests.py --check                  # Check test structure
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--specific", metavar="PATTERN", help="Run specific tests by pattern")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--report", action="store_true", help="Generate detailed test report")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--check", action="store_true", help="Check test structure")
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    args = parser.parse_args()
    
    # If no specific action is specified, show help
    if not any([args.all, args.unit, args.integration, args.specific, 
                args.lint, args.install, args.report, args.clean, args.check]):
        parser.print_help()
        return 1
    
    setup_test_environment()
    success = True
    
    try:
        if args.check:
            success &= check_test_structure()
        
        if args.clean:
            clean_test_artifacts()
        
        if args.install:
            success &= install_test_dependencies()
        
        # Check for pytest before running any tests
        if args.unit or args.integration or args.all or args.specific or args.report:
            if not check_pytest_installation():
                return 1
        
        if args.lint:
            success &= run_linting()
        
        if args.unit:
            success &= run_unit_tests(args.verbose, args.coverage)
        
        if args.integration:
            success &= run_integration_tests(args.verbose)
        
        if args.all:
            success &= run_all_tests(args.verbose, args.coverage, args.parallel)
        
        if args.specific:
            success &= run_specific_test(args.specific, args.verbose)
        
        if args.report:
            success &= generate_test_report()
    
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1
    
    if success:
        print("\n🎉 All operations completed successfully!")
        return 0
    else:
        print("\n💥 Some operations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
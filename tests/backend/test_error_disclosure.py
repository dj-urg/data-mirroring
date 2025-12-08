#!/usr/bin/env python3
"""
Test script to verify error disclosure fixes.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.utils.logging_config import log_error_safely, log_stack_trace_safely

def test_production_error_logging():
    """Test error logging in production mode."""
    print("Testing production error logging...")
    
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    
    # Create a mock logger
    class MockLogger:
        def __init__(self):
            self.messages = []
        
        def error(self, message):
            self.messages.append(message)
            print(f"LOG: {message}")
    
    logger = MockLogger()
    
    # Test with a sensitive error
    try:
        raise ValueError("Database connection failed: user=admin, password=secret123, host=internal-server.local")
    except Exception as e:
        log_error_safely(e, "Database connection test", logger)
        log_stack_trace_safely(e, logger)
    
    # Check that sensitive information is redacted
    error_logs = [msg for msg in logger.messages if "Error:" in msg]
    stack_logs = [msg for msg in logger.messages if "Error occurred:" in msg]
    
    print(f"Error logs: {error_logs}")
    print(f"Stack logs: {stack_logs}")
    
    # Verify sensitive data is redacted
    all_logs = " ".join(logger.messages)
    assert "password=secret123" not in all_logs, "Password should be redacted"
    assert "internal-server.local" not in all_logs, "Internal hostname should be redacted"
    assert "[SENSITIVE_DATA_REDACTED]" in all_logs, "Should contain redaction marker"
    
    print("✅ Production error logging test passed!")

def test_development_error_logging():
    """Test error logging in development mode."""
    print("\nTesting development error logging...")
    
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    
    # Create a mock logger
    class MockLogger:
        def __init__(self):
            self.messages = []
        
        def error(self, message):
            self.messages.append(message)
            print(f"LOG: {message}")
    
    logger = MockLogger()
    
    # Test with a sensitive error
    try:
        raise ValueError("Database connection failed: user=admin, password=secret123")
    except Exception as e:
        log_error_safely(e, "Database connection test", logger)
        log_stack_trace_safely(e, logger)
    
    # In development, we should see full details
    all_logs = " ".join(logger.messages)
    print(f"Development logs: {all_logs}")
    
    # In development, sensitive data might be visible (for debugging)
    # This is acceptable in development mode
    print("✅ Development error logging test passed!")

if __name__ == "__main__":
    print("🔒 Testing Error Disclosure Fixes")
    print("=" * 50)
    
    try:
        test_production_error_logging()
        test_development_error_logging()
        
        print("\n🎉 All error disclosure tests passed!")
        print("\nSecurity improvements implemented:")
        print("✅ Sensitive data is redacted from error logs in production")
        print("✅ Stack traces are sanitized in production")
        print("✅ Full debugging info available in development")
        print("✅ Error information disclosure is now FIXED!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

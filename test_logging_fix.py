"""
Test script to verify that exc_info and stack_info are properly cleared
before formatting in the ColorFormatter.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.logging.setup_logging import ColorFormatter


def test_exc_info_cleared():
    """Test that exc_info is cleared before formatting."""
    print("=" * 60)
    print("Test 1: Verify exc_info is cleared before formatting")
    print("=" * 60)
    
    # Create a test formatter with simple config
    component_config = {"prefix": "TEST", "color": "blue"}
    level_colors = {"ERROR": "red"}
    formatter = ColorFormatter(
        "[%(component)s] | %(levelname)s | %(message)s",
        component_config,
        level_colors,
        use_colors=False  # Disable colors for easier output inspection
    )
    
    # Create a log record with exc_info and stack_info
    try:
        1 / 0
    except ZeroDivisionError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Division failed!",
            args=(),
            exc_info=sys.exc_info(),
            stack_info=True
        )
        
        print("\nBefore formatting:")
        print(f"  exc_info is None: {record.exc_info is None}")
        print(f"  stack_info is None: {record.stack_info is None}")
        
        # Format the record
        formatted = formatter.format(record)
        
        print("\nAfter formatting:")
        print(f"  exc_info is None: {record.exc_info is None}")
        print(f"  stack_info is None: {record.stack_info is None}")
        
        print(f"\nFormatted output:\n{formatted}")
        
        # Check that the output only contains the message, not the traceback
        if "Traceback" not in formatted and "ZeroDivisionError" not in formatted:
            print("\n✓ SUCCESS: Traceback is NOT in the formatted output")
        else:
            print("\n✗ FAILURE: Traceback found in the formatted output")
            return False
    
    return True


def test_with_logger():
    """Test using a real logger with the ColorFormatter."""
    print("\n" + "=" * 60)
    print("Test 2: Test with actual logger")
    print("=" * 60)
    
    # Create a logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # Create a stream handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create our custom formatter
    component_config = {"prefix": "APP", "color": "green"}
    level_colors = {"ERROR": "red", "DEBUG": "cyan"}
    formatter = ColorFormatter(
        "[%(component)s] | %(levelname)s | %(message)s",
        component_config,
        level_colors,
        use_colors=False
    )
    handler.setFormatter(formatter)
    
    # Clear existing handlers and add our handler
    logger.handlers = []
    logger.addHandler(handler)
    
    # Log a normal message
    print("\nLogging normal message:")
    logger.info("This is a normal info message")
    
    # Log with exception info
    print("\nLogging error with exc_info=True:")
    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.error("Division by zero occurred!", exc_info=True)
    
    print("\n✓ If no traceback appears above, the fix is working!")
    
    return True


if __name__ == "__main__":
    print("\nTesting the ColorFormatter fix...\n")
    
    test1_passed = test_exc_info_cleared()
    test2_passed = test_with_logger()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60 + "\n")

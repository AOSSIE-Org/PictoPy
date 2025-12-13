"""
Verification script for Memories feature setup.
Checks all dependencies, database schema, file structure, and API routes.

Usage:
    python -m app.utils.verify_memories_setup
"""

import sys
import os
import sqlite3
import importlib
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    """Print info message"""
    print(f"  {text}")

def check_dependencies():
    """Check if all required packages are installed"""
    print_header("1. Checking Python Dependencies")
    
    required_packages = {
        'numpy': '1.26.4',
        'sklearn': '1.5.1',  # scikit-learn imports as sklearn
        'fastapi': '0.111.0',
        'sqlalchemy': None,
        'pydantic': None,
    }
    
    all_installed = True
    
    for package, expected_version in required_packages.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            
            if expected_version and version != expected_version:
                print_warning(f"{package} installed (v{version}), expected v{expected_version}")
            else:
                print_success(f"{package} v{version}")
        except ImportError:
            print_error(f"{package} is NOT installed")
            all_installed = False
    
    return all_installed

def check_file_structure():
    """Check if all required files exist"""
    print_header("2. Checking File Structure")
    
    backend_path = Path(__file__).parent.parent.parent
    
    required_files = [
        'app/utils/extract_location_metadata.py',
        'app/utils/memory_clustering.py',
        'app/routes/memories.py',
        'app/database/images.py',
        'main.py',
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = backend_path / file_path
        if full_path.exists():
            print_success(f"{file_path}")
            print_info(f"   → {full_path}")
        else:
            print_error(f"{file_path} NOT FOUND")
            all_exist = False
    
    return all_exist

def check_database_schema():
    """Check if database has required columns and indexes"""
    print_header("3. Checking Database Schema")
    
    backend_path = Path(__file__).parent.parent.parent
    db_path = backend_path / 'app' / 'database' / 'PictoPy.db'
    
    if not db_path.exists():
        print_warning("Database file 'gallery.db' not found")
        print_info("   → Database will be created on first run")
        return None  # Not an error, just not initialized yet
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if images table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
        if not cursor.fetchone():
            print_error("Table 'images' does not exist")
            conn.close()
            return False
        
        print_success("Table 'images' exists")
        
        # Check for required columns
        cursor.execute("PRAGMA table_info(images)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_columns = {
            'latitude': 'FLOAT',
            'longitude': 'FLOAT',
            'captured_at': 'DATETIME',
        }
        
        all_columns_exist = True
        for col_name, col_type in required_columns.items():
            if col_name in columns:
                print_success(f"Column '{col_name}' ({columns[col_name]})")
            else:
                print_error(f"Column '{col_name}' NOT FOUND")
                print_info("   → Run migration: python migrate_add_memories_columns.py")
                print_info("   → Or restart the app (auto-migration enabled)")
                all_columns_exist = False
        
        # Check for indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        required_indexes = [
            'ix_images_latitude',
            'ix_images_longitude',
            'ix_images_captured_at',
        ]
        
        print()
        for index_name in required_indexes:
            if index_name in indexes:
                print_success(f"Index '{index_name}'")
            else:
                print_warning(f"Index '{index_name}' not found (recommended for performance)")
        
        conn.close()
        return all_columns_exist
        
    except Exception as e:
        print_error(f"Database check failed: {e}")
        return False

def check_imports():
    """Check if all modules can be imported"""
    print_header("4. Checking Module Imports")
    
    modules_to_check = [
        'app.utils.extract_location_metadata',
        'app.utils.memory_clustering',
        'app.routes.memories',
        'app.database.images',
    ]
    
    all_imported = True
    
    for module_name in modules_to_check:
        try:
            importlib.import_module(module_name)
            print_success(f"{module_name}")
        except Exception as e:
            print_error(f"{module_name} - {str(e)}")
            all_imported = False
    
    return all_imported

def check_api_routes():
    """Check if Memories API routes are registered"""
    print_header("5. Checking API Routes")
    
    try:
        # Import main app
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from main import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        required_routes = [
            '/api/memories/generate',
            '/api/memories/timeline',
            '/api/memories/on-this-day',
            '/api/memories/locations',
        ]
        
        all_routes_exist = True
        for route_path in required_routes:
            if route_path in routes:
                print_success(f"{route_path}")
            else:
                print_error(f"{route_path} NOT FOUND")
                print_info("   → Check if memories router is included in main.py")
                all_routes_exist = False
        
        return all_routes_exist
        
    except Exception as e:
        print_error(f"Failed to check routes: {e}")
        return False

def print_summary(results):
    """Print final summary"""
    print_header("Verification Summary")
    
    all_passed = all(result is not False for result in results.values())
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else ("⚠ WARNING" if result is None else "✗ FAIL")
        color = Colors.GREEN if result else (Colors.YELLOW if result is None else Colors.RED)
        print(f"{color}{status}{Colors.RESET} - {check_name}")
    
    print()
    if all_passed:
        print(f"{Colors.BOLD}{Colors.GREEN}🎉 All checks passed! Memories feature is ready to use.{Colors.RESET}")
        print_info("Next steps:")
        print_info("1. Start the backend: cd backend && ./run.sh")
        print_info("2. Run metadata extraction: python -m app.utils.extract_location_metadata")
        print_info("3. Test API endpoints: see MEMORIES_TESTING_GUIDE.md")
    else:
        print(f"{Colors.BOLD}{Colors.RED}❌ Some checks failed. Please fix the issues above.{Colors.RESET}")
        print_info("See MEMORIES_README.md for setup instructions")
    
    print()

def main():
    """Run all verification checks"""
    print(f"\n{Colors.BOLD}PictoPy Memories Feature Verification{Colors.RESET}")
    print(f"{Colors.BOLD}====================================={Colors.RESET}")
    
    results = {
        'Dependencies': check_dependencies(),
        'File Structure': check_file_structure(),
        'Database Schema': check_database_schema(),
        'Module Imports': check_imports(),
        'API Routes': check_api_routes(),
    }
    
    print_summary(results)

if __name__ == '__main__':
    main()

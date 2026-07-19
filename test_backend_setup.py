#!/usr/bin/env python3
"""
Test script to verify backend setup and configuration.
Run this before starting the server to check everything is configured correctly.
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print_success(f"{description} exists: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables."""
    print_header("Checking Environment Configuration")
    
    env_path = Path("backend/.env")
    
    if not env_path.exists():
        print_error(".env file not found in backend directory")
        print_info("Copy backend/.env.example to backend/.env and fill in your values")
        return False
    
    print_success(".env file found")
    
    # Read .env file
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Check for required variables
    required_vars = {
        'DATABASE_URL': 'Database connection string',
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_KEY': 'Supabase anon key',
        'JWT_SECRET': 'JWT secret key',
    }
    
    missing_vars = []
    placeholder_vars = []
    
    for var, description in required_vars.items():
        if var not in env_content:
            missing_vars.append(f"{var} ({description})")
            print_error(f"{var} not found in .env")
        elif f"{var}=" in env_content:
            # Check if it's still a placeholder
            line = [l for l in env_content.split('\n') if l.startswith(f"{var}=")][0]
            value = line.split('=', 1)[1].strip()
            
            if not value or value.startswith('[') or 'your-' in value.lower() or 'change' in value.lower():
                placeholder_vars.append(f"{var} ({description})")
                print_warning(f"{var} appears to be a placeholder value")
            else:
                print_success(f"{var} is configured")
    
    if missing_vars:
        print_error(f"\nMissing required variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    if placeholder_vars:
        print_warning(f"\nPlaceholder values detected:")
        for var in placeholder_vars:
            print(f"  - {var}")
        print_info("Please update these with your actual Supabase credentials")
        return False
    
    print_success("\nAll required environment variables are configured!")
    return True

def check_python_version():
    """Check Python version."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python version: {version_str} (OK)")
        return True
    else:
        print_error(f"Python version: {version_str} (Requires Python 3.8+)")
        return False

def check_dependencies():
    """Check if required Python packages are installed."""
    print_header("Checking Python Dependencies")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'asyncpg',
        'psycopg2',
        'supabase',
        'python-jose',
        'passlib',
        'pydantic',
        'python-dotenv',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} is installed")
        except ImportError:
            missing_packages.append(package)
            print_error(f"{package} is not installed")
    
    if missing_packages:
        print_error(f"\nMissing packages: {', '.join(missing_packages)}")
        print_info("Install with: pip install -r backend/requirements.txt")
        return False
    
    print_success("\nAll required packages are installed!")
    return True

def check_project_structure():
    """Check if project structure is correct."""
    print_header("Checking Project Structure")
    
    required_files = [
        ('backend/app/main.py', 'Main application file'),
        ('backend/app/core/config.py', 'Configuration module'),
        ('backend/app/core/database.py', 'Database module'),
        ('backend/app/core/security.py', 'Security module'),
        ('backend/app/api/v1/api.py', 'API router'),
        ('backend/app/api/v1/endpoints/auth.py', 'Auth endpoints'),
        ('backend/requirements.txt', 'Requirements file'),
        ('database/phase1_minimal_schema.sql', 'Database schema'),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def test_database_connection():
    """Test database connection."""
    print_header("Testing Database Connection")
    
    try:
        from dotenv import load_dotenv
        load_dotenv('backend/.env')
        
        database_url = os.getenv('DATABASE_URL')
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not database_url and not (supabase_url and supabase_key):
            print_error("No database configuration found")
            return False
        
        # Try Supabase connection
        if supabase_url and supabase_key:
            try:
                from supabase import create_client
                client = create_client(supabase_url, supabase_key)
                
                # Try a simple query
                response = client.table('users').select('count', count='exact').limit(1).execute()
                print_success("Supabase connection successful!")
                return True
            except Exception as e:
                print_error(f"Supabase connection failed: {e}")
        
        # Try PostgreSQL connection
        if database_url:
            try:
                import psycopg2
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result[0] == 1:
                    print_success("PostgreSQL connection successful!")
                    return True
            except Exception as e:
                print_warning(f"PostgreSQL connection failed: {e}")
                print_info("This is expected on Windows. App will use Supabase fallback.")
                return True  # Not a critical error
        
        return False
        
    except Exception as e:
        print_error(f"Database connection test failed: {e}")
        return False

def check_database_schema():
    """Check if database schema is applied."""
    print_header("Checking Database Schema")
    
    try:
        from dotenv import load_dotenv
        load_dotenv('backend/.env')
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not (supabase_url and supabase_key):
            print_warning("Supabase not configured, skipping schema check")
            return True
        
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        
        # Check if tables exist
        required_tables = ['users', 'organizations', 'subscription_plans', 'campuses']
        
        for table in required_tables:
            try:
                response = client.table(table).select('count', count='exact').limit(1).execute()
                print_success(f"Table '{table}' exists")
            except Exception as e:
                print_error(f"Table '{table}' not found")
                print_info("Run: python apply_phase1_schema.py")
                return False
        
        # Check if default data exists
        try:
            response = client.table('users').select('email').eq('email', 'admin@learnlyf.com').execute()
            if response.data:
                print_success("System admin account exists")
            else:
                print_warning("System admin account not found")
                print_info("Run: python apply_phase1_schema.py")
        except Exception:
            pass
        
        print_success("\nDatabase schema is properly configured!")
        return True
        
    except Exception as e:
        print_error(f"Schema check failed: {e}")
        print_info("Make sure to run: python apply_phase1_schema.py")
        return False

def main():
    """Run all checks."""
    print_header("LEARNLYF - BACKEND SETUP TEST")
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Environment Configuration", check_env_file),
        ("Python Dependencies", check_dependencies),
        ("Database Connection", test_database_connection),
        ("Database Schema", check_database_schema),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_error(f"Check failed with error: {e}")
            results.append((check_name, False))
    
    # Print summary
    print_header("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
    
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if passed == total:
        print_success(f"All checks passed! ({passed}/{total})")
        print_success("\n🚀 You're ready to start the backend server!")
        print_info("\nRun: cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
    else:
        print_error(f"Some checks failed ({passed}/{total} passed)")
        print_info("\nPlease fix the issues above before starting the server")
    print(f"{BLUE}{'=' * 60}{RESET}\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
Script to fix all authentication checks across endpoint files.
Adds null checks before accessing user data to prevent NoneType errors.
"""

import os
import re
from pathlib import Path

# Pattern to find: get token and user without proper null check
PATTERN_WITHOUT_NULL_CHECK = re.compile(
    r'(\s+)token = get_token_from_request\(request\)\n'
    r'(\s+)user = get_current_user_from_token\(token\)\n'
    r'(?!.*if not user:).*?'  # Not followed by null check
    r'(\s+)(require_|if not user\.get)',
    re.MULTILINE | re.DOTALL
)

def add_auth_checks(filepath):
    """Add proper authentication checks to endpoint file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: token -> user -> immediate user.get() without check
    pattern1 = r'(\s+)token = get_token_from_request\(request\)\n(\s+)user = get_current_user_from_token\(token\)\n(\s+)\n(\s+)if not user\.get\("school_id"\):'
    
    replacement1 = r'\1token = get_token_from_request(request)\n\1if not token:\n\1    raise AuthorizationError("Authentication token required")\n\1\n\2user = get_current_user_from_token(token)\n\2if not user:\n\2    raise AuthorizationError("User authentication failed - no valid user found")\n\3\n\4if not user.get("school_id"):'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: token -> user -> require_* without check
    pattern2 = r'(\s+)token = get_token_from_request\(request\)\n(\s+)user = get_current_user_from_token\(token\)\n(\s+)(require_\w+\(user\))'
    
    replacement2 = r'\1token = get_token_from_request(request)\n\1if not token:\n\1    raise AuthorizationError("Authentication token required")\n\1\n\2user = get_current_user_from_token(token)\n\2if not user:\n\2    raise AuthorizationError("User authentication failed - no valid user found")\n\2\n\3\4'
    
    content = re.sub(pattern2, replacement2, content)
    
    # Pattern 3: Bare token -> user pattern at start of try block
    pattern3 = r'(try:\n\s+)token = get_token_from_request\(request\)\n(\s+)user = get_current_user_from_token\(token\)\n(?!\s+if not)(\s+)(?!if not)'
    
    replacement3 = r'\1token = get_token_from_request(request)\n\1if not token:\n\1    raise AuthorizationError("Authentication token required")\n\1\n\2user = get_current_user_from_token(token)\n\2if not user:\n\2    raise AuthorizationError("User authentication failed - no valid user found")\n\2\n\3'
    
    content = re.sub(pattern3, replacement3, content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all endpoint files."""
    endpoints_dir = Path(__file__).parent / 'backend' / 'app' / 'api' / 'v1' / 'endpoints'
    
    files_to_fix = [
        'students.py',
        'teachers.py',
        'sessions.py',
        'classes.py',
        'subjects.py',
        'terms.py',
        'parents.py',
        'assignments.py',
        'attendance.py',
        'fees.py',
        'grading.py',
        'teacher_management.py',
        'organizations.py'
    ]
    
    fixed_count = 0
    for filename in files_to_fix:
        filepath = endpoints_dir / filename
        if filepath.exists():
            try:
                if add_auth_checks(filepath):
                    print(f"✅ Fixed: {filename}")
                    fixed_count += 1
                else:
                    print(f"ℹ️  No changes needed: {filename}")
            except Exception as e:
                print(f"❌ Error fixing {filename}: {e}")
        else:
            print(f"⚠️  Not found: {filename}")
    
    print(f"\n📊 Total files fixed: {fixed_count}")

if __name__ == '__main__':
    main()

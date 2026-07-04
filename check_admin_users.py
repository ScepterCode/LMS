"""Check for existing admin users in the database"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import get_supabase

def check_admin_users():
    try:
        supabase = get_supabase()
        
        print("\n🔍 Checking for admin users...\n")
        
        # Get admin users
        response = supabase.table('users').select('email,role,full_name,is_active').in_(
            'role', ['admin', 'system_admin']
        ).execute()
        
        if response.data:
            print(f"✅ Found {len(response.data)} admin user(s):\n")
            for user in response.data:
                status = "✅ Active" if user.get('is_active') else "❌ Inactive"
                print(f"  Email: {user['email']}")
                print(f"  Name:  {user.get('full_name', 'N/A')}")
                print(f"  Role:  {user['role']}")
                print(f"  Status: {status}")
                print()
            
            print("📝 To log in:")
            print(f"   1. Go to http://localhost:3000/login")
            print(f"   2. Use one of the emails above")
            print(f"   3. Enter your password")
            print()
            
        else:
            print("❌ No admin users found in database!\n")
            print("You need to create an admin user first.")
            print("\nOptions:")
            print("1. Register a school at: http://localhost:3000/register-school")
            print("2. Or run: python create_admin_user.py")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Backend server is running")
        print("2. Database connection is configured")
        print("3. .env file has correct SUPABASE credentials")

if __name__ == "__main__":
    check_admin_users()

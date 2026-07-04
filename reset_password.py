"""Reset password for a specific user"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import get_supabase
from app.core.security import get_password_hash

def reset_password(email, new_password):
    try:
        supabase = get_supabase()
        
        print(f"\n🔐 Resetting password for: {email}")
        
        # Hash the new password
        password_hash = get_password_hash(new_password)
        
        # Update the user's password
        response = supabase.table('users').update({
            'password_hash': password_hash
        }).eq('email', email).execute()
        
        if response.data:
            print(f"✅ Password reset successfully!")
            print(f"\n📝 Login Credentials:")
            print(f"   Email: {email}")
            print(f"   Password: {new_password}")
            print(f"\n🌐 Login at: http://localhost:3000/login")
            print(f"\nAfter logging in:")
            print(f"   → Go to Dashboard → Academic → Sessions")
            print(f"   → Click '+ Add Session'")
            print(f"   → Fill form and submit")
            print(f"   → It will work! ✅")
            return True
        else:
            print(f"❌ User not found: {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Reset password for Sarah
    email = "sarahchidiloveday@gmail.com"
    new_password = "Admin123!"
    
    reset_password(email, new_password)

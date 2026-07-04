#!/usr/bin/env python3
"""
Supabase Connection Diagnostic
Tests various connection methods to identify the issue
"""

import asyncio
import asyncpg
import socket
import sys
from urllib.parse import urlparse

# Read from .env
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("=" * 70)
print("SUPABASE CONNECTION DIAGNOSTIC")
print("=" * 70)
print()

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"📍 Database URL configured: {DATABASE_URL[:50]}...")
print()

# Parse connection string
result = urlparse(DATABASE_URL)
print("📋 Connection Details:")
print(f"   Host: {result.hostname}")
print(f"   Port: {result.port or 5432}")
print(f"   Database: {result.path[1:]}")
print(f"   User: {result.username}")
print()

# Test 1: DNS Resolution
print("🔍 Test 1: DNS Resolution")
try:
    host = result.hostname
    ip = socket.gethostbyname(host)
    print(f"   ✅ Host resolves to: {ip}")
except socket.gaierror as e:
    print(f"   ❌ DNS resolution failed: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 2: TCP Port Connection
print("🔍 Test 2: TCP Port Connection")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result_code = sock.connect_ex((result.hostname, result.port or 5432))
    sock.close()
    
    if result_code == 0:
        print(f"   ✅ Port 5432 is open and accepting connections")
    else:
        print(f"   ❌ Port 5432 connection refused (errno: {result_code})")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 3: asyncpg Direct Connection
print("🔍 Test 3: asyncpg Connection")
async def test_asyncpg():
    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=10)
        version = await conn.fetchval("SELECT version()")
        print(f"   ✅ Connected successfully")
        print(f"   Database: {version[:50]}...")
        await conn.close()
        return True
    except asyncpg.PostgresError as e:
        print(f"   ❌ PostgreSQL error: {e}")
        return False
    except asyncpg.TooManyConnectionsError as e:
        print(f"   ❌ Too many connections: {e}")
        return False
    except (OSError, asyncio.TimeoutError) as e:
        print(f"   ❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return False

try:
    success = asyncio.run(test_asyncpg())
except Exception as e:
    print(f"   ❌ Failed to run test: {e}")
    success = False

print()
print("=" * 70)

if success:
    print("✅ All tests passed! Your database connection is working.")
    print()
    print("Next steps:")
    print("   python run_migrations.py")
else:
    print("❌ Connection tests failed. Possible issues:")
    print()
    print("1. VPN/Proxy Required?")
    print("   - Check if your network requires VPN")
    print("   - Some corporate networks block database connections")
    print()
    print("2. Firewall Issue?")
    print("   - Check Windows Firewall settings")
    print("   - Ensure outbound port 5432 is allowed")
    print()
    print("3. Supabase Status?")
    print("   - Visit https://status.supabase.com")
    print("   - Check if your project is running")
    print()
    print("4. Alternative: Use Supabase SQL Editor")
    print("   - Go to Supabase Dashboard → SQL Editor")
    print("   - Copy contents of database/phase4_complete_schema.sql")
    print("   - Paste and run in the editor")
    print()
    print("5. Check Credentials")
    print("   - Verify DATABASE_URL in backend/.env is correct")
    print("   - Ensure no typos in password")

print()

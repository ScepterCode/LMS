#!/usr/bin/env python3
"""
Comprehensive Database Migration Runner
Applies all schema migrations in the correct order.

This script reads SQL files and executes them against the database.
Supports both direct PostgreSQL connections and Supabase.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncpg
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")

class DatabaseMigrationRunner:
    """Run database migrations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        
    async def connect(self) -> bool:
        """Establish database connection."""
        try:
            if not self.database_url:
                print("❌ DATABASE_URL not configured")
                return False
                
            result = urlparse(self.database_url)
            
            self.pool = await asyncpg.create_pool(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port or 5432,
                min_size=1,
                max_size=5,
                command_timeout=60,
            )
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self.pool:
            await self.pool.close()
            print("✅ Database connection closed")
    
    async def execute_sql_file(self, filepath: str, description: str) -> bool:
        """Execute SQL file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            if not sql_content.strip():
                print(f"⚠️  {description}: File is empty, skipping")
                return True
            
            print(f"📋 Applying: {description}")
            print(f"   File: {filepath}")
            
            async with self.pool.acquire() as connection:
                await connection.execute(sql_content)
            
            print(f"   ✅ Success")
            return True
            
        except FileNotFoundError:
            print(f"   ❌ File not found: {filepath}")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def run_migrations(self) -> bool:
        """Run all migrations in order."""
        if not await self.connect():
            return False
        
        try:
            print()
            print("=" * 70)
            print("DATABASE MIGRATION RUNNER")
            print("=" * 70)
            print()
            
            # Define migrations in order
            migrations = [
                ("database/phase1_minimal_schema.sql", "Phase 1: Minimal Schema (Auth & Org)"),
                ("database/phase2_schema.sql", "Phase 2: Student & Teacher Management"),
                ("database/phase3_grading_schema.sql", "Phase 3A: Grading & Assessment"),
                ("database/phase3_attendance_schema.sql", "Phase 3B: Attendance Management"),
                ("database/phase3_fees_schema.sql", "Phase 3C: Fee Management"),
                ("database/phase4_teacher_class_schema.sql", "Phase 4: Teacher Class Management"),
                ("database/phase4_seed_data.sql", "Phase 4: Seed Default Data"),
            ]
            
            successful = 0
            failed = 0
            skipped = 0
            
            for filepath, description in migrations:
                if not os.path.exists(filepath):
                    print(f"⏭️  Skipping: {description}")
                    print(f"   File not found: {filepath}")
                    skipped += 1
                elif await self.execute_sql_file(filepath, description):
                    successful += 1
                else:
                    failed += 1
                print()
            
            print("=" * 70)
            print("MIGRATION SUMMARY")
            print("=" * 70)
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            print(f"⏭️  Skipped: {skipped}")
            print()
            
            if failed > 0:
                print("⚠️  Some migrations failed. Check the errors above.")
                return False
            else:
                print("🎉 All migrations completed successfully!")
                return True
                
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL environment variable is not set")
        print("   Please configure your .env file with DATABASE_URL")
        sys.exit(1)
    
    runner = DatabaseMigrationRunner(DATABASE_URL)
    success = await runner.run_migrations()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

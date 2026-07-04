#!/usr/bin/env python3
"""
Phase 4 Migration Helper
Run migrations programmatically or from CLI

Usage:
    python migrate_phase4.py --apply       # Apply Phase 4 migrations
    python migrate_phase4.py --verify      # Verify Phase 4 schema
    python migrate_phase4.py --rollback    # Rollback Phase 4 (DESTRUCTIVE)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import asyncio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase4Migrator:
    """Handle Phase 4 migrations"""
    
    def __init__(self, db_url: str = None):
        """Initialize migrator with database connection"""
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.db_path = Path(__file__).parent
        self.migration_files = [
            'phase4_teacher_class_schema.sql',
            'phase4_seed_data.sql'
        ]
    
    async def apply_migrations(self) -> bool:
        """Apply Phase 4 migrations"""
        logger.info("Starting Phase 4 migration...")
        
        try:
            import psycopg
            conn = await psycopg.AsyncConnection.connect(self.db_url)
            
            for migration_file in self.migration_files:
                file_path = self.db_path / migration_file
                
                if not file_path.exists():
                    logger.error(f"Migration file not found: {file_path}")
                    return False
                
                logger.info(f"Applying {migration_file}...")
                
                with open(file_path, 'r') as f:
                    sql = f.read()
                
                try:
                    await conn.execute(sql)
                    logger.info(f"✓ {migration_file} applied successfully")
                except Exception as e:
                    logger.error(f"✗ Error applying {migration_file}: {str(e)}")
                    await conn.close()
                    return False
            
            await conn.close()
            logger.info("✓ Phase 4 migration complete!")
            return True
            
        except ImportError:
            logger.error("psycopg3 not installed. Install with: pip install psycopg[binary]")
            return False
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    async def verify_migration(self) -> bool:
        """Verify Phase 4 schema is correctly applied"""
        logger.info("Verifying Phase 4 schema...")
        
        try:
            import psycopg
            conn = await psycopg.AsyncConnection.connect(self.db_url)
            
            checks = {
                'class_subjects': 'SELECT COUNT(*) FROM class_subjects;',
                'grading_schemes': 'SELECT COUNT(*) FROM grading_schemes;',
                'grading_scheme_components': 'SELECT COUNT(*) FROM grading_scheme_components;',
                'teacher_class_assignments': 'SELECT COUNT(*) FROM teacher_class_assignments;',
                'student_remarks': 'SELECT COUNT(*) FROM student_remarks;',
                'school_reports': 'SELECT COUNT(*) FROM school_reports;',
                'school_report_recipients': 'SELECT COUNT(*) FROM school_report_recipients;',
            }
            
            all_passed = True
            
            for table_name, query in checks.items():
                try:
                    result = await conn.execute(query)
                    count = result[0][0] if result else 0
                    logger.info(f"✓ {table_name}: {count} records")
                except Exception as e:
                    logger.error(f"✗ {table_name}: Table not found or error - {str(e)}")
                    all_passed = False
            
            # Verify indices
            index_query = """
            SELECT COUNT(*) FROM pg_indexes 
            WHERE schemaname = 'public' AND tablename IN (
                'class_subjects', 'grading_schemes', 'grading_scheme_components',
                'teacher_class_assignments', 'student_remarks', 'school_reports', 'school_report_recipients'
            );
            """
            
            try:
                result = await conn.execute(index_query)
                index_count = result[0][0] if result else 0
                if index_count >= 10:  # Should be ~15
                    logger.info(f"✓ Indices: {index_count} created")
                else:
                    logger.warning(f"⚠ Indices: Only {index_count} created (expected ~15)")
            except Exception as e:
                logger.error(f"✗ Index verification failed: {str(e)}")
                all_passed = False
            
            await conn.close()
            
            if all_passed:
                logger.info("✓ Phase 4 schema verification passed!")
            else:
                logger.error("✗ Phase 4 schema verification failed!")
            
            return all_passed
            
        except ImportError:
            logger.error("psycopg3 not installed")
            return False
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False
    
    async def rollback_migrations(self) -> bool:
        """Rollback Phase 4 migrations (DESTRUCTIVE)"""
        logger.warning("⚠ ROLLBACK INITIATED - This will DELETE all Phase 4 data!")
        response = input("Type 'ROLLBACK' to confirm: ")
        
        if response != 'ROLLBACK':
            logger.info("Rollback cancelled")
            return False
        
        try:
            import psycopg
            conn = await psycopg.AsyncConnection.connect(self.db_url)
            
            rollback_file = self.db_path / 'phase4_rollback.sql'
            
            if not rollback_file.exists():
                logger.error(f"Rollback file not found: {rollback_file}")
                return False
            
            with open(rollback_file, 'r') as f:
                sql = f.read()
            
            logger.info("Executing rollback...")
            await conn.execute(sql)
            await conn.close()
            
            logger.info("✓ Phase 4 rollback complete!")
            return True
            
        except ImportError:
            logger.error("psycopg3 not installed")
            return False
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Phase 4 Migration Helper')
    parser.add_argument('--apply', action='store_true', help='Apply Phase 4 migrations')
    parser.add_argument('--verify', action='store_true', help='Verify Phase 4 schema')
    parser.add_argument('--rollback', action='store_true', help='Rollback Phase 4 (DESTRUCTIVE)')
    parser.add_argument('--db-url', help='Database URL (or use DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Default to verify if no action specified
    if not any([args.apply, args.verify, args.rollback]):
        args.verify = True
    
    try:
        migrator = Phase4Migrator(db_url=args.db_url)
        
        if args.apply:
            success = await migrator.apply_migrations()
            sys.exit(0 if success else 1)
        
        elif args.verify:
            success = await migrator.verify_migration()
            sys.exit(0 if success else 1)
        
        elif args.rollback:
            success = await migrator.rollback_migrations()
            sys.exit(0 if success else 1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

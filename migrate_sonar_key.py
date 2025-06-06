#!/usr/bin/env python3
"""
Migration script to add sonar_project_key column to projects table
"""

import os
import sys
sys.path.append('.')

from sqlalchemy import text
from models import db, Project
from main import app

def migrate_database():
    """Add sonar_project_key column to projects table"""
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='projects' AND column_name='sonar_project_key'
            """))
            
            if result.fetchone():
                print("Column sonar_project_key already exists")
                return
            
            # Add the new column
            db.session.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN sonar_project_key VARCHAR(255)
            """))
            
            db.session.commit()
            print("Successfully added sonar_project_key column to projects table")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_database()
#!/usr/bin/env python3
"""
DATABASE INSPECTOR - Quick check of trade database structure
"""

import sqlite3
import pandas as pd

def inspect_database():
    conn = sqlite3.connect('trading_data.db')
    cursor = conn.cursor()
    
    print("🔍 DATABASE STRUCTURE INSPECTION")
    print("=" * 50)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        table = table_name[0]
        print(f"\n📊 Table: {table}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print("   Columns:")
        for col in columns:
            print(f"     • {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   Records: {count}")
        
        # Show sample data for trades table
        if table == 'trades' and count > 0:
            print("   Sample records:")
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            sample_data = cursor.fetchall()
            for i, row in enumerate(sample_data):
                print(f"     Row {i+1}: {row}")
    
    # Check specifically trades table columns
    print(f"\n🔍 DETAILED TRADES TABLE ANALYSIS")
    print("=" * 50)
    
    trades_df = pd.read_sql_query("SELECT * FROM trades LIMIT 5", conn)
    print("Column names in trades table:")
    for col in trades_df.columns:
        print(f"  • {col}")
    
    print(f"\nFirst few records:")
    print(trades_df)
    
    conn.close()

if __name__ == "__main__":
    inspect_database()

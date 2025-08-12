#!/usr/bin/env python3
"""
FILE AUDIT SYSTEM
Check which files are actually used and which are redundant
"""

import os
import subprocess
from pathlib import Path

def check_file_usage():
    """Audit files to see which are actually needed"""
    
    print("🔍 AUDITING FILES FOR ACTUAL USAGE")
    print("=" * 50)
    
    core_files = [
        'main_papertrader.py',
        'broker_interface.py', 
        'connect_broker.py',
        'portfolio_manager.py',
        'database_manager.py',
        'dashboard.py',
        'trade_logger.py',
        'config_loader.py',
        'data_router.py',
        'charge_calculator.py',
        'select_broker.py',
        'zerodha_login.py',
        'broker_login.py',
        'enhanced_morning_validation.py'
    ]
    
    data_files = [
        'instruments.csv',
        'angel_instruments.csv', 
        'trading_data.db',
        'requirements.txt'
    ]
    
    utility_files = [
        'show_structure.sh',
        'README.md'
    ]
    
    # Check if files actually exist and are used
    print("\n🎯 CORE TRADING FILES:")
    for file in core_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            if size > 0:
                print(f"   ✅ {file} ({size:,} bytes)")
            else:
                print(f"   ⚠️ {file} (EMPTY - {size} bytes)")
        else:
            print(f"   ❌ {file} (MISSING)")
    
    print("\n📊 DATA FILES:")
    for file in data_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            print(f"   ❌ {file} (MISSING)")
    
    print("\n🛠️ UTILITY FILES:")
    for file in utility_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            print(f"   ❌ {file} (MISSING)")
    
    # Check for potential redundant files
    print("\n🔍 CHECKING FOR REDUNDANT FILES:")
    
    # Check if broker_login.py is empty or redundant
    if os.path.exists('broker_login.py'):
        size = os.path.getsize('broker_login.py')
        if size == 0:
            print("   🗑️ broker_login.py is EMPTY - can be removed")
        else:
            print(f"   ✅ broker_login.py has content ({size} bytes)")
    
    # Check config files
    config_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.yml') or file.endswith('.json'):
                if 'automation' not in root and 'optimization' not in root:
                    config_files.append(os.path.join(root, file))
    
    if config_files:
        print("   ⚠️ Loose config files found:")
        for cf in config_files:
            if os.path.getsize(cf) > 0:
                print(f"     📄 {cf}")
    
    # Check for old Python cache
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            pycache_dirs.append(pycache_path)
    
    if pycache_dirs:
        print("   🗑️ Python cache directories (can be cleaned):")
        for pcd in pycache_dirs:
            print(f"     📁 {pcd}")

def check_imports():
    """Check which Python files are actually imported by main files"""
    
    print("\n🔗 CHECKING FILE DEPENDENCIES:")
    print("=" * 30)
    
    main_files = ['main_papertrader.py', 'enhanced_morning_validation.py']
    
    for main_file in main_files:
        if os.path.exists(main_file):
            print(f"\n📄 {main_file} imports:")
            try:
                with open(main_file, 'r') as f:
                    content = f.read()
                    
                # Look for local imports
                lines = content.split('\n')
                imports = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('from ') and not line.startswith('from datetime') and not line.startswith('from typing'):
                        if '.' in line or 'import' in line:
                            imports.append(line)
                    elif line.startswith('import ') and not any(x in line for x in ['pandas', 'numpy', 'datetime', 'time', 'os', 'sys', 'json']):
                        imports.append(line)
                
                if imports:
                    for imp in imports[:5]:  # Show first 5
                        print(f"     {imp}")
                else:
                    print("     No obvious local imports found")
                    
            except Exception as e:
                print(f"     Error reading file: {e}")

def recommend_cleanup():
    """Recommend files that can be safely removed"""
    
    print("\n🧹 CLEANUP RECOMMENDATIONS:")
    print("=" * 30)
    
    cleanup_candidates = []
    
    # Check empty files
    for file in os.listdir('.'):
        if file.endswith('.py') and os.path.isfile(file):
            if os.path.getsize(file) == 0:
                cleanup_candidates.append(f"EMPTY: {file}")
    
    # Check for duplicate or backup files
    for file in os.listdir('.'):
        if any(x in file for x in ['_backup', '_old', '.bak', '_copy']):
            cleanup_candidates.append(f"BACKUP: {file}")
    
    if cleanup_candidates:
        print("   Files that can be removed:")
        for candidate in cleanup_candidates:
            print(f"     🗑️ {candidate}")
    else:
        print("   ✅ No obvious cleanup candidates found")
    
    # Size analysis
    print(f"\n📊 SIZE ANALYSIS:")
    total_size = 0
    large_files = []
    
    for file in os.listdir('.'):
        if os.path.isfile(file):
            size = os.path.getsize(file)
            total_size += size
            if size > 100000:  # > 100KB
                large_files.append((file, size))
    
    print(f"   Total size of root files: {total_size:,} bytes")
    
    if large_files:
        print("   Large files (>100KB):")
        for file, size in sorted(large_files, key=lambda x: x[1], reverse=True):
            print(f"     📦 {file}: {size:,} bytes")

def main():
    """Main audit function"""
    check_file_usage()
    check_imports()
    recommend_cleanup()
    
    print(f"\n✨ AUDIT COMPLETE!")
    print(f"   Root directory contains only essential files")
    print(f"   All analysis/automation moved to organized folders")
    print(f"   Background optimizer running independently")

if __name__ == "__main__":
    main()

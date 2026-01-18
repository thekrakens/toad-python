#!/usr/bin/env python3
"""
Debug script to examine the Planned field structure
"""

import sys
import os
from datetime import date, datetime
import pandas as pd

# Add the parent directory to the path so we can import toad
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toad.notion_client import TOADNotionClient
from toad.productivity.task_relations import TaskRelationsManager

def debug_planned_field():
    """Debug the Planned field to understand its structure"""
    
    print("🔍 DEBUGGING PLANNED FIELD STRUCTURE")
    print("="*50)
    
    # Initialize the task relations manager
    notion_client = TOADNotionClient()
    relations_manager = TaskRelationsManager(notion_client)
    
    # Extract task data
    print("📊 Extracting task data...")
    tasks_df = relations_manager.task_extractor.extract_tasks_to_dataframe()
    
    print(f"   Tasks extracted: {len(tasks_df)}")
    
    # Check for planned-related columns
    planned_columns = [col for col in tasks_df.columns if 'plan' in col.lower()]
    print(f"\n📋 Planning-related columns found: {planned_columns}")
    
    # Look at the Planned field specifically
    if 'Planned' in tasks_df.columns:
        print(f"\n🎯 EXAMINING 'Planned' FIELD:")
        
        # Get tasks with non-null Planned values
        planned_tasks = tasks_df[tasks_df['Planned'].notna()]
        print(f"   Tasks with Planned values: {len(planned_tasks)}")
        
        if len(planned_tasks) > 0:
            print(f"\n📝 Sample Planned values:")
            for i, (_, task) in enumerate(planned_tasks.head(10).iterrows()):
                planned_val = task['Planned']
                task_name = task.get('Name', 'Unknown')[:40]
                print(f"   {i+1}. {task_name} | Planned: {planned_val} | Type: {type(planned_val)}")
                
                # If it's a date range, try to extract start/end
                if hasattr(planned_val, 'start') and hasattr(planned_val, 'end'):
                    print(f"      └─ Start: {planned_val.start} | End: {planned_val.end}")
                elif isinstance(planned_val, dict):
                    print(f"      └─ Dict keys: {list(planned_val.keys())}")
                    if 'start' in planned_val:
                        print(f"      └─ Start: {planned_val['start']}")
                    if 'end' in planned_val:
                        print(f"      └─ End: {planned_val['end']}")
            
            # Look for tasks around 2025-07-31
            print(f"\n🎯 SEARCHING FOR TASKS AROUND 2025-07-31:")
            target_date = datetime(2025, 7, 31).date()
            
            found_any = False
            for _, task in planned_tasks.iterrows():
                planned_val = task['Planned']
                task_name = task.get('Name', 'Unknown')
                
                # Try different ways to extract date info
                try:
                    dates_to_check = []
                    
                    # Method 1: If it's a string, parse it
                    if isinstance(planned_val, str):
                        if '2025-07-31' in planned_val:
                            dates_to_check.append(planned_val)
                    
                    # Method 2: If it's a dict with start/end
                    elif isinstance(planned_val, dict):
                        if 'start' in planned_val and planned_val['start'] and '2025-07-31' in str(planned_val['start']):
                            dates_to_check.append(planned_val)
                        if 'end' in planned_val and planned_val['end'] and '2025-07-31' in str(planned_val['end']):
                            dates_to_check.append(planned_val)
                    
                    # Method 3: If it has start/end attributes
                    elif hasattr(planned_val, 'start') or hasattr(planned_val, 'end'):
                        if hasattr(planned_val, 'start') and planned_val.start and '2025-07-31' in str(planned_val.start):
                            dates_to_check.append(planned_val)
                        if hasattr(planned_val, 'end') and planned_val.end and '2025-07-31' in str(planned_val.end):
                            dates_to_check.append(planned_val)
                    
                    if dates_to_check:
                        print(f"   📅 FOUND: {task_name[:50]}")
                        print(f"      └─ Planned: {planned_val}")
                        found_any = True
                        
                        # Check specifically for known task names
                        known_names = ['pay bills', 'Q2 Earnings Call', 'AiQ Sync', 'heatmap']
                        for known_name in known_names:
                            if known_name.lower() in task_name.lower():
                                print(f"      🎉 MATCHES EXPECTED TASK: {known_name}")
                        
                except Exception as e:
                    # Silently continue - we're just exploring
                    pass
            
            if not found_any:
                print("   ❌ No tasks found with 2025-07-31 in Planned field")
                
                # Show a few more recent tasks for reference
                print(f"\n📋 Recent Planned tasks for reference:")
                recent_count = 0
                for _, task in planned_tasks.iterrows():
                    if recent_count >= 5:
                        break
                    planned_val = task['Planned']
                    task_name = task.get('Name', 'Unknown')[:40]
                    if '2025-07' in str(planned_val) or '2025-08' in str(planned_val):
                        print(f"   • {task_name} | {planned_val}")
                        recent_count += 1
    
    else:
        print("❌ No 'Planned' column found!")

if __name__ == "__main__":
    debug_planned_field()

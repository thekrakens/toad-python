#!/usr/bin/env python3
"""
Test script for task relations logic validation.
Tests the core logic for identifying Planned, Active, Worked, and Done tasks
without actually updating Notion relations.
"""

import sys
import os
from datetime import date, datetime
from typing import Dict, List

# Add the parent directory to the path so we can import toad
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toad.notion_client import TOADNotionClient
from toad.productivity.task_relations import TaskRelationsManager

def test_task_relations_logic(test_date_str: str):
    """Test the task relations logic for a specific date without making Notion updates"""
    
    print(f"\n{'='*60}")
    print(f"🐸 TESTING TASK RELATIONS LOGIC FOR {test_date_str}")
    print(f"{'='*60}")
    
    try:
        # Parse the test date
        test_date = datetime.strptime(test_date_str, '%Y-%m-%d').date()
        
        # Initialize the task relations manager
        notion_client = TOADNotionClient()
        relations_manager = TaskRelationsManager(notion_client)
        
        # Extract data
        print("📊 Extracting task and time entry data...")
        tasks_df = relations_manager.task_extractor.extract_tasks_to_dataframe()
        time_entries_df = relations_manager.time_entry_extractor.extract_time_entries_to_dataframe()
        
        print(f"   Tasks extracted: {len(tasks_df)}")
        print(f"   Time entries extracted: {len(time_entries_df)}")
        
        # Test each relation type logic
        print(f"\n🔍 Testing relation logic for {test_date}:")
        
        # 1. PLANNED - Tasks with Planned Timeline for target date
        planned_tasks = relations_manager._get_planned_tasks(tasks_df, test_date)
        print(f"\n📋 PLANNED ({len(planned_tasks)} tasks):")
        
        # Check which planned column exists
        planned_col = None
        if "Planned" in tasks_df.columns:
            planned_col = "Planned"
        elif "Planned Timeline" in tasks_df.columns:
            planned_col = "Planned Timeline"
        
        print(f"   Logic: Tasks with '{planned_col}' set to {test_date}")
        print(f"   Available columns: {[col for col in tasks_df.columns if 'plan' in col.lower()]}")
        
        if planned_tasks:
            print(f"   Task IDs: {planned_tasks}")
            print(f"\n   📝 COMPLETE LIST OF PLANNED TASKS:")
            for i, task_id in enumerate(planned_tasks, 1):
                task_row = tasks_df[tasks_df['page_id'] == task_id]
                if not task_row.empty:
                    task_name = task_row.iloc[0].get('Name', 'Unknown')
                    planned_timeline = task_row.iloc[0].get(planned_col, 'None')
                    print(f"     {i:2d}. {task_name[:60]:<60} | {planned_timeline}")
        else:
            print("   No planned tasks found for this date")
        
        # 2. ACTIVE - Tasks on the list for the day  
        active_tasks = relations_manager._get_active_tasks(tasks_df, time_entries_df, test_date)
        print(f"\n🎯 ACTIVE ({len(active_tasks)} tasks):")
        print(f"   Logic: Planned today OR worked today OR planned earlier but not done")
        
        if active_tasks:
            print(f"   Task IDs: {active_tasks}")
            
            # Show breakdown of active task sources
            planned_today = set(planned_tasks)
            worked_today = set(relations_manager._get_worked_tasks(time_entries_df, test_date))
            active_set = set(active_tasks)
            
            planned_today_count = len(active_set & planned_today)
            worked_today_count = len(active_set & worked_today)
            
            print(f"     • From planned today: {planned_today_count}")
            print(f"     • From worked today: {worked_today_count}")
            print(f"     • From earlier planning: {len(active_tasks) - len(active_set & (planned_today | worked_today))}")
            
            print(f"\n   📝 COMPLETE LIST OF ACTIVE TASKS:")
            for i, task_id in enumerate(active_tasks, 1):
                task_row = tasks_df[tasks_df['page_id'] == task_id]
                if not task_row.empty:
                    task_name = task_row.iloc[0].get('Name', 'Unknown')
                    source = []
                    if task_id in planned_today:
                        source.append("planned")
                    if task_id in worked_today:
                        source.append("worked")
                    if not source:
                        source.append("earlier-planning")
                    print(f"     {i:2d}. {task_name[:60]:<60} | Source: {', '.join(source)}")
        else:
            print("   No active tasks found for this date")
        
        # 3. WORKED - Tasks with time entries on target date
        worked_tasks = relations_manager._get_worked_tasks(time_entries_df, test_date)
        print(f"\n⏰ WORKED ({len(worked_tasks)} tasks):")
        print(f"   Logic: Tasks with time entries recorded on {test_date}")
        
        if worked_tasks:
            print(f"   Task IDs: {worked_tasks}")
            print(f"\n   📝 COMPLETE LIST OF WORKED TASKS:")
            for i, task_id in enumerate(worked_tasks, 1):
                task_row = tasks_df[tasks_df['page_id'] == task_id]
                if not task_row.empty:
                    task_name = task_row.iloc[0].get('Name', 'Unknown')
                    print(f"     {i:2d}. {task_name[:60]:<60} | ID: {task_id}")
        else:
            print("   No worked tasks found for this date")
        
        # 4. DONE - Tasks completed on target date  
        done_tasks = relations_manager._get_done_tasks(tasks_df, test_date)
        print(f"\n✅ DONE ({len(done_tasks)} tasks):")
        print(f"   Logic: Tasks with 'Done' date set to {test_date}")
        
        if done_tasks:
            print(f"   Task IDs: {done_tasks}")
            print(f"\n   📝 COMPLETE LIST OF DONE TASKS:")
            for i, task_id in enumerate(done_tasks, 1):
                task_row = tasks_df[tasks_df['page_id'] == task_id]
                if not task_row.empty:
                    task_name = task_row.iloc[0].get('Name', 'Unknown')
                    done_date = task_row.iloc[0].get('Done', 'None')
                    print(f"     {i:2d}. {task_name[:60]:<60} | Done: {done_date}")
        else:
            print("   No completed tasks found for this date")
        
        # Summary
        print(f"\n📈 SUMMARY FOR {test_date}:")
        print(f"  📋 Planned: {len(planned_tasks)} tasks")
        print(f"  🎯 Active:  {len(active_tasks)} tasks")
        print(f"  ⏰ Worked:  {len(worked_tasks)} tasks")
        print(f"  ✅ Done:    {len(done_tasks)} tasks")
        
        # Overlap analysis
        planned_set = set(planned_tasks)
        active_set = set(active_tasks)
        worked_set = set(worked_tasks)
        done_set = set(done_tasks)
        
        print(f"\n🔄 OVERLAP ANALYSIS:")
        print(f"  Planned ∩ Worked: {len(planned_set & worked_set)} tasks")
        print(f"  Planned ∩ Done:   {len(planned_set & done_set)} tasks")
        print(f"  Active ∩ Worked:  {len(active_set & worked_set)} tasks")
        print(f"  Active ∩ Done:    {len(active_set & done_set)} tasks")
        print(f"  Worked ∩ Done:    {len(worked_set & done_set)} tasks")
        
        return {
            'date': test_date_str,
            'planned': len(planned_tasks),
            'active': len(active_tasks),
            'worked': len(worked_tasks),
            'done': len(done_tasks),
            'planned_ids': planned_tasks,
            'active_ids': active_tasks,
            'worked_ids': worked_tasks,
            'done_ids': done_tasks
        }
        
    except Exception as e:
        print(f"❌ Error testing logic for {test_date_str}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test task relations logic for multiple dates"""
    
    # Test dates - you can modify these
    test_dates = [
        "2025-07-25",  # Past date with likely activity
        "2025-07-26",  # Another past date
        "2025-08-01",  # Recent date
        "2025-08-02",  # Today
    ]
    
    print("🐸 TOAD Task Relations Logic Tester")
    print("This script tests the core logic without making any Notion updates")
    
    # Allow command line date input
    if len(sys.argv) > 1:
        test_dates = [sys.argv[1]]
    
    results = []
    
    for test_date in test_dates:
        result = test_task_relations_logic(test_date)
        if result:
            results.append(result)
    
    # Overall summary
    print(f"\n{'='*60}")
    print(f"🎯 OVERALL SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        print(f"{result['date']}: P:{result['planned']} A:{result['active']} W:{result['worked']} D:{result['done']}")
    
    print(f"\n✅ Logic testing complete!")
    print(f"📝 Once you're satisfied with the logic, you can add the relation")
    print(f"   properties to your Daily Productivity Metrics database:")
    print(f"   • Planned (Relation to Tasks)")
    print(f"   • Active (Relation to Tasks)")  
    print(f"   • Worked (Relation to Tasks)")
    print(f"   • Done (Relation to Tasks)")

if __name__ == "__main__":
    main()

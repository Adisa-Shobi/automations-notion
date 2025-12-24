#!/usr/bin/env python3
"""
Notion Daily Planner Auto-Rollover Script
Rolls over incomplete tasks from past dates to today at 8pm daily
"""

import os
from datetime import datetime, timedelta
import requests

# Configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "YOUR_INTEGRATION_TOKEN_HERE")
DATABASE_ID = "eab92f8e866448479d5e6dde8eb8a920"  # Your Daily Planner database ID

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_overdue_tasks():
    """Find all tasks that are not Done and have due dates in the past"""
    today = datetime.now().date().isoformat()
    
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # Query for tasks where Status != Done and Due Date < Today
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Status",
                    "select": {
                        "does_not_equal": "Done"
                    }
                },
                {
                    "property": "Due Date",
                    "date": {
                        "before": today
                    }
                }
            ]
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        print(f"Error querying database: {response.status_code}")
        print(response.text)
        return []
    
    return response.json().get("results", [])


def update_task_date(page_id, new_date):
    """Update a task's due date to today"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    payload = {
        "properties": {
            "Due Date": {
                "date": {
                    "start": new_date
                }
            }
        }
    }
    
    response = requests.patch(url, headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        print(f"Error updating page {page_id}: {response.status_code}")
        print(response.text)
        return False


def rollover_tasks():
    """Main function to roll over all overdue tasks"""
    print(f"Running rollover at {datetime.now()}")
    
    # Get today's date
    today = datetime.now().date().isoformat()
    
    # Find overdue tasks
    overdue_tasks = get_overdue_tasks()
    
    if not overdue_tasks:
        print("No overdue tasks found. All done!")
        return
    
    print(f"Found {len(overdue_tasks)} overdue task(s)")
    
    # Update each task
    updated_count = 0
    for task in overdue_tasks:
        page_id = task["id"]
        task_name = task["properties"]["Name"]["title"][0]["plain_text"] if task["properties"]["Name"]["title"] else "Untitled"
        
        print(f"Rolling over: {task_name}")
        
        if update_task_date(page_id, today):
            updated_count += 1
            print(f"  ✓ Updated to {today}")
        else:
            print(f"  ✗ Failed to update")
    
    print(f"\nRollover complete: {updated_count}/{len(overdue_tasks)} tasks updated")


if __name__ == "__main__":
    rollover_tasks()

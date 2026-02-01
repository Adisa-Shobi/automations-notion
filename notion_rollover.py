#!/usr/bin/env python3
"""
Notion Daily Planner Auto-Rollover Script
Rolls over incomplete tasks from past dates to today at 8pm daily
"""

import os
from datetime import datetime, timedelta
import requests
import time

# Configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "YOUR_INTEGRATION_TOKEN_HERE")
DATABASE_ID = "eab92f8e866448479d5e6dde8eb8a920"  # Your Daily Planner database ID

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Rate limiting: Notion allows 3 requests per second
REQUEST_DELAY = 0.4  # 400ms between requests = ~2.5 req/sec (safe buffer)
MAX_TASKS_PER_RUN = 25  # Process max 25 tasks per run to avoid timeouts

def get_overdue_tasks():
    """Find all tasks that are To Do or Doing and have due dates in the past"""
    today = datetime.now().date().isoformat()
    
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # Query for tasks where Status = To Do OR Doing, and Due Date < Today
    payload = {
        "filter": {
            "and": [
                {
                    "or": [
                        {
                            "property": "Status",
                            "select": {
                                "equals": "To Do"
                            }
                        },
                        {
                            "property": "Status",
                            "select": {
                                "equals": "Doing"
                            }
                        }
                    ]
                },
                {
                    "property": "Due Date",
                    "date": {
                        "on_or_before": today
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


def update_task_date(page_id, new_date, max_retries=3):
    """Update a task's due date to today with retry logic"""
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
    
    for attempt in range(max_retries):
        try:
            response = requests.patch(url, headers=HEADERS, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            elif response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 5))
                print(f"  ⏸ Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            else:
                print(f"  ✗ Error {response.status_code}: {response.text}")
                return False
                
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"  ⚠ Connection error, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  ✗ Failed after {max_retries} attempts: {str(e)}")
                return False
    
    return False


def rollover_tasks():
    """Main function to roll over all overdue tasks"""
    print(f"Running rollover at {datetime.now()}")
    
    # Get today's date
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    
    # Find overdue tasks
    overdue_tasks = get_overdue_tasks()
    
    if not overdue_tasks:
        print("No overdue tasks found. All done!")
        return
    
    total_tasks = len(overdue_tasks)
    tasks_to_process = overdue_tasks[:MAX_TASKS_PER_RUN]
    
    if total_tasks > MAX_TASKS_PER_RUN:
        print(f"Found {total_tasks} overdue task(s)")
        print(f"Processing first {MAX_TASKS_PER_RUN} tasks (remaining will be processed in next run)")
    else:
        print(f"Found {total_tasks} overdue task(s)")
    
    # Update each task with rate limiting
    updated_count = 0
    failed_count = 0
    
    for i, task in enumerate(tasks_to_process, 1):
        page_id = task["id"]
        task_name = task["properties"]["Name"]["title"][0]["plain_text"] if task["properties"]["Name"]["title"] else "Untitled"
        
        print(f"[{i}/{len(tasks_to_process)}] Rolling over: {task_name}")
        
        if update_task_date(page_id, tomorrow):
            updated_count += 1
            print(f"  ✓ Updated to {tomorrow}")
        else:
            failed_count += 1
            print(f"  ✗ Failed to update")
        
        # Rate limiting: wait between requests (except on last item)
        if i < len(tasks_to_process):
            time.sleep(REQUEST_DELAY)
    
    print(f"\n{'='*50}")
    print(f"Rollover complete:")
    print(f"  ✓ Updated: {updated_count}")
    if failed_count > 0:
        print(f"  ✗ Failed: {failed_count}")
    if total_tasks > MAX_TASKS_PER_RUN:
        remaining = total_tasks - MAX_TASKS_PER_RUN
        print(f"  ⏳ Remaining: {remaining} (will process in next run)")
    print(f"{'='*50}")


if __name__ == "__main__":
    rollover_tasks()

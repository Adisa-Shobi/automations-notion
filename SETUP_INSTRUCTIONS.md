# Notion Auto-Rollover Setup Guide

This script automatically rolls over incomplete tasks from past dates to today.

## What You Need

1. Python 3.7+ installed
2. Your Notion integration token
3. A way to run the script daily at 8pm

## Setup Steps

### 1. Get Your Notion Integration Token

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Name it: "Task Rollover Bot"
4. Submit and copy the token (starts with `secret_`)

### 2. Give Integration Access to Your Database

1. Open your Daily Planner in Notion
2. Click "..." (top right)
3. Click "Connections" or "Add connections"
4. Select "Task Rollover Bot"

### 3. Set Up the Script

**Option A: Run Locally (Your Computer)**

1. Save `notion_rollover.py` to your computer
2. Install requests library:
   ```bash
   pip install requests
   ```
3. Set your token as an environment variable:
   ```bash
   # On Mac/Linux:
   export NOTION_TOKEN="your_token_here"
   
   # On Windows:
   set NOTION_TOKEN=your_token_here
   ```
   
4. Test it:
   ```bash
   python notion_rollover.py
   ```

**Option B: Run on GitHub Actions (Free, Cloud-Based)**

1. Create a new GitHub repository (can be private)
2. Upload `notion_rollover.py` to the repo
3. Create `.github/workflows/rollover.yml`:

```yaml
name: Daily Task Rollover

on:
  schedule:
    # Runs at 8:00 PM UTC daily (adjust timezone as needed)
    - cron: '0 20 * * *'
  workflow_dispatch:  # Allows manual triggering

jobs:
  rollover:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Run rollover script
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
        run: python notion_rollover.py
```

4. In your GitHub repo:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `NOTION_TOKEN`
   - Value: Your integration token
   - Save

5. The script will now run automatically at 8pm UTC daily

**Option C: Run on Render.com (Free, Cloud-Based)**

1. Sign up at https://render.com
2. Create a new "Cron Job"
3. Connect your GitHub repo (or upload the script)
4. Set schedule: `0 20 * * *` (8pm daily)
5. Add environment variable: `NOTION_TOKEN` = your token
6. Deploy

## Timezone Notes

The cron schedule `0 20 * * *` runs at 8:00 PM in the timezone of where it's running:
- GitHub Actions: UTC (adjust as needed)
- Your computer: Your local timezone
- Render: UTC

To convert 8pm your time to UTC:
- If you're UTC+2 (e.g., Kigali): Use `0 18 * * *` (6pm UTC = 8pm Kigali)
- If you're UTC-5 (e.g., EST): Use `0 1 * * *` (1am UTC next day = 8pm EST)

## How It Works

1. Script runs at 8pm daily
2. Finds all tasks where:
   - Status ≠ "Done"
   - Due Date < Today
3. Updates their Due Date to today
4. You see them in your planner tomorrow morning

## Testing

Run manually to see it work:
```bash
python notion_rollover.py
```

Output will show:
```
Running rollover at 2025-12-24 20:00:00
Found 3 overdue task(s)
Rolling over: Update resume
  ✓ Updated to 2025-12-24
Rolling over: Apply to jobs
  ✓ Updated to 2025-12-24
Rolling over: LeetCode practice
  ✓ Updated to 2025-12-24

Rollover complete: 3/3 tasks updated
```

## Troubleshooting

**"Error 401: Unauthorized"**
- Check your integration token is correct
- Make sure you gave the integration access to your Daily Planner database

**"No overdue tasks found" (but you know there are some)**
- Check the DATABASE_ID in the script matches your Daily Planner
- Make sure tasks have Status ≠ "Done" and Due Date in the past

**Script doesn't run automatically**
- Check your cron schedule is correct
- Verify environment variables are set properly
- Check logs in GitHub Actions or Render dashboard

## Which Option Should You Choose?

- **GitHub Actions**: Best if you already use GitHub. 100% free. Easy to monitor.
- **Render**: Good if you don't have GitHub. Free tier available. Simple setup.
- **Your Computer**: Only if your computer is always on. Not recommended for laptops.

I recommend GitHub Actions - it's reliable, free forever, and you can see logs of every run.

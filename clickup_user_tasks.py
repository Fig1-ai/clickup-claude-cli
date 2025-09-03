#!/usr/bin/env python3
"""
ClickUp CLI to fetch tasks for a specific user
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from tabulate import tabulate


class ClickUpUserTasksCLI:
    """ClickUp CLI for fetching specific user's tasks."""
    
    def __init__(self):
        """Initialize with API token from config."""
        self.api_token = self._load_token()
        if not self.api_token:
            raise ValueError("ClickUp API token not found. Please run setup first.")
        
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
    
    def _load_token(self) -> Optional[str]:
        """Load API token from config file."""
        config_path = Path.home() / ".clickup" / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('api_token')
        return None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request to ClickUp."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"API Error {response.status_code}: {response.text}")
        
        return response.json()
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams/workspaces."""
        response = self._make_request("GET", "team")
        return response.get("teams", [])
    
    def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all members of a team."""
        teams = self.get_teams()
        for team in teams:
            if team['id'] == team_id:
                return team.get('members', [])
        return []
    
    def find_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a user by name across all teams."""
        name_lower = name.lower()
        teams = self.get_teams()
        
        for team in teams:
            members = team.get('members', [])
            for member in members:
                user = member.get('user', {})
                username = user.get('username', '') or ''
                email = user.get('email', '') or ''
                
                # Check if name matches username or email (case-insensitive)
                if username and name_lower in username.lower():
                    print(f"✅ Found user: {username} ({email})")
                    return user
                elif email and name_lower in email.lower():
                    print(f"✅ Found user: {username} ({email})")
                    return user
        
        # Also check for exact matches in initials or full name
        print(f"Checking all team members for '{name}'...")
        for team in teams:
            members = team.get('members', [])
            for member in members:
                user = member.get('user', {})
                username = user.get('username', '') or ''
                email = user.get('email', '') or ''
                initials = user.get('initials', '') or ''
                
                if username:
                    print(f"  - {username} ({email})")
                
                # Check various name formats
                if (username and name_lower == username.lower()) or \
                   (initials and name_lower == initials.lower()) or \
                   (email and name_lower.split('@')[0] in email.lower()):
                    print(f"✅ Found user: {username} ({email})")
                    return user
        
        return None
    
    def get_user_tasks(self, user_id: str, team_id: str = None) -> List[Dict[str, Any]]:
        """Get all tasks assigned to a specific user."""
        all_tasks = []
        
        if team_id:
            teams = [{'id': team_id}]
        else:
            teams = self.get_teams()
        
        for team in teams:
            try:
                # Get tasks assigned to the specific user
                params = {
                    "assignees[]": user_id,
                    "include_closed": False,
                    "subtasks": True
                }
                
                tasks_response = self._make_request("GET", f"team/{team['id']}/task", params=params)
                tasks = tasks_response.get("tasks", [])
                all_tasks.extend(tasks)
                
            except Exception as e:
                print(f"Warning: Could not fetch tasks from team {team.get('name', team['id'])}: {e}", file=sys.stderr)
                continue
        
        return all_tasks
    
    def format_tasks_as_table(self, tasks: List[Dict[str, Any]], username: str) -> str:
        """Format tasks as a detailed table."""
        if not tasks:
            return f"No tasks found for {username}."
        
        table_data = []
        
        for task in tasks:
            # Task name
            name = task.get('name', 'Unnamed')[:40]
            
            # Status
            status = task.get('status', {}).get('status', 'No status')
            
            # Priority
            priority = task.get('priority')
            if priority:
                priority_map = {1: "🔴 Urgent", 2: "🟡 High", 3: "🔵 Normal", 4: "⚪ Low"}
                priority_str = priority_map.get(priority.get('priority', 0), "None")
            else:
                priority_str = "None"
            
            # Due date
            due_date = task.get('due_date')
            if due_date:
                dt = datetime.fromtimestamp(int(due_date) / 1000)
                due_str = dt.strftime('%Y-%m-%d')
                # Check if overdue
                if dt < datetime.now():
                    due_str = f"⚠️ {due_str}"
            else:
                due_str = "-"
            
            # Description (truncated)
            description = task.get('description', '')
            if description:
                import re
                description = re.sub('<[^<]+?>', '', description)
                description = description[:60] + "..." if len(description) > 60 else description
                description = description.replace('\n', ' ')
            else:
                description = "-"
            
            # List/Location
            list_name = task.get('list', {}).get('name', 'Unknown')
            folder_name = task.get('folder', {}).get('name', '')
            space_name = task.get('space', {}).get('name', '')
            
            if folder_name:
                location = f"{space_name}/{folder_name}/{list_name}"
            elif space_name:
                location = f"{space_name}/{list_name}"
            else:
                location = list_name
            
            # Tags
            tags = task.get('tags', [])
            tag_names = [tag.get('name', '') for tag in tags]
            tags_str = ', '.join(tag_names[:3]) if tag_names else "-"
            
            # Time estimate
            time_estimate = task.get('time_estimate')
            if time_estimate:
                hours = time_estimate / (1000 * 60 * 60)
                time_str = f"{hours:.1f}h"
            else:
                time_str = "-"
            
            table_data.append([
                name,
                status,
                priority_str,
                due_str,
                description,
                location,
                tags_str,
                time_str
            ])
        
        headers = ["Task", "Status", "Priority", "Due", "Description", "Location", "Tags", "Est."]
        
        return tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[40, 12, 10, 12, 60, 30, 20, 8])


def main():
    """Main function to display user's tasks."""
    if len(sys.argv) < 2:
        print("Usage: python clickup_user_tasks.py <username>")
        print("Example: python clickup_user_tasks.py jeremy")
        sys.exit(1)
    
    username = sys.argv[1]
    
    try:
        cli = ClickUpUserTasksCLI()
        
        print(f"🔍 Searching for user '{username}'...\n")
        
        # Find the user
        user = cli.find_user_by_name(username)
        
        if not user:
            print(f"❌ User '{username}' not found in any of your teams.")
            print("\nTip: Try searching with:")
            print("  - First name only")
            print("  - Part of their email address")
            print("  - Their ClickUp username")
            sys.exit(1)
        
        user_id = user['id']
        user_fullname = user.get('username', username)
        
        print(f"\n🔄 Fetching tasks for {user_fullname}...\n")
        
        # Get user's tasks
        tasks = cli.get_user_tasks(user_id)
        
        if not tasks:
            print(f"No active tasks found for {user_fullname}.")
            return
        
        # Sort tasks by due date (tasks without due date at the end)
        tasks.sort(key=lambda x: int(x.get('due_date', 0)) if x.get('due_date') else float('inf'))
        
        print(f"📊 Found {len(tasks)} active task(s) for {user_fullname}:\n")
        print(cli.format_tasks_as_table(tasks, user_fullname))
        
        # Summary statistics
        print(f"\n📈 Summary for {user_fullname}:")
        print(f"   Total active tasks: {len(tasks)}")
        
        # Count by status
        status_counts = {}
        for task in tasks:
            status = task.get('status', {}).get('status', 'No status')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("   By status:")
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      {status}: {count}")
        
        # Count overdue and upcoming
        now = datetime.now()
        overdue = 0
        due_this_week = 0
        due_this_month = 0
        
        for task in tasks:
            if task.get('due_date'):
                due_dt = datetime.fromtimestamp(int(task['due_date']) / 1000)
                if due_dt < now:
                    overdue += 1
                elif (due_dt - now).days <= 7:
                    due_this_week += 1
                elif (due_dt - now).days <= 30:
                    due_this_month += 1
        
        if overdue > 0:
            print(f"   ⚠️  Overdue: {overdue}")
        if due_this_week > 0:
            print(f"   📅 Due this week: {due_this_week}")
        if due_this_month > 0:
            print(f"   📆 Due this month: {due_this_month}")
        
        # Count by priority
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, None: 0}
        for task in tasks:
            priority = task.get('priority')
            if priority:
                priority_counts[priority.get('priority')] = priority_counts.get(priority.get('priority'), 0) + 1
            else:
                priority_counts[None] += 1
        
        if any(v > 0 for k, v in priority_counts.items() if k and k <= 2):
            print("   By priority:")
            if priority_counts.get(1, 0) > 0:
                print(f"      🔴 Urgent: {priority_counts[1]}")
            if priority_counts.get(2, 0) > 0:
                print(f"      🟡 High: {priority_counts[2]}")
            if priority_counts.get(3, 0) > 0:
                print(f"      🔵 Normal: {priority_counts[3]}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
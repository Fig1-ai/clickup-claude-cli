#!/usr/bin/env python3
"""
Enhanced ClickUp CLI for detailed task information with table display
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from tabulate import tabulate


class ClickUpDetailedCLI:
    """Enhanced ClickUp CLI for detailed task information."""
    
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
    
    def get_user(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        return self._make_request("GET", "user")
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams/workspaces."""
        response = self._make_request("GET", "team")
        return response.get("teams", [])
    
    def get_spaces(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all spaces in a team."""
        response = self._make_request("GET", f"team/{team_id}/space")
        return response.get("spaces", [])
    
    def get_folders(self, space_id: str) -> List[Dict[str, Any]]:
        """Get all folders in a space."""
        response = self._make_request("GET", f"space/{space_id}/folder")
        return response.get("folders", [])
    
    def get_lists(self, space_id: str) -> List[Dict[str, Any]]:
        """Get all lists in a space."""
        response = self._make_request("GET", f"space/{space_id}/list")
        return response.get("lists", [])
    
    def get_folder_lists(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get all lists in a folder."""
        response = self._make_request("GET", f"folder/{folder_id}/list")
        return response.get("lists", [])
    
    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific task."""
        return self._make_request("GET", f"task/{task_id}")
    
    def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """Get comments for a task."""
        response = self._make_request("GET", f"task/{task_id}/comment")
        return response.get("comments", [])
    
    def get_all_tasks_detailed(self, include_subtasks: bool = True) -> List[Dict[str, Any]]:
        """Get all tasks with detailed information."""
        all_tasks_detailed = []
        user = self.get_user()
        user_id = user['user']['id']
        
        teams = self.get_teams()
        
        for team in teams:
            try:
                # Get tasks assigned to user
                tasks_response = self._make_request("GET", f"team/{team['id']}/task", 
                                                   params={"assignees[]": user_id, 
                                                          "include_closed": False,
                                                          "subtasks": include_subtasks})
                tasks = tasks_response.get("tasks", [])
                
                # Enhance each task with additional details
                for task in tasks:
                    # Get comments for each task
                    try:
                        comments = self.get_task_comments(task['id'])
                        task['comments'] = comments
                    except:
                        task['comments'] = []
                    
                    all_tasks_detailed.append(task)
                    
            except Exception as e:
                print(f"Warning: Could not fetch tasks from team {team['name']}: {e}", file=sys.stderr)
                continue
        
        return all_tasks_detailed
    
    def format_tasks_as_table(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks as a detailed table."""
        if not tasks:
            return "No tasks found."
        
        table_data = []
        
        for task in tasks:
            # Task name
            name = task.get('name', 'Unnamed')[:50]  # Truncate long names
            
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
            else:
                due_str = "-"
            
            # Description (truncated)
            description = task.get('description', '')
            if description:
                # Remove HTML tags if present
                import re
                description = re.sub('<[^<]+?>', '', description)
                description = description[:100] + "..." if len(description) > 100 else description
                description = description.replace('\n', ' ')
            else:
                description = "-"
            
            # Parent task (if this is a subtask)
            parent = task.get('parent')
            if parent:
                parent_str = f"↳ Subtask of {parent}"[:30]
            else:
                parent_str = ""
            
            # Subtasks count
            subtasks = task.get('subtasks', [])
            subtask_count = len(subtasks) if subtasks else 0
            subtask_str = f"{subtask_count} subtasks" if subtask_count > 0 else "-"
            
            # Comments count
            comments = task.get('comments', [])
            comment_count = len(comments)
            
            # Latest comment preview
            if comment_count > 0 and comments:
                latest_comment = comments[0].get('comment_text', '')[:50]
                comment_str = f"{comment_count} comments"
                if latest_comment:
                    comment_str += f": {latest_comment}..."
            else:
                comment_str = "-"
            
            # List/Location
            list_name = task.get('list', {}).get('name', 'Unknown')
            folder_name = task.get('folder', {}).get('name', '')
            location = f"{folder_name}/{list_name}" if folder_name else list_name
            
            table_data.append([
                name,
                status,
                priority_str,
                due_str,
                description,
                subtask_str,
                comment_str,
                location,
                parent_str
            ])
        
        headers = ["Task", "Status", "Priority", "Due", "Description", "Subtasks", "Comments", "Location", "Parent"]
        
        return tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 12, 10, 10, 40, 10, 30, 20, 20])


def main():
    """Main function to display detailed tasks."""
    try:
        cli = ClickUpDetailedCLI()
        
        print("🔄 Fetching your ClickUp tasks with details...\n")
        
        # Get all tasks with details
        tasks = cli.get_all_tasks_detailed(include_subtasks=True)
        
        if not tasks:
            print("No tasks found.")
            return
        
        # Sort tasks by due date (tasks without due date at the end)
        tasks.sort(key=lambda x: int(x.get('due_date', 0)) if x.get('due_date') else float('inf'))
        
        print(f"📊 Found {len(tasks)} task(s):\n")
        print(cli.format_tasks_as_table(tasks))
        
        # Summary statistics
        print(f"\n📈 Summary:")
        print(f"   Total tasks: {len(tasks)}")
        
        # Count by status
        status_counts = {}
        for task in tasks:
            status = task.get('status', {}).get('status', 'No status')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("   By status:")
        for status, count in status_counts.items():
            print(f"      {status}: {count}")
        
        # Count overdue
        now = datetime.now()
        overdue = 0
        due_this_week = 0
        
        for task in tasks:
            if task.get('due_date'):
                due_dt = datetime.fromtimestamp(int(task['due_date']) / 1000)
                if due_dt < now:
                    overdue += 1
                elif (due_dt - now).days <= 7:
                    due_this_week += 1
        
        if overdue > 0:
            print(f"   ⚠️  Overdue: {overdue}")
        if due_this_week > 0:
            print(f"   📅 Due this week: {due_this_week}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
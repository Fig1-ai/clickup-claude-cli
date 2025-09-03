#!/usr/bin/env python3
"""
ClickUp CLI Integration for Claude CLI
Allows Claude CLI users to interact with ClickUp tasks directly from the command line.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, List, Any
from pathlib import Path


class ClickUpCLI:
    """Main class for ClickUp CLI integration."""
    
    def __init__(self, api_token: Optional[str] = None):
        """Initialize ClickUp CLI with API token."""
        self.api_token = api_token or self._load_token()
        if not self.api_token:
            raise ValueError("ClickUp API token not found. Please provide token or run setup.")
        
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
    
    @staticmethod
    def setup(api_token: str):
        """Setup ClickUp CLI with user's personal API token."""
        config_dir = Path.home() / ".clickup"
        config_dir.mkdir(exist_ok=True)
        config_path = config_dir / "config.json"
        
        config = {
            "api_token": api_token,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set file permissions to be readable only by the user
        os.chmod(config_path, 0o600)
        
        print(f"✅ ClickUp CLI configured successfully!")
        print(f"   Config saved to: {config_path}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request to ClickUp."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        if response.status_code != 200:
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
    
    def get_lists(self, space_id: str) -> List[Dict[str, Any]]:
        """Get all lists in a space."""
        response = self._make_request("GET", f"space/{space_id}/list")
        return response.get("lists", [])
    
    def get_tasks(self, list_id: str, **filters) -> List[Dict[str, Any]]:
        """Get tasks from a list with optional filters."""
        params = {}
        
        # Add date filters if specified
        if filters.get('due_this_week'):
            now = datetime.now()
            week_end = now + timedelta(days=(6 - now.weekday()))
            params['due_date_gt'] = int(now.timestamp() * 1000)
            params['due_date_lt'] = int(week_end.timestamp() * 1000)
        
        if filters.get('assignee') == 'me':
            user = self.get_user()
            params['assignees[]'] = user['user']['id']
        
        if filters.get('status'):
            params['statuses[]'] = filters['status']
        
        response = self._make_request("GET", f"list/{list_id}/task", params=params)
        return response.get("tasks", [])
    
    def get_all_tasks(self, **filters) -> List[Dict[str, Any]]:
        """Get all tasks across all accessible lists."""
        all_tasks = []
        teams = self.get_teams()
        
        for team in teams:
            spaces = self.get_spaces(team['id'])
            for space in spaces:
                # Include tasks from space-level lists
                lists = self.get_lists(space['id'])
                for list_item in lists:
                    tasks = self.get_tasks(list_item['id'], **filters)
                    all_tasks.extend(tasks)
        
        return all_tasks
    
    def create_task(self, list_id: str, name: str, description: str = "", 
                   priority: Optional[int] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task."""
        data = {
            "name": name,
            "description": description
        }
        
        if priority:
            data["priority"] = priority
        
        if due_date:
            # Convert date string to timestamp
            dt = datetime.fromisoformat(due_date)
            data["due_date"] = int(dt.timestamp() * 1000)
        
        return self._make_request("POST", f"list/{list_id}/task", json=data)
    
    def update_task(self, task_id: str, **updates) -> Dict[str, Any]:
        """Update an existing task."""
        data = {}
        
        if 'name' in updates:
            data['name'] = updates['name']
        
        if 'description' in updates:
            data['description'] = updates['description']
        
        if 'status' in updates:
            data['status'] = updates['status']
        
        if 'priority' in updates:
            data['priority'] = updates['priority']
        
        return self._make_request("PUT", f"task/{task_id}", json=data)
    
    def format_task(self, task: Dict[str, Any]) -> str:
        """Format task for display."""
        name = task.get('name', 'Unnamed')
        status = task.get('status', {}).get('status', 'No status')
        priority = task.get('priority')
        due_date = task.get('due_date')
        
        output = f"📋 {name}\n"
        output += f"   Status: {status}\n"
        
        if priority:
            priority_map = {1: "🔴 Urgent", 2: "🟡 High", 3: "🔵 Normal", 4: "⚪ Low"}
            output += f"   Priority: {priority_map.get(priority['priority'], 'Unknown')}\n"
        
        if due_date:
            dt = datetime.fromtimestamp(int(due_date) / 1000)
            output += f"   Due: {dt.strftime('%Y-%m-%d %H:%M')}\n"
        
        return output


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ClickUp CLI Integration for Claude CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup ClickUp CLI with your API token')
    setup_parser.add_argument('token', help='Your personal ClickUp API token')
    
    # User command
    subparsers.add_parser('whoami', help='Show current authenticated user')
    
    # Teams command
    subparsers.add_parser('teams', help='List all teams/workspaces')
    
    # Tasks command
    tasks_parser = subparsers.add_parser('tasks', help='List tasks')
    tasks_parser.add_argument('--due-this-week', action='store_true', help='Show only tasks due this week')
    tasks_parser.add_argument('--assigned-to-me', action='store_true', help='Show only tasks assigned to you')
    tasks_parser.add_argument('--list', help='List ID to fetch tasks from')
    
    # Create task command
    create_parser = subparsers.add_parser('create', help='Create a new task')
    create_parser.add_argument('list_id', help='List ID where task will be created')
    create_parser.add_argument('name', help='Task name')
    create_parser.add_argument('--description', help='Task description')
    create_parser.add_argument('--priority', type=int, choices=[1, 2, 3, 4], help='Priority (1=Urgent, 4=Low)')
    create_parser.add_argument('--due', help='Due date (ISO format: YYYY-MM-DD)')
    
    # Update task command
    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('task_id', help='Task ID to update')
    update_parser.add_argument('--name', help='New task name')
    update_parser.add_argument('--status', help='New status')
    update_parser.add_argument('--description', help='New description')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle setup command separately
    if args.command == 'setup':
        ClickUpCLI.setup(args.token)
        return
    
    # Initialize CLI for other commands
    try:
        cli = ClickUpCLI()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Run 'clickup_cli.py setup YOUR_API_TOKEN' to configure")
        sys.exit(1)
    
    try:
        if args.command == 'whoami':
            user = cli.get_user()
            print(f"👤 Authenticated as: {user['user']['username']}")
            print(f"   Email: {user['user']['email']}")
        
        elif args.command == 'teams':
            teams = cli.get_teams()
            print("🏢 Your Teams:")
            for team in teams:
                print(f"   • {team['name']} (ID: {team['id']})")
        
        elif args.command == 'tasks':
            filters = {}
            if args.due_this_week:
                filters['due_this_week'] = True
            if args.assigned_to_me:
                filters['assignee'] = 'me'
            
            if args.list:
                tasks = cli.get_tasks(args.list, **filters)
            else:
                tasks = cli.get_all_tasks(**filters)
            
            if not tasks:
                print("No tasks found matching criteria.")
            else:
                print(f"Found {len(tasks)} task(s):\n")
                for task in tasks:
                    print(cli.format_task(task))
        
        elif args.command == 'create':
            task = cli.create_task(
                args.list_id,
                args.name,
                description=args.description or "",
                priority=args.priority,
                due_date=args.due
            )
            print(f"✅ Task created successfully!")
            print(f"   ID: {task['id']}")
            print(f"   URL: {task['url']}")
        
        elif args.command == 'update':
            updates = {}
            if args.name:
                updates['name'] = args.name
            if args.status:
                updates['status'] = args.status
            if args.description:
                updates['description'] = args.description
            
            task = cli.update_task(args.task_id, **updates)
            print(f"✅ Task updated successfully!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
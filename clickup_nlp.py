#!/usr/bin/env python3
"""
Natural Language Processing interface for ClickUp CLI
Allows users to interact with ClickUp using natural language commands.
"""

import os
import sys
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import subprocess

class ClickUpNLP:
    """Natural Language Processing interface for ClickUp."""
    
    def __init__(self):
        """Initialize NLP interface."""
        self.patterns = self._build_patterns()
        self.check_setup()
    
    def check_setup(self):
        """Check if ClickUp CLI is set up."""
        config_path = Path.home() / ".clickup" / "config.json"
        if not config_path.exists():
            print("❌ ClickUp CLI not configured. Please run:")
            print("   python3 clickup_cli.py setup YOUR_API_TOKEN")
            sys.exit(1)
    
    def _build_patterns(self) -> List[Tuple[str, str, Dict]]:
        """Build regex patterns for natural language understanding."""
        return [
            # View tasks patterns
            (r"(show|list|get|what are|display).*my tasks", "view_my_tasks", {}),
            (r"(show|list|get).*tasks.*due.*(today|this week|tomorrow)", "view_tasks_due", {"period": "matched"}),
            (r"tasks.*(due|deadline).*(today|this week|tomorrow)", "view_tasks_due", {"period": "matched"}),
            (r"what.*(do I have|should I|need to).*(do|complete).*(today|this week)", "view_tasks_due", {"period": "matched"}),
            (r"(show|list|get).*overdue.*tasks?", "view_overdue", {}),
            (r"what.*overdue", "view_overdue", {}),
            
            # View specific user's tasks
            (r"(show|list|get|what are).*tasks.*(?:for|of|assigned to)\s+(\w+)", "view_user_tasks", {"user": "group2"}),
            (r"what.*(\w+).*working on", "view_user_tasks", {"user": "group1"}),
            (r"(\w+)(?:'s|s)?\s+tasks", "view_user_tasks", {"user": "group1"}),
            
            # Create task patterns
            (r"(create|add|make|new).*task.*[\"']([^\"']+)[\"']", "create_task", {"name": "group2"}),
            (r"remind me to\s+(.+)", "create_task", {"name": "group1"}),
            (r"add\s+[\"']([^\"']+)[\"'].*to.*list", "create_task", {"name": "group1"}),
            
            # Update task patterns
            (r"(mark|set|update).*task.*(\w+).*as\s+(done|complete|finished)", "update_task_status", {"status": "complete"}),
            (r"(close|finish|complete).*task.*(\w+)", "update_task_status", {"status": "complete"}),
            
            # Team and workspace patterns
            (r"(show|list|what are).*teams", "view_teams", {}),
            (r"(show|list|what are).*workspaces", "view_teams", {}),
            
            # User info patterns
            (r"who am i", "whoami", {}),
            (r"(show|what is).*my.*(profile|info|account)", "whoami", {}),
            
            # Priority tasks
            (r"(show|list|what are).*urgent.*tasks", "view_priority_tasks", {"priority": "urgent"}),
            (r"(show|list|what are).*high priority", "view_priority_tasks", {"priority": "high"}),
            (r"what.*important.*today", "view_priority_tasks", {"priority": "high"}),
            
            # Summary patterns
            (r"(summary|summarize|overview).*tasks", "task_summary", {}),
            (r"how many tasks", "task_summary", {}),
            (r"task.*(count|stats|statistics)", "task_summary", {}),
            
            # Detailed view
            (r"(show|view).*detailed.*tasks", "view_detailed", {}),
            (r"(show|view).*tasks.*with.*(comments|descriptions)", "view_detailed", {}),
            (r"full.*task.*list", "view_detailed", {}),
            
            # Help patterns
            (r"(help|what can you do|how do I)", "show_help", {}),
            (r"(examples|show examples)", "show_examples", {}),
        ]
    
    def parse_intent(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Parse user input to determine intent and extract parameters."""
        user_input_lower = user_input.lower().strip()
        
        for pattern, intent, params in self.patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                # Extract matched groups if needed
                extracted_params = params.copy()
                for key, value in params.items():
                    if value == "matched":
                        # Extract from the match itself
                        if "today" in user_input_lower:
                            extracted_params[key] = "today"
                        elif "tomorrow" in user_input_lower:
                            extracted_params[key] = "tomorrow"
                        elif "this week" in user_input_lower or "week" in user_input_lower:
                            extracted_params[key] = "this_week"
                    elif value.startswith("group"):
                        # Extract from regex groups
                        group_num = int(value.replace("group", ""))
                        if len(match.groups()) >= group_num:
                            extracted_params[key] = match.group(group_num)
                
                return intent, extracted_params
        
        return "unknown", {}
    
    def execute_intent(self, intent: str, params: Dict[str, Any]) -> None:
        """Execute the identified intent."""
        
        if intent == "view_my_tasks":
            print("📋 Fetching your tasks...")
            self._run_command(["python3", "clickup_cli.py", "tasks", "--assigned-to-me"])
        
        elif intent == "view_tasks_due":
            period = params.get("period", "this_week")
            if period in ["today", "tomorrow"]:
                print(f"📅 Tasks due {period} feature coming soon. Showing this week's tasks...")
            print("📅 Fetching tasks due this week...")
            self._run_command(["python3", "clickup_cli.py", "tasks", "--due-this-week"])
        
        elif intent == "view_overdue":
            print("⚠️ Fetching overdue tasks...")
            self._run_command(["python3", "clickup_detailed.py"])
        
        elif intent == "view_user_tasks":
            user = params.get("user", "").strip()
            if user:
                print(f"👤 Fetching tasks for {user}...")
                self._run_command(["python3", "clickup_user_tasks.py", user])
            else:
                print("❌ Could not determine which user's tasks to show.")
        
        elif intent == "create_task":
            task_name = params.get("name", "").strip()
            if task_name:
                print(f"📝 To create task '{task_name}', you'll need to specify a LIST_ID:")
                print("   Run: python3 clickup_cli.py teams  # to find your list")
                print(f"   Then: python3 clickup_cli.py create LIST_ID \"{task_name}\"")
            else:
                print("❌ Could not determine task name to create.")
        
        elif intent == "update_task_status":
            print("✏️ To update task status, you'll need the task ID:")
            print("   Run: python3 clickup_cli.py tasks  # to find task IDs")
            print("   Then: python3 clickup_cli.py update TASK_ID --status complete")
        
        elif intent == "view_teams":
            print("🏢 Fetching your teams...")
            self._run_command(["python3", "clickup_cli.py", "teams"])
        
        elif intent == "whoami":
            print("👤 Fetching your profile...")
            self._run_command(["python3", "clickup_cli.py", "whoami"])
        
        elif intent == "view_priority_tasks":
            priority = params.get("priority", "high")
            print(f"🔥 Fetching {priority} priority tasks...")
            self._run_command(["python3", "clickup_detailed.py"])
        
        elif intent == "task_summary":
            print("📊 Generating task summary...")
            self._run_command(["python3", "clickup_detailed.py"])
        
        elif intent == "view_detailed":
            print("📊 Fetching detailed task view...")
            self._run_command(["python3", "clickup_detailed.py"])
        
        elif intent == "show_help":
            self.show_help()
        
        elif intent == "show_examples":
            self.show_examples()
        
        else:
            print("🤔 I didn't understand that. Here are some examples of what you can say:")
            self.show_examples()
    
    def _run_command(self, cmd: List[str]) -> None:
        """Run a command and display output."""
        try:
            # Activate virtual environment if it exists
            venv_activate = "source venv/bin/activate && " if os.path.exists("venv") else ""
            
            if venv_activate:
                # Run with shell and venv activation
                full_cmd = venv_activate + " ".join(cmd)
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
            else:
                # Run directly
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr and result.returncode != 0:
                print(f"Error: {result.stderr}", file=sys.stderr)
                
        except Exception as e:
            print(f"❌ Error running command: {e}")
    
    def show_help(self):
        """Show help information."""
        print("""
🤖 ClickUp Natural Language Interface

I understand natural language commands for managing your ClickUp tasks.
You can talk to me like you would to a colleague!

Categories of commands I understand:
• Viewing tasks (yours, others, due dates, priorities)
• Creating tasks
• Updating task status
• Team and workspace information
• Task summaries and statistics

Type 'examples' to see specific examples.
Type 'quit' or 'exit' to leave.
        """)
    
    def show_examples(self):
        """Show example commands."""
        print("""
📝 Example Commands:

VIEWING YOUR TASKS:
• "show my tasks"
• "what do I need to do today?"
• "list my tasks due this week"
• "show overdue tasks"
• "what am I working on?"

VIEWING OTHERS' TASKS:
• "show jeremy's tasks"
• "what is rolla working on?"
• "list tasks for sachin"
• "show me tasks assigned to john"

PRIORITIES & SUMMARIES:
• "show urgent tasks"
• "what are the high priority items?"
• "give me a task summary"
• "how many tasks do I have?"

DETAILED VIEWS:
• "show detailed tasks"
• "view tasks with comments"
• "show full task list"

TEAM INFO:
• "show teams"
• "list workspaces"
• "who am i?"

CREATING TASKS:
• "create task 'Review PR #123'"
• "add 'Fix login bug' to my list"
• "remind me to update documentation"

Note: Some commands will provide instructions for completing the action.
        """)
    
    def interactive_mode(self):
        """Run in interactive mode."""
        print("""
🤖 ClickUp Natural Language Interface
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Talk to me naturally! Say 'help' for guidance or 'quit' to exit.
        """)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Parse and execute
                intent, params = self.parse_intent(user_input)
                print(f"\n🔄 Processing: {intent.replace('_', ' ').title()}...\n")
                self.execute_intent(intent, params)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
                print("Please try again or type 'help' for assistance.")


def main():
    """Main entry point."""
    nlp = ClickUpNLP()
    
    if len(sys.argv) > 1:
        # Process command line argument as natural language
        user_input = " ".join(sys.argv[1:])
        intent, params = nlp.parse_intent(user_input)
        nlp.execute_intent(intent, params)
    else:
        # Run in interactive mode
        nlp.interactive_mode()


if __name__ == "__main__":
    main()
from google.adk.agents import Agent
from google.adk.tools import BaseTool, ToolContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import FunctionTool
from google.adk.agents import Agent
import requests
from datetime import datetime, timedelta
from typing import List, Optional
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dateutil import parser
import requests

class ExtractScheduleDetailsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="extract_schedule_details",
            description="Extracts date, time, and attendee emails from a task description."
        )

    async def run_llm(self, tool_context: ToolContext, task: str) -> Dict:
        prompt = f"""
You will be given a user task. Extract the following if present:
- date (in YYYY-MM-DD)
- time (in HH:MM 24-hr format)
- location
- attendees (only email addresses)

Respond in JSON like this:
{{
  "date": "...",
  "time": "...",
  "location": "...",
  "attendees": ["email1@example.com", "email2@example.com"]
}}

If any field is missing, set it to null or empty list.
Task: {task}
"""
        llm_request = LlmRequest(prompt=prompt.strip())
        llm_response: LlmResponse = await tool_context.llm.complete(llm_request)
        try:
            return json.loads(llm_response.text)
        except Exception:
            return {"date": None, "time": None, "location": None, "attendees": []}

# -- TOOL 1: Decompose Task --
class DecomposeTaskTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="decompose_task",
            description="Decomposes a task into subtasks and estimates XP using prompting."
        )

    async def run_llm(self, tool_context: ToolContext, task: str) -> str:
        prompt = f"""
You are an intelligent task planner that receives a user task and decides whether the task needs to be broken down into subtasks.

Respond in the following format:

---
task: {task}

If the task is simple and doesn’t need subtasks:
subtasks required: 0
note: This task is straightforward and does not require subtasking.

If the task needs to be broken down:
subtasks required: <number of subtasks>
subtask1: <subtask description> | XP: <estimated XP>
subtask2: <subtask description> | XP: <estimated XP>
...
total XP: <sum of all XP values>
---

Guidelines:
- Skip subtasks for trivial tasks like “water the plants”.
- XP should reflect effort (sum up to 100 if fully scoped).
"""
        llm_request = LlmRequest(prompt=prompt.strip())
        llm_response: LlmResponse = await tool_context.llm.complete(llm_request)
        return llm_response.text.strip()

    async def run(self, tool_context: ToolContext, task: str) -> str:
        return await self.run_llm(tool_context, task)

# -- TOOL 2: Estimate XP --
class EstimateXPTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="estimate_xp",
            description="Estimates XP score for subtasks."
        )

    async def run(self, tool_context: ToolContext, task: str, subtasks: List[str]) -> Dict:
        xp_per_subtask = {}
        for i, subtask in enumerate(subtasks):
            xp_per_subtask[subtask] = 10 + 5 * i
        total_xp = sum(xp_per_subtask.values())

        return {
            "status": "success",
            "report": {
                "task": task,
                "subtasks_required": len(subtasks),
                "subtask_details": [{"subtask": s, "xp": xp_per_subtask[s]} for s in subtasks],
                "total_xp": total_xp
            }
        }

def schedule_event(
    date: str,
    time: Optional[str] = None,
    location: str = "",
    description: str = "",
    attendees: Optional[List[Dict[str,str]]] = None
) -> str:
    event_details = {
        "summary": description,
        "location": location,
        "description": description,
        "timeZone": "Asia/Kolkata"
    }

    try:
        if time and time.lower() != "unknown":
            # Try to parse the time using dateutil for flexibility
            parsed_time = parser.parse(time)
            start_datetime = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=parsed_time.hour, minute=parsed_time.minute, second=0
            )
            end_datetime = start_datetime + timedelta(minutes=30)

            # Format to ISO strings for scheduling
            event_details["start"] = start_datetime.isoformat()
            event_details["end"] = end_datetime.isoformat()
        else:
            # # All-day event
            event_details["start"] = date
            event_details["end"] = date
            # event_details["allDay"] = True
            
    except Exception as e:
        return f"Error parsing time: {str(e)}"

    if attendees:
        event_details["attendees"] = [email for email in attendees]

    try:
        print(event_details) #http://127.0.0.1:5000/schedule
        response = requests.post("https://e04c-49-206-114-222.ngrok-free.app/schedule", json=event_details) #https://d49c-49-206-114-222.ngrok-free.app
        if response.status_code == 200:
            return f"Event scheduled: {description} on {date}"
        else:
            return f"Failed to schedule event. Server response: {response.text}"
    except Exception as e:
        return f"Error during scheduling: {str(e)}"

schedule_event_tool = FunctionTool(func=schedule_event)

# -- ROOT AGENT --
root_agent =  Agent(
        name="personaliser",
        description="Agent to gamify tasks and create calendar events.",
        model="gemini-2.0-flash",
        instruction=("""
            You are a productivity assistant that gamifies and schedules tasks.

        Your workflow:
        1. Detect the task.
        2. Gamify it using `decompose_task` and `estimate_xp`.
        3. Use `extract_schedule_details` to identify if a date/time is mentioned.
        4. If the task has:
        - a date
        - a valid description (the task itself)
        Then call `schedule_event`.

        Always summarize in this format:
        - Main Task
        - Subtasks (with XP)
        - Total XP
        - Event Details (date, time, location, attendees)

        **Important**:
        - Never show internal tool names, JSON structures, or debug logs to the user.
        - Your tone should be friendly, helpful, and focused on making the user's tasks more enjoyable and efficient.
        - If the task is trivial (e.g., “water the plants”), skip subtasks but still assign an XP score and acknowledge completion."""
        ),
        tools=[
            DecomposeTaskTool(),
            EstimateXPTool(),
            ExtractScheduleDetailsTool(),
            schedule_event_tool
        ]
    )

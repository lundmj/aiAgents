import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime

from tool_box import ToolBox

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

email_tool_box = ToolBox()
calendar_tool_box = ToolBox()

def get_creds():
    """
    Retrieves Google API credentials, refreshing or generating them if necessary.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("creds.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def get_tz_name() -> str:
    """
    Detect the system's current IANA timezone name. Fall back to 'UTC' if detection fails.
    """
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    from datetime import datetime as _dt

    try:
        sys_tz = _dt.now().astimezone().tzinfo
        name = getattr(sys_tz, "key", None) or getattr(sys_tz, "zone", None)
        if name:
            try:
                ZoneInfo(name)
                return name
            except ZoneInfoNotFoundError:
                pass
        abbr = sys_tz.tzname(None)
        COMMON_ABBREV_MAP = {
            "MST": "America/Denver",
            "MDT": "America/Denver",
            "PST": "America/Los_Angeles",
            "PDT": "America/Los_Angeles",
            "EST": "America/New_York",
            "EDT": "America/New_York",
            "CST": "America/Chicago",
            "CDT": "America/Chicago",
            "UTC": "UTC",
        }
        if abbr and abbr in COMMON_ABBREV_MAP:
            return COMMON_ABBREV_MAP[abbr]
    except Exception:
        pass
    try:
        from tzlocal import get_localzone_name
        local_name = get_localzone_name()
        try:
            ZoneInfo(local_name)
            return local_name
        except ZoneInfoNotFoundError:
            pass
    except Exception:
        pass

    return "UTC"

@calendar_tool_box.tool
def create_calendar_event(
    event_title: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    duration_minutes: int,
    description: str = ""
) -> str:
    """
    Creates a Google Calendar event.

    year, month (1-12), day (1-31), hour (0-23), minute (0-59): start time
    duration_minutes: event duration in minutes

    Returns a link to the created event.
    """
    from datetime import datetime, timedelta

    def valid_input_ranges():
        """
        Validate input ranges for month, day, hour, minute, and duration_minutes.
        Returns True if all inputs are valid, otherwise returns False.
        """
        if not (1 <= month <= 12):
            return False, "month must be in 1..12"
        if not (1 <= day <= 31):
            return False, "day must be in 1..31"
        if not (0 <= hour <= 23):
            return False, "hour must be in 0..23"
        if not (0 <= minute <= 59):
            return False, "minute must be in 0..59"
        if duration_minutes <= 0:
            return False, "duration_minutes must be positive"
        return True, ""

    # Validate input ranges
    is_valid, error_message = valid_input_ranges()
    if not is_valid:
        return f"Failure: {error_message}"

    try:
        start_dt = datetime(year, month, day, hour, minute)
    except Exception as e:
        return f"Failure: invalid date/time: {e}"

    end_dt = start_dt + timedelta(minutes=duration_minutes)

    creds = get_creds()
    service = build("calendar", "v3", credentials=creds)
    tz = get_tz_name()
    event = {
        "summary": event_title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": tz},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": tz},
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    return event.get("htmlLink")

@email_tool_box.tool
@calendar_tool_box.tool
def get_current_date(format: str = "%Y-%m-%d") -> str:
    """
    Returns the current date.
    If format is not specified, returns %Y-%m-%d.
    """
    return datetime.now().strftime(format)

@email_tool_box.tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email using SMTP.
    to: recipient email address
    subject: email subject
    body: email body text

    returns string indicating success or failure.
    """
    # confirmation helper
    def _confirm() -> bool:
        prompt = (
            "\n---\nSending to: " + to + "\nSubject: " + subject + "\n\n" + body + "\n\nSend? (y/n): "
        )
        while True:
            choice = input(prompt).strip().lower()
            if choice in {"y", "n"}:
                return choice == "y"

    if not _confirm():
        return "Failure: Email cancelled by user"

    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = os.environ.get('GMAIL_APP_USER', '')
    msg['To'] = to

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as s:
            s.starttls()
            s.login(
                os.environ.get('GMAIL_APP_USER', ''),
                os.environ.get('GMAIL_APP_PASSWORD', '')
            )
            s.send_message(msg)
        return "Success"
    except Exception as e:
        return f"Failure: {e}"

@calendar_tool_box.tool
def delete_calendar_event(event_id: str) -> str:
    """
    Deletes a Google Calendar event by its event_id.

    event_id: The unique identifier of the event to delete.

    Returns a success message or an error message if the deletion fails.
    """
    try:
        creds = get_creds()
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"Success: Event with ID {event_id} has been deleted."
    except Exception as e:
        return f"Failure: Could not delete event with ID {event_id}. Error: {e}"

@calendar_tool_box.tool
def list_events_on_date(year: int, month: int, day: int) -> list:
    """
    Lists all events happening on a specific date.

    year, month (1-12), day (1-31): The date to query events for.

    Returns a list of dictionaries with event details (e.g., summary, start, description, eventId)
    or an error message if the query fails.
    """
    try:
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        # Get the current timezone
        tz_name = get_tz_name()
        tz = ZoneInfo(tz_name)

        # Define the time range for the specified date in the local timezone
        start_time = datetime(year, month, day, tzinfo=tz)
        end_time = start_time + timedelta(days=1)

        creds = get_creds()
        service = build("calendar", "v3", credentials=creds)

        # Query events within the time range
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return [{"message": "No events found for the specified date."}]

        # Format the events into a list of dictionaries
        event_list = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            event_list.append({
                "summary": event["summary"],
                "start": start,
                "description": event.get("description", "No description provided."),
                "eventId": event["id"],
            })

        return event_list

    except Exception as e:
        return [{"error": f"Failure: Could not retrieve events. Error: {e}"}]

@calendar_tool_box.tool
def get_next_event() -> dict:
    """
    Retrieves the next upcoming event from the current time.

    Returns a dictionary with the event's details (e.g., summary, start, description, eventId)
    or an error message if no events are found or the query fails.
    """
    try:
        from datetime import datetime

        # Define the current time as the starting point
        now = datetime.utcnow().isoformat() + "Z"

        creds = get_creds()
        service = build("calendar", "v3", credentials=creds)

        # Query the next event starting from now
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=1,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return {"message": "No upcoming events found."}

        # Extract details of the next event
        event = events[0]
        start = event["start"].get("dateTime", event["start"].get("date"))
        return {
            "summary": event["summary"],
            "start": start,
            "description": event.get("description", "No description provided."),
            "eventId": event["id"],
        }

    except Exception as e:
        return {"error": f"Failure: Could not retrieve the next event. Error: {e}"}

@calendar_tool_box.tool
def update_calendar_event(
    event_id: str,
    new_title: str = None,
    new_start_time: str = None,
    new_end_time: str = None,
    new_description: str = None
) -> str:
    """
    Updates an existing Google Calendar event by its event_id.

    event_id: The unique identifier of the event to update.
    new_title: The new title for the event (optional).
    new_start_time: The new start time in RFC3339 format (optional).
    new_end_time: The new end time in RFC3339 format (optional).
    new_description: The new description for the event (optional).

    Returns a success message or an error message if the update fails.
    """
    try:
        creds = get_creds()
        service = build("calendar", "v3", credentials=creds)

        # Fetch the existing event
        event = service.events().get(calendarId="primary", eventId=event_id).execute()

        # Update the fields if new values are provided
        if new_title:
            event["summary"] = new_title
        if new_start_time:
            event["start"]["dateTime"] = new_start_time
        if new_end_time:
            event["end"]["dateTime"] = new_end_time
        if new_description:
            event["description"] = new_description

        # Update the event on the calendar
        updated_event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()

        return f"Success: Event with ID {event_id} has been updated."

    except Exception as e:
        return f"Failure: Could not update event with ID {event_id}. Error: {e}"

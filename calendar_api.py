# calendar_api.py

from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import logging
app = Flask(__name__)

@app.route("/schedule", methods=["POST"])
def schedule_event():
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

            # Then continue with your console-style auth
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"Go to this URL: {auth_url}")
            code = input("Enter the authorization code: ")
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)

    event_details = request.json

    try:
        logging.info(f"Service type: {type(service)}")

        event = {
            'summary': event_details['summary'],
            'location': event_details.get('location', ''),
            'description': event_details.get('description', ''),
            'attendees': event_details.get('attendees', []),
            'start': {
                'dateTime': event_details['start'],
                'timeZone': event_details.get('timeZone', 'Asia/Kolkata'),
            },
            'end': {
                'dateTime': event_details['end'],
                'timeZone': event_details.get('timeZone', 'Asia/Kolkata'),
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        created_event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        print(created_event)
        return jsonify({
            "status": "success",
            "event_link": created_event.get('htmlLink'),
            "message": f"Event created: {created_event.get('summary')}"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error_message": str(e)
        })


if __name__ == "__main__":
    app.run(port=5000, debug=True)
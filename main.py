import datetime
from datetime import datetime
import pickle
import os.path

import googleapiclient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


class GCalendar:
    def __init__(self):
        self.creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                self.creds = pickle.load(token)

        # if no valid credentials are available, let user login
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(self.creds, token)

        # start service
        self.service = build("calendar", "v3", credentials=self.creds)

    def get_events(self, cal_id="primary", n=5):
        """
        :param cal_id: the calendar ID, DEFAULT: 'primary'
        :param n: the number of events to get, DEFAULT: 5
        :return: None, instead print out a list of up coming events
        """
        # call Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print(f"[INFO]: Getting the {n} upcoming events...")
        events_result = (
            self.service.events()
            .list(
                calendarId=cal_id,
                timeMin=now,
                maxResults=n,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("item", [])

        if not events:
            print("No upcoming events")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(f"{start}: {event['summary']}")

    def get_calendar_list(self):
        print("[INFO]: Getting calendar lists...")
        calendars_result = self.service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])

        if not calendars:
            print("No calendar found.")
        for calendar in calendars:
            info = "primary" if calendar.get("primary") else "-------"
            print(f"{calendar['summary']}: {info} | {calendar['Id']}")

    def add_event(self, events, calendarId="primary"):
        """
        :param events: list of events, expecting each event to be in a dictionary
        :param calendarId: which calendar to add to, DEFAULT to 'primary'
        :return: error message or successful notification
        """
        # checking inputs
        if not type(events) is list:
            raise TypeError(
                "Events should be in a list (even single event), expecting each event "
                "to be in the form of a dictionary, examples can be found here"
                "https://developers.google.com/calendar/v3/reference/events"
            )
        elif len(events) == 0:
            raise ValueError("Empty event list, please double check.")

        if not type(calendarId) is str:
            raise TypeError("Expected calendarId to be a string object.")

        for event in events:
            event_result = (
                self.service.events()
                .insert(calendarId=calendarId, body=event)
                .execute()
            )
            print(f"[INFO]: Event created")
            print(f"ID: {event_result['id']} | HTML: {event_result.get('htmlLink')}")

    def update_event(self, events, calendarId, Id):
        """
        :param events: list of events, expecting each event to be in a dictionary
        :param calendarId: which calendar to add to, DEFAULT to 'primary'
        :param Id: id of the event to be updated
        :return: error message or successful notification
        """
        # checking inputs
        if not type(events) is list:
            raise TypeError(
                "Events should be in a list (even single event), expecting each event "
                "to be in the form of a dictionary, examples can be found here"
                "https://developers.google.com/calendar/v3/reference/events/insert#python"
            )
        elif len(events) == 0:
            raise ValueError("Empty event list, please double check.")

        if not type(calendarId) is str:
            raise TypeError("Expected calendarId to be a string object.")

        if not type(Id) is str:
            raise TypeError("Expected Id to be a string object.")

        for event in events:
            event_result = (
                self.service.events()
                .update(calendarId=calendarId, eventId=Id, body=event)
                .execute()
            )
            print(f"[INFO]: Event created")
            print(f"ID: {event_result['id']} | HTML: {event_result.get('htmlLink')}")

    def delete_events(self, Ids, calendarId="primary"):
        """
        :param Ids: list of ids, expecting each id to be in a string
        :param calendarId: which calendar to add to, DEFAULT to 'primary'
        :return: error message or successful notification
        """
        # checking inputs
        if not type(Ids) is list:
            raise TypeError(
                "Events should be in a list (even single event), expecting each event "
                "to be in the form of a dictionary, examples can be found here"
                "https://developers.google.com/calendar/v3/reference/events"
            )
        elif len(Ids) == 0:
            raise ValueError("Empty event list, please double check.")

        if not type(calendarId) is str:
            raise TypeError("Expected calendarId to be a string object.")

        for Id in Ids:
            if not type(Id) is str:
                raise TypeError("Expect IDs inside ID list to be a string object.")
            try:
                self.service.events().delete(
                    calendarId=calendarId, eventId=Id
                ).execute()
                print(f"Event {Id} was successfully deleted from {calendarId}.")
            except googleapiclient.errors.HttpError:
                raise ValueError("Event ID not found in calendar")


def mds_to_events(path, date_time):
    md_list = [
        i
        for i in os.listdir(path)
        if os.path.isfile(os.path.join(path, i)) and i[-3:] == ".md"
    ]
    md_list.sort(key=lambda x: x[:6])
    day1 = md_list.pop(0)
    day2 = md_list.pop(10)
    first_half = md_list[-7:]
    second_half = md_list[:-7]
    md_list = first_half + second_half
    md_list.insert(0, day2)
    md_list.insert(0, day1)

    event_list = []
    for x, i in enumerate(md_list):
        start_time, end_time = increment_day(date_time, x - 1)

        with open(f"{path}/{i}", "r") as f:
            lines = f.readlines()
            urls = []
            for line in lines:
                line = line.replace("\n", "")
                if line.startswith("# "):
                    summary = line[2:]
                if line.startswith("["):
                    file_url = line[line.index("[") + 1 : line.index("]")]
                    urls.append(file_url)
            if len(urls) == 0:
                urls = "Rest Day"
            else:
                urls = "\n\n".join(urls)
            event_list.append(
                {
                    "summary": summary,
                    "description": urls,
                    "start": {"dateTime": start_time, "timeZone": "Asia/Tokyo"},
                    "end": {"dateTime": end_time, "timeZone": "Asia/Tokyo"},
                    "recurrence": ["RRULE:FREQ=MONTHLY;COUNT=1"],
                }
            )

    return event_list


def increment_day(date_time, x):
    day = str(int(date_time[8:10]) + x)
    if int(day) > 31:
        day = "01"
    start_time = date_time[:8] + day + date_time[10:]
    end_time = start_time.split(":")
    end_time[1] = str(int(end_time[1]) + 30)
    return start_time, ":".join(end_time)


if __name__ == "__main__":
    root_path = os.path.join(
        "notion_calendar", "Workout Calendar 897ed488b6f94fa4bd29eddee342dd9a"
    )
    START_DATE_TIME = "2020-10-05T09:00:00-09:00"
    workoutCal = "5oph0fsegcb9ljpctpu38irsbo@group.calendar.google.com"
    cal = GCalendar()
    events = mds_to_events(root_path, START_DATE_TIME)
    cal.add_event(events=events, calendarId=workoutCal)

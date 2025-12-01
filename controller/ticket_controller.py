from datetime import datetime, timezone
import requests
import os
import dotenv
from utils.time_util import parse_time,format_duration
dotenv.load_dotenv()
class Ticket:
    def __init__(self,access_token):
          self.access_token = access_token

    def get_ticket_based_on_id(self,ticket_id):
        try:
            header = {
                "Authorization": f"Zoho-oauthtoken {self.access_token}",
                "orgId": os.getenv("ORG_ID")
            }
            response = requests.get(f"https://desk.zoho.com/api/v1/tickets/search?limit=1&ticketNumber={ticket_id}",
                                   headers=header)
            data = response.json()
            print(data)
            if not data:
                return None
            ticket = data.get("data")[0]
            ticket_login =  ticket.get("customFields", {}).get("Ticket Login", "")
            if ticket_login == 'Approved':
                ticket_login_date = ticket.get("customFields").get("Ticket Login Date")
            else:
                ticket_login_date = ticket.get("customFields").get("Rejected SH")
            result = {
                "ticket_id": ticket.get("id", ""),
                "account_name": ticket.get("contact", {}).get("account", {}).get("accountName", ""),
                "account_owner": f"{ticket.get('assignee', {}).get('firstName', '')} "
                                 f"{ticket.get('assignee', {}).get('lastName', '')}".strip(),
                "ticket_login": ticket.get("customFields", {}).get("Ticket Login", ""),
                "ticket_login_date": ticket_login_date,
                "created_date": ticket.get("createdTime")
            }

            return {
                "id": ticket.get("id"),
                "createdTime": ticket.get("createdTime"),
                "ticket_login_status":ticket_login,
                "ticket_login_date":ticket_login_date
            },result
        except Exception as e:
            print("error raised while getting ticket based on_id",e)

    def get_ticket_history(self,ticket_dict):
        try:
            header = {
                "Authorization": f"Zoho-oauthtoken {self.access_token}",
                "orgId": os.getenv("ORG_ID")
            }
            result = []
            offset = 0
            while True:
                response = requests.get(f"https://desk.zoho.com/api/v1/tickets/{ticket_dict.get('id')}/History?from={offset}&limit={50}",
                                       headers=header)
                print(response.status_code)
                if response.status_code == 204:
                    break
                history = response.json()
                for event in history.get("data", []):
                    if event.get("eventName") == "TicketUpdated":

                        # Check eventInfo section (main property transitions)
                        for info in event.get("eventInfo", []):
                            prop_name = str(info.get("propertyName", "")).lower()

                            # Match any fields relating to Status
                            if "status" in prop_name or prop_name in ["case status"]:
                                property_value = info.get("propertyValue", {})
                                result.append({
                                    "eventTime": event.get("eventTime"),
                                    "actor": event.get("actor"),
                                    "propertyName": info.get("propertyName"),
                                    "previousValue": property_value.get("previousValue"),
                                    "updatedValue": property_value.get("updatedValue"),
                                })
                offset+=50
            print(result)
            return ticket_dict['createdTime'],result
        except Exception as e:
            print("error raised while getting ticket history based",e)

    def transform_data_for_frontend(self,logs,creation_time_str):

        # 1. Inject Creation Event
        creation_event = {'eventTime': creation_time_str, 'propertyName': 'Case Status',
                          'updatedValue': 'Yet to Lender Login'}
        status_logs = [l for l in logs if l.get('propertyName') == 'Case Status']
        status_logs.append(creation_event)

        # 2. Filter and Sort
        status_logs.sort(key=lambda x: x['eventTime'])

        gantt_data = []

        # 3. Calculate Intervals (Loop runs until the second-to-last log)
        for i in range(len(status_logs) - 1):
            current_event = status_logs[i]
            next_event = status_logs[i + 1]

            t1 = parse_time(current_event['eventTime'])
            t2 = parse_time(next_event['eventTime'])
            duration_seconds = (t2 - t1).total_seconds()

            gantt_data.append({
                "id": i + 1,
                "status": current_event['updatedValue'],
                "start_time": current_event['eventTime'],
                "end_time": next_event['eventTime'],
                "duration_human": format_duration(duration_seconds)
            })

        # 4. Handle Ongoing Status
        final_event = status_logs[-1]
        final_start_time = parse_time(final_event['eventTime'])
        now_utc = datetime.now(timezone.utc)
        final_duration_seconds = (now_utc - final_start_time).total_seconds()

        gantt_data.append({
            "id": len(status_logs),
            "status": final_event['updatedValue'],
            "start_time": final_event['eventTime'],
            "end_time": None,  # Null end time signals an ongoing status
            "duration_human": format_duration(final_duration_seconds) + " (Ongoing)"
        })
        print(gantt_data)
        # Convert the Python list to a JSON string for the frontend
        return gantt_data


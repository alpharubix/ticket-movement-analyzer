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
            if not data:
                return None, None

            ticket = data.get("data")[0]
            print(ticket)

            # FIX 2: Handle 'assignee' being explicitly None
            # (ticket.get('assignee') or {}) ensures we have a dict even if the value is None
            assignee = ticket.get('assignee') or {}
            first_name = assignee.get('firstName', '')
            last_name = assignee.get('lastName', '')

            ticket_login = ticket.get("customFields", {}).get("Ticket Login", "")

            if ticket_login == 'Approved':
                ticket_login_date = ticket.get("customFields").get("Ticket Login Date")
            else:
                ticket_login_date = ticket.get("customFields").get("Rejected SH")

            result = {
                "ticket_id": ticket.get("id", ""),
                "account_name": ticket.get("contact", {}).get("account", {}).get("accountName", ""),
                "account_owner": f"{first_name} {last_name}".strip(),  # Use the safe variables
                "ticket_login": ticket_login,
                "ticket_login_date": ticket_login_date,
                "created_date": ticket.get("createdTime")
            }

            return {
                "id": ticket.get("id"),
                "createdTime": ticket.get("createdTime"),
                "ticket_login_status": ticket_login,
                "ticket_login_date": ticket_login_date
                # "ticket_owner":
            }, result

        except Exception as e:
            print("error raised while getting ticket based on_id", e)
        # FIX 3: Return two values (or raise HTTPException) to prevent 'cannot unpack' error
        return None, None

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

    def parse_time(self,ts: str) -> datetime:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def transform_data_for_frontend(self, logs, creation_time_str):
        # 1. Inject creation event
        creation_event = {
            "eventTime": creation_time_str,
            "propertyName": "Case Status",
            "updatedValue": "Yet to Lender Login"
        }

        status_logs = [
            l for l in logs if l.get("propertyName") == "Case Status"
        ]
        status_logs.append(creation_event)

        # 2. Sort chronologically
        status_logs.sort(key=lambda x: x["eventTime"])

        status_totals = {}  # status → total seconds
        status_occurrences = []  # per occurrence
        total_seconds = 0

        # 3. Handle completed transitions
        for i in range(len(status_logs) - 1):
            curr = status_logs[i]
            nxt = status_logs[i + 1]

            status = curr["updatedValue"]

            t1 = self.parse_time(curr["eventTime"])
            t2 = self.parse_time(nxt["eventTime"])

            seconds = (t2 - t1).total_seconds()
            hours = round(seconds / 3600, 2)

            status_occurrences.append({
                "status": status,
                "start_time": curr["eventTime"],
                "end_time": nxt["eventTime"],
                "duration_hours": hours
            })

            status_totals[status] = status_totals.get(status, 0) + seconds
            total_seconds += seconds

        # 4. 🔥 Handle ONGOING (last) status
        final_event = status_logs[-1]
        final_status = final_event["updatedValue"]

        final_start_time = self.parse_time(final_event["eventTime"])
        now_utc = datetime.now(timezone.utc)

        ongoing_seconds = (now_utc - final_start_time).total_seconds()
        ongoing_hours = round(ongoing_seconds / 3600, 2)

        # per-occurrence (no end_time)
        status_occurrences.append({
            "status": final_status,
            "start_time": final_event["eventTime"],
            "end_time": None,
            "duration_hours": ongoing_hours
        })

        # per-status total
        status_totals[final_status] = status_totals.get(final_status, 0) + ongoing_seconds
        total_seconds += ongoing_seconds

        # 5. Build total summary in DAYS
        status_totals_days = [
            {
                "status": status,
                "total_days": f"{int(seconds // 86400)}D{int((seconds % 86400) // 3600)}hrs"
            }
            for status, seconds in status_totals.items()
        ]

        return {
            "total_duration_days": f"{int(total_seconds // 86400)}D{int((total_seconds % 86400) // 3600)}hrs",
            "status_totals": status_totals_days,
            "status_occurrences": status_occurrences
        }

    # def transform_data_for_frontend(self, logs, creation_time_str):
    #         print("The logs",logs)
    #
    #         # 1. Inject Creation Event
    #         creation_event = {
    #             'eventTime': creation_time_str,
    #             'propertyName': 'Case Status',
    #             'updatedValue': 'Yet to Lender Login'
    #         }
    #
    #         status_logs = [l for l in logs if l.get('propertyName') == 'Case Status']
    #         status_logs.append(creation_event)
    #
    #         # 2. Sort by time
    #         status_logs.sort(key=lambda x: x['eventTime'])
    #
    #         status_duration = {}  # seconds
    #         status_start = {}
    #         status_end = {}
    #
    #         # 3. Calculate durations between consecutive events
    #         for i in range(len(status_logs) - 1):
    #             current_event = status_logs[i]
    #             next_event = status_logs[i + 1]
    #
    #             status = current_event['updatedValue']
    #
    #             t1 = parse_time(current_event['eventTime'])
    #             t2 = parse_time(next_event['eventTime'])
    #             duration_seconds = (t2 - t1).total_seconds()
    #
    #             status_duration[status] = status_duration.get(status, 0) + duration_seconds
    #
    #             if status not in status_start:
    #                 status_start[status] = current_event['eventTime']
    #
    #             status_end[status] = next_event['eventTime']
    #
    #         # 4. Handle ongoing status
    #         final_event = status_logs[-1]
    #         final_status = final_event['updatedValue']
    #         final_start_time = parse_time(final_event['eventTime'])
    #
    #         now_utc = datetime.now(timezone.utc)
    #         ongoing_seconds = (now_utc - final_start_time).total_seconds()
    #
    #         status_duration[final_status] = status_duration.get(final_status, 0) + ongoing_seconds
    #
    #         if final_status not in status_start:
    #             status_start[final_status] = final_event['eventTime']
    #
    #         status_end[final_status] = None
    #
    #         # 5. Build frontend response
    #         gantt_data = []
    #         for idx, status in enumerate(status_duration, start=1):
    #             total_seconds = status_duration[status]
    #             total_days = int(round(total_seconds / 86400, 2))
    #
    #             gantt_data.append({
    #                 "id": idx,
    #                 "status": status,
    #                 "start_time": status_start[status],
    #                 "end_time": status_end[status],
    #                 "duration_human": (
    #                         format_duration(total_seconds) +
    #                         (" (Ongoing)" if status_end[status] is None else "")
    #                 ),
    #                 "total_duration_days": total_days
    #             })
    #         return gantt_data




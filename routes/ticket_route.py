from fastapi import APIRouter
from starlette.responses import JSONResponse
from auth_token.zoho_desk_token import get_access_token
from controller.ticket_controller import Ticket

ticket_router = APIRouter()

@ticket_router.get("/get-ticket-status")
async def get_ticket_status(ticket_id:int):
     # access_token = get_access_token()
     ticket = Ticket(access_token="1000.3137bf2d7c60043af20b0df87b6fb8e5.50505499ca2cf9a639d3bddf8669e617")
     id_dict,result = ticket_info = ticket.get_ticket_based_on_id(ticket_id)
     created_time,history = ticket.get_ticket_history(ticket_dict=id_dict)
     data = ticket.transform_data_for_frontend(history,created_time)
     return JSONResponse(status_code=200,content={"ticket_info":result,"data_status_analysis":data})
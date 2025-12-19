import fastapi
from fastapi import APIRouter
from starlette.responses import JSONResponse
from auth_token.zoho_desk_token import get_access_token,token_validator
from controller.ticket_controller import Ticket

ticket_router = APIRouter()


@ticket_router.get("/get-ticket-status")
async def get_ticket_status(ticket_id:int):
     token = await token_validator()
     ticket = Ticket(access_token=token)
     id_dict,result = ticket.get_ticket_based_on_id(ticket_id)
     if id_dict is None:
          return fastapi.HTTPException(status_code=404, detail="No much information found for this ticket try different ticket")
     created_time,history = ticket.get_ticket_history(ticket_dict=id_dict)
     data = ticket.transform_data_for_frontend(history,created_time)
     return JSONResponse(status_code=200,content={"ticket_info":result,"data_status_analysis":data})
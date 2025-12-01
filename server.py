from fastapi import FastAPI
from uvicorn.main import run
from routes.ticket_route import ticket_router



app = FastAPI()
app.include_router(ticket_router)


if __name__ == "__main__":
    run("server:app", host="127.0.0.1", port=8000)
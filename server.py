
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.db_config import get_mongo_client
from uvicorn.main import run
from routes.ticket_route import ticket_router



@asynccontextmanager
async def lifespan(app: FastAPI):
      get_mongo_client()
      yield
      get_mongo_client().close()

app = FastAPI(lifespan=lifespan)
app.include_router(ticket_router)

if __name__ == "__main__":
    run("server:app", host="127.0.0.1", port=3500)
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from database.db_config import get_mongo_client
from uvicorn.main import run
from routes.ticket_route import ticket_router
from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app: FastAPI):
      get_mongo_client()
      yield
      get_mongo_client().close()

app = FastAPI(lifespan=lifespan)
@app.get('/')
def health_check():
    return {'message': 'server is up and running'}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.include_router(ticket_router)
app.add_middleware(CORSMiddleware,allow_origins=["*"])
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
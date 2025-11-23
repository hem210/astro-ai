from fastapi import FastAPI
from app.routes import kundali, matchmaking

app = FastAPI()
app.include_router(kundali.router)
app.include_router(matchmaking.router)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

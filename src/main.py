import uvicorn
import os
import pandas as pd
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from routers import test
from model import learniverse_model

app = FastAPI()
app.include_router(test.router)

#CORS - Nginx에서 처리
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,  
#     allow_methods=["*"],  
#     allow_headers=["*"],  
# )

@app.get("/")
def root():
    return {"message": "Hello, Learni AI!!"}

@app.get("/recommendRoom")
def main_rec(memberId : int):
    room_id_list = learniverse_model(memberId)
    return {"status":200, "success": "OK", "data":room_id_list[:5]}



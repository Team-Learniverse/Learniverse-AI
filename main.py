import uvicorn
import os
import pandas as pd
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
import user_based, content_based, read_data

app = FastAPI()

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/")
def root():
    return {"message": "Hello, Learni AI!!"}

@app.get("/recommendRoomTest")
def get_rec_room_test():
    member_room_list = user_based.get_member_room_list()
    recommend_list = content_based.get_rec_room_list(member_room_list[0], 5)
    print(recommend_list)
    

@app.get("/recommendRoom")
def get_rec_room(memberId:int):
    member_room_list = user_based.get_member_room_list()
    recommend_list = content_based.get_rec_room_list(member_room_list[0], 5)
    room_id_list = recommend_list['roomId'].to_list()
    return {"status":200, "success": "OK", "data":room_id_list}
@app.get("/datatest")
def get_room():
    df = read_data.get_data('rooms')
    print(df.head())


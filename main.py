import uvicorn
import os
import pandas as pd
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
import user_based, content_based, read_data, model

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

@app.get("/defult")
def test_def(memberId:int):
    recommend_list = model.default_room_based(memberId)
    print(model.check_room_info(recommend_list))
    #return recommend_list

@app.get("/member/lang")
def test_member_lang(memberId:int):
    recommend_list = user_based.get_lang_member_list(memberId)
    print(recommend_list)

@app.get("/room/lang")
def test_member_lang(memberId:int):
    recommend_list = content_based.get_rec_room_list_based_lang(memberId, 30)
    print(recommend_list)




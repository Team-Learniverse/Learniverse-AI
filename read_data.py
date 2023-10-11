import os
import pymongo
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# MongoDB 연결 정보 설정
client = pymongo.MongoClient(os.environ["MONGODB_URL"])  # MongoDB 서버 주소 및 포트

# MongoDB 데이터베이스 선택
db = client[os.environ["MONGODB_DB"]]

def get_data(coll_name):
    collection = db[coll_name]
    data = list(collection.find({}))
    if(len(data) == 0): return None
    df = pd.DataFrame(data)
    df.drop('_id', axis = 1, inplace = True)
    return df

def get_data_find_member(coll_name, memberId):
    collection = db[coll_name]
    query = {"memberId":memberId}
    data = list(collection.find(query))
    if(len(data) == 0): return None
    df = pd.DataFrame(data)
    df.drop('_id', axis = 1, inplace = True)
    return df

def cnt_member_join_room(member_id):
    collection = db['joins']

    query = {"memberId": member_id} 
    return collection.count_documents(query)







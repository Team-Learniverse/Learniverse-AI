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
    df = pd.DataFrame(data)
    df.drop('_id', axis = 1, inplace = True)
    return df








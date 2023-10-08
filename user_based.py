import numpy as np
import scipy as sp
from sklearn.metrics.pairwise import cosine_similarity
import os
import pandas as pd
import read_data


def join_list (joins, rooms) :
  rooms.drop('roomIntro', axis = 1, inplace = True)
  rooms.drop('roomHashtags', axis = 1, inplace = True)
  rooms.drop('roomCategory', axis = 1, inplace = True)
  rooms.drop('roomLanguages', axis = 1, inplace = True)
  rooms.drop('roomName', axis = 1, inplace = True)
  rooms['isJoin'] = 1.0

  join_rooms = pd.merge(joins, rooms, on = "roomId")
  join_rooms.to_csv('join_rooms.csv', index = False, header = False)

  return join_rooms


def member_recommend_list(join_rooms, target_id):
  piv = join_rooms.pivot(index='memberId', columns = 'roomId', values='isJoin').fillna(0.0)
  piv_norm = piv.apply(lambda x: (x-np.mean(x))/(np.max(x)-np.min(x)), axis = 1)

  piv_sparse = sp.sparse.csr_matrix(piv_norm.values)
  user_similarity = cosine_similarity(piv_sparse)
  user_sim_df = pd.DataFrame(user_similarity, index = piv_norm.index, columns = piv_norm.index)

  target = user_sim_df.loc[target_id]
  target = target.drop(target_id)
  target = target.sort_values(ascending=False)

  return target.index.tolist()

def find_member_rooms(joins, target_id):
  target = joins[joins['memberId'] == target_id]

  return target['roomId'].tolist()

def get_member_room_list() :  
  joins = read_data.get_data('joins')
  rooms = read_data.get_data('rooms')
  join_rooms = join_list(joins, rooms)

  recommend_members = member_recommend_list(join_rooms, 1)

  return find_member_rooms(joins, recommend_members[0])

#깃허브 언어 기준으로 유사 사용자 가져오기 
def get_lang_member_list(target_id):
  member_git_lang = read_data.get_data('memberGitLang')

  piv = member_git_lang.pivot(index="memberId", columns = 'language', values='bytes').fillna(0)
  piv_norm = piv.apply(lambda x: (x-np.mean(x))/(np.max(x)-np.min(x)), axis = 1)

  piv_sparse = sp.sparse.csr_matrix(piv_norm.values)
  user_similarity = cosine_similarity(piv_sparse)
  user_sim_df = pd.DataFrame(user_similarity, index = piv_norm.index, columns = piv_norm.index)

  print(user_sim_df)

  target = user_sim_df.loc[target_id]
  target = target.drop(target_id)
  target = target.sort_values(ascending=False)

  return target.index.tolist()


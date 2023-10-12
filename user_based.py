import numpy as np
import scipy as sp
from sklearn.metrics.pairwise import cosine_similarity
import os
import pandas as pd
import read_data
from content_based import cul_date

def join_list (joins, rooms) :
  rooms.drop('roomIntro')
  rooms.drop('roomHashtags', axis = 1, inplace = True)
  rooms.drop('roomCategory', axis = 1, inplace = True)
  rooms.drop('roomLanguages', axis = 1, inplace = True)
  rooms.drop('roomName', axis = 1, inplace = True)
  rooms['isJoin'] = 1.0

  join_rooms = pd.merge(joins, rooms, on = "roomId")
  join_rooms.to_csv('join_rooms.csv', index = False, header = False)

  return join_rooms

# 참여한 방 가입 여부에 따른 유사도 
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

# enterRoom 기준에 따른 유사도
def member_rec_list_based_enter(member_id):
  check = read_data.get_data_find_member('joins', member_id)
  if(check is None): return None 
  check = check[check['isDefault'] != True]
  if(check.shape[0] == 0): return None

  joins = read_data.get_data('joins')
  joins = joins = joins[joins['isDefault'] == False]
  #관심있는 방 제거 
  joins.drop('isDefault', axis = 1, inplace = True)
  joins.drop('createdDate', axis = 1, inplace = True)
  if 'pinDate' in joins.columns:
    joins.drop('pinDate', axis = 1, inplace = True)
  
  piv = joins.pivot(index='memberId', columns = 'roomId', values='enterRoom').fillna(-1.0)
  piv_norm = piv.apply(lambda x: (x-np.mean(x))/(np.max(x)-np.min(x)), axis = 1)
  piv_sparse = sp.sparse.csr_matrix(piv_norm.values)
  
  user_similarity = cosine_similarity(piv_sparse)
  user_sim_df = pd.DataFrame(user_similarity, index = piv_norm.index, columns = piv_norm.index)

  target = user_sim_df.loc[member_id]
  target = target.drop(member_id)
  target = target.sort_values(ascending=False)

  return target.index.tolist()

def find_member_rooms(target_id):
  joins = read_data.get_data('joins')
  target = joins[joins['memberId'] == target_id]
  target = target[target['isDefault'] == False] 

  return target['roomId'].tolist()


#깃허브 언어 기준으로 유사 사용자 가져오기 
def get_lang_member_list(target_id):
  check_git_lang = read_data.get_data_find_member('memberGitLang', target_id)
  if(check_git_lang is None): return None 
  member_git_lang = read_data.get_data('memberGitLang')

  piv = member_git_lang.pivot(index="memberId", columns = 'language', values='bytes').fillna(0)
  piv_norm = piv.apply(lambda x: (x-np.mean(x))/(np.max(x)-np.min(x)), axis = 1)

  piv_sparse = sp.sparse.csr_matrix(piv_norm.values)
  user_similarity = cosine_similarity(piv_sparse)
  user_sim_df = pd.DataFrame(user_similarity, index = piv_norm.index, columns = piv_norm.index)

  #date
  target = user_sim_df.loc[target_id]
  target = target.drop(target_id)
  #print(target) : date 적용 전후 비교를 위한 print 문

  members = read_data.get_data('members')
  for idx, score in target.items():
    member_id = idx
    this_data = members[members['memberId']==member_id].iloc[0]
    this_date = this_data['lastLoginDate']
    diff_date = cul_date(this_date)
    final_score = float(score) * 0.4 + (1-diff_date*0.03) * 0.6
    target[idx] = final_score

  #print(target)
  target = target.sort_values(ascending=False)
  return target.index.tolist()


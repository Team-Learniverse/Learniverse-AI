import pandas as pd
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import read_data
from datetime import datetime

#text 정렬
def data_sort(str):
  strings = str.split()
  strings = sorted(strings)
  lang_str = ""
  for string in strings:
    lang_str += string+" "
  return lang_str

#자카드 유사도를 위한 집합 
def str_to_set(x):
  language_set = set()
  strings = x.split()
  for string in strings:
    language_set.add(string)
  return language_set

#날짜 차이 계산
def cul_date(str_datetime):
  date = str_datetime.split()
  date_format = "%Y-%m-%d" 
  comp_date = datetime.strptime(date[0], date_format)
  current_date = datetime.now()
  date_difference = current_date - comp_date
  return date_difference.days

#자카드 유사도 계산
def jaccard_similarity(s1, s2):
  # 분모가 0이면 계산할 수 없기 때문에 s1s2 합집합의 크기가 0인 경우 return 0
  if len(s1|s2) == 0:
    return 0
  # 아닌 경우 교집합/합집합 반환
  return len(s1&s2)/len(s1|s2)

#특정 방과 유사한 방 리스트 
def get_rec_room_list(target_row, top):
  rooms = read_data.get_data('rooms')
  rooms = rooms.fillna(" ")
  rooms = pd.concat([rooms, target_row], ignore_index=True)

  #집합
  rooms['roomLanguages'] = rooms['roomLanguages'].apply(str_to_set)
  rooms['roomHashtagsSet'] = rooms['roomHashtags'].apply(str_to_set)

  #정렬 
  rooms["roomHashtags"] = rooms.apply(lambda x: data_sort(x["roomHashtags"]), axis=1)

  #result = recommend_list(rooms, 0, top)
  #result_df = pd.DataFrame(result, columns = ['roomId','finalScore'])
  return recommend_list(rooms, 0, top)

  #merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
  #return merged_df.sort_values(by='finalScore', ascending=False)

#사용자 개발 언어 가져오기 
def get_member_git_lang(memberId):
  languages = ""
  member_git_lang = read_data.get_data_find_member('memberGitLang', memberId)
  for lang in member_git_lang['language']:
    languages += lang +" "
  return languages

#개발언어 리스트로 유사한 방 리스트 찾기
def get_rec_room_list_based_lang(memberId, top):
  rooms = read_data.get_data('rooms')
  rooms = rooms.fillna(" ")

  rooms['roomLanguages'] = rooms['roomLanguages'].apply(str_to_set)
  
  languages = get_member_git_lang(memberId)
  lang_set = str_to_set(languages)
  lang_result = []
  date_result = []
  #점수 계산
  for this_id in rooms['roomId']:
    this_data = rooms.loc[rooms['roomId'] == this_id].iloc[ 0]
    this_lang_set = this_data['roomLanguages']
    this_date = this_data['createdDate']

    sim_lang = jaccard_similarity(this_lang_set, lang_set)

    lang_result.append((this_id, sim_lang))
    date_result.append(cul_date(this_date))

  #결과 
  room_ids = []
  final_scores = []
  for room_id in rooms['roomId']:
    idx = rooms[rooms['roomId'] == room_id].index[0]
    
    sim_lang = lang_result[idx][1]
    diff_date = date_result[idx]

    final_score = float(sim_lang) * 0.5 + (1-diff_date*0.03) * 0.5
    room_ids.append(room_id)
    final_scores.append(final_score)

  data = {'roomId':room_ids, 'finalScore':final_scores}
  result = pd.DataFrame(data)
  result = result.sort_values(by='finalScore', ascending=False)
  return result[:top]

#히스토리 얻기
def get_history(memberId):
  ret = ""
  data = read_data.get_data_find_member('searchHistory', memberId)
  for str in data['search']:
    ret += str +" "
  return ret

#검색 기록 기반(해시태그) 유사한 방 리스트 찾기
def get_rec_room_list_based_history(member_id, top):
  #데이터 처리 
  rooms = read_data.get_data('rooms')
  rooms = rooms.fillna(" ")
  search_history = get_history(member_id)
  data = pd.DataFrame({'roomId': [0], 'roomHashtags': [search_history]})
  rooms = pd.concat([rooms, data], ignore_index=True)

  counter_vector = CountVectorizer(ngram_range=(1,3))
  # 코사인 - 해시태그
  target_idx = rooms[rooms['roomId'] == 0].index[0]
  c_vector_hash = counter_vector.fit_transform(rooms['roomHashtags'])
  similarity_hash = cosine_similarity(c_vector_hash, c_vector_hash)
  hash_result = list(enumerate(similarity_hash[target_idx]))


  #점수 계산
  for this_id in rooms['roomId']:
    this_data = rooms.loc[rooms['roomId'] == this_id].iloc[0]

  #결과 
  room_ids = []
  final_scores = []
  for room_id in rooms['roomId']:
    idx = rooms[rooms['roomId'] == room_id].index[0]
    if(idx == target_idx): continue
    
    sim_hash = hash_result[idx][1]

    final_score = float(sim_hash) * 0.5
    room_ids.append(room_id)
    final_scores.append(final_score)


  data = {'roomId':room_ids, 'finalScore':final_scores}
  result = pd.DataFrame(data)
  result = result.sort_values(by='finalScore', ascending=False)
  return result[:top]
  

#특정 방과 유사한 방 점 수 계산
def recommend_list(data, target_id, top):
  target = data.loc[data['roomId'] == target_id].iloc[0]
  lang_set = target['roomLanguages']
  hash_set = target['roomHashtagsSet']

  lang_result = []
  hash_result = []
  hash_jaccard_result = []
  category_result = []
  name_result = []
  intro_result = []

  # 자카드 - 개발언어, 해시태그 / 카테고리
  for this_id in data['roomId']:
    this_data = data.loc[data['roomId'] == this_id].iloc[ 0]
    this_lang_set = this_data['roomLanguages']
    this_hash_set = this_data['roomHashtagsSet']

    sim_lang = jaccard_similarity(this_lang_set, lang_set)
    sim_hash = jaccard_similarity(this_hash_set, hash_set)
    sim_category = this_data['roomCategory'] == target['roomCategory']

    lang_result.append((this_id, sim_lang))
    hash_jaccard_result.append((this_id, sim_hash))
    category_result.append((this_id, sim_category))

  target_idx = data[data['roomId'] == target_id].index[0]
  # 코사인 - 해시태그
  counter_vector = CountVectorizer(ngram_range=(1,3))
  c_vector_hash = counter_vector.fit_transform(data['roomHashtags'])
  similarity_hash = cosine_similarity(c_vector_hash, c_vector_hash)
  hash_result = list(enumerate(similarity_hash[target_idx]))
  # 코사인 - 방이름
  c_vector_name = counter_vector.fit_transform(data['roomName'])
  similarity_name = cosine_similarity(c_vector_name, c_vector_name)
  name_result = list(enumerate(similarity_name[target_idx]))
  # 코사인 - 방소개
  c_vector_intro = counter_vector.fit_transform(data['roomIntro'])
  similarity_intro = cosine_similarity(c_vector_intro, c_vector_intro)
  intro_result = list(enumerate(similarity_intro[target_idx]))

  room_ids = []
  final_scores = []
  #결과 합산
  for room_id in data['roomId']:
    if room_id==target_id : continue
    idx = data[data['roomId'] == room_id].index[0]
    
    sim_lang = lang_result[idx][1]
    sim_jaccard_hash = hash_jaccard_result[idx][1]
    sim_category = category_result[idx][1]

    sim_hash = hash_result[idx][1]
    sim_name = name_result[idx][1]
    sim_intro = intro_result[idx][1]

    #print(room_id, idx, sim_hash," ",sim_name," ",sim_intro)

    # 가중 평균을 계산하고 최종 결과 리스트에 추가
    final_score = 0.4 * float(sim_lang) + 0.1 * float(sim_name) + 0.05 * float(sim_intro)
    final_score +=  0.15 * float(sim_hash) + 0.15 * float(sim_jaccard_hash)
    if(sim_category):
      final_score+=0.2

    room_ids.append(room_id)
    final_scores.append(final_score)

  data = {'roomId':room_ids, 'finalScore':final_scores}
  result = pd.DataFrame(data)
  result = result.sort_values(by='finalScore', ascending=False)
  return result[:top]

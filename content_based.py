import pandas as pd
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import read_data

def str_to_set(x):
  language_set = set()
  strings = x.split()
  for string in strings:
    language_set.add(string)
  return language_set

def data_sort(languages):
  strings = languages.split()
  strings = sorted(strings)
  lang_str = ""
  for string in strings:
    lang_str += string+" "
  return lang_str

def jaccard_similarity(s1, s2):
  # 분모가 0이면 계산할 수 없기 때문에 s1s2 합집합의 크기가 0인 경우 return 0
  if len(s1|s2) == 0:
    return 0
  # 아닌 경우 교집합/합집합 반환
  return len(s1&s2)/len(s1|s2)

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

  j_result = []
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


  # 코사인 - 해시태그
  counter_vector = CountVectorizer(ngram_range=(1,3))
  c_vector_hash = counter_vector.fit_transform(data['roomHashtags'])
  similarity_hash = cosine_similarity(c_vector_hash, c_vector_hash)
  hash_result = list(enumerate(similarity_hash[target_id]))
  # 코사인 - 방이름
  c_vector_name = counter_vector.fit_transform(data['roomName'])
  similarity_name = cosine_similarity(c_vector_name, c_vector_name)
  name_result = list(enumerate(similarity_name[target_id]))
  # 코사인 - 방소개
  c_vector_intro = counter_vector.fit_transform(data['roomIntro'])
  similarity_intro = cosine_similarity(c_vector_intro, c_vector_intro)
  intro_result = list(enumerate(similarity_intro[target_id]))



  result = []
  #결과 합산
  for room_id in range(len(data)):
    if room_id==target_id : continue

    sim_lang = lang_result[room_id][1]
    sim_hash = hash_result[room_id][1]
    sim_jaccard_hash = hash_jaccard_result[room_id][1]
    sim_category = category_result[room_id][1]
    sim_name = name_result[room_id][1]
    sim_intro = intro_result[room_id][1]

    # 가중 평균을 계산하고 최종 결과 리스트에 추가
    final_score = 0.4 * float(sim_lang) + 0.1 * float(sim_name) + 0.05 * float(sim_intro)
    final_score +=  0.15 * float(sim_hash) + 0.15 * float(sim_jaccard_hash)
    if(sim_category):
      final_score+=0.2

    result.append((room_id, final_score))

  result.sort(key=lambda r:r[1], reverse=True)
  return result[:top]

def get_rec_room_list(target_id, top):
  #path = os.path.dirname(os.path.abspath(__file__)) 
  #rooms = pd.read_csv(path+'/data/learniverse_sample_less.csv', encoding='euc-kr')
  rooms = read_data.get_data('rooms')
  rooms = rooms.fillna(" ")

  #집합
  rooms['roomLanguages'] = rooms['roomLanguages'].apply(str_to_set)
  rooms['roomHashtagsSet'] = rooms['roomHashtags'].apply(str_to_set)

  #정렬 
  rooms["roomHashtags"] = rooms.apply(lambda x: data_sort(x["roomHashtags"]), axis=1)

  result = recommend_list(rooms, target_id, top)
  result_df = pd.DataFrame(result, columns = ['roomId','finalScore'])

  merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
  return merged_df.sort_values(by='finalScore', ascending=False)
   
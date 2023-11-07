import pandas as pd
import read_data
import content_based, user_based
import concurrent.futures
from functools import partial

#데이터 처리
def rooms_set(data):
    rooms = data.fillna(" ")
    #집합
    rooms['roomLanguages'] = rooms['roomLanguages'].apply(content_based.str_to_set)
    rooms['roomHashtagsSet'] = rooms['roomHashtags'].apply(content_based.str_to_set)
    #정렬 
    rooms["roomHashtags"] = rooms.apply(lambda x: content_based.data_sort(x["roomHashtags"]), axis=1)
    return rooms

def learniverse_model(member_id):
    rooms = read_data.get_data('rooms')
    rooms_p_set = rooms_set(rooms)
    def_rooms = read_data.get_data('defaultRooms')

    target = read_data.get_data_find_member('joins',member_id)
    joins_default = target[target['isDefault'] == True] 
    joins = target[target['isDefault'] == False] 
    #print("join_room")
    #print(pd.merge(rooms, joins, on='roomId', how='inner').to_string(index=False))
    #print("dafault_room")
    #print(pd.merge(def_rooms, joins_default, on='roomId', how='inner').to_string(index=False))
    
    result_df = pd.DataFrame(columns = ['roomId','finalScore'])

    functions = [
        partial(default_room_based, rooms),
        partial(git_lang_based, rooms_p_set, rooms),
        partial(enter_room_base, rooms_p_set),
        partial(join_room_base, rooms_p_set),
        partial(content_based.get_rec_room_list_based_history, rooms)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda func: func(member_id), functions))

    #관심있는 방 기반 
    default_room_based_list = results[0]
    #깃헙 : 깃허브 사용 코드에 따른 정보 20
    git_lang_based_list = results[1]
    ##사용자 기록 
    #유사 사용자 - 방 접속 횟수에 따른 
    enter_based_list = results[2]
    #가입했던 방과 유사한 방 
    join_room_based_list = results[3]
    #검색어 기반
    history_based_list = results[4]

    #
    ##결과 합치기 
    # 관심 있는 방 가중치 : 사용자 방 가입 정보 없으면 80 이후에는 createdDate에 따라 떨어지기
    join_cnt = read_data.cnt_member_join_room(member_id)
    if(join_cnt == 0):
        default_weight = 0.8
    else: 
        member_data = read_data.get_data_find_member('members', member_id).iloc[0]
        diff_date = content_based.cul_date(member_data['createdDate'])
        default_weight = 0.8 - (0.003*diff_date)
        # join room 에 따른 가중치 떨어지기
        default_weight -= 0.3 * join_cnt

    
    if(default_weight < 0): default_weight = 0


    # 관심 있는 방 외의 가중치 
    entire_weight = 1 - default_weight
    lang_weight = entire_weight * 0.05
    enter_weight = entire_weight * 0.05
    join_weight = entire_weight * 0.65
    history_weight = entire_weight * 0.25

    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    result_df = cul_finalScore(result_df, default_room_based_list, default_weight)
    result_df = cul_finalScore(result_df, git_lang_based_list, lang_weight)
    result_df = cul_finalScore(result_df, enter_based_list, enter_weight)
    result_df = cul_finalScore(result_df, join_room_based_list, join_weight)
    result_df = cul_finalScore(result_df, history_based_list, history_weight)
    
    #print(result_df.sort_values(by='finalScore', ascending=False))
    result_df = result_df.sort_values(by='finalScore', ascending=False)
    rec_ids = result_df['roomId'].tolist()

    #가입한 방 삭제
    joins = read_data.get_data_find_member('joins', member_id)
    if(joins is not None):
        joins = joins[joins['isDefault'] != True]
        if(joins.shape[0] != 0):
            joins_ids = joins['roomId'].tolist()
            rec_ids = [item for item in rec_ids if item not in joins_ids]
    
    #ret = rec_ids[:5]

    #print("-----result-----")
    rooms['order'] = rooms['roomId'].apply(lambda x: rec_ids.index(x) if x in rec_ids else len(rec_ids))
    rooms = rooms.sort_values(by=['order'])
    rooms = rooms.drop(columns=['order'])

    merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
    #print(rooms.to_string(index=False))
    #print(merged_df.to_string(index=False))
    #merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
    #print(merged_df.sort_values(by='finalScore', ascending=False))
    return [int(x) for x in rec_ids]

def cul_finalScore(result_df, merge_df, weight):
    if(merge_df is None): return result_df
    
    #print("-----before-----")
    #print(result_df.sort_values(by='finalScore', ascending=False))
    #print("-----merge-----")
    #print(merge_df.sort_values(by='finalScore', ascending=False))
    for index, row in merge_df.iterrows():
        room_id = row['roomId']
        final_score = row['finalScore']
        
        #weight 처리 
        final_score = final_score * weight
        if room_id in result_df['roomId'].values:
            result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
        else :
            row['finalScore'] = final_score
            result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    #print("-----after----")
    #print(result_df.sort_values(by='finalScore', ascending=False))
    return result_df
    

#방 접속한 횟수에 따른 사용자 + 사용자 정보와 유사한 방
def enter_room_base(rooms, member_id):
    like_member = user_based.member_rec_list_based_enter(member_id)
    if(like_member is None): return None
    like_member_list = like_member.index.tolist()
    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    # 비슷한 사용자 3명 -> 서비스 확대시 5명으로 수정
    if(like_member_list is None): return None
    like_member_list = like_member_list[:3]
    for like_member_id in like_member_list:
        room_ids = user_based.find_member_rooms(like_member_id)
        for room_id in room_ids:
            temp_df = content_based.get_rec_room_list_id(rooms, room_id, True)
            for index, row in temp_df.iterrows():
                room_id = row['roomId']
                #final_score에 사용자 유사도 곱하기 
                final_score = row['finalScore'] * like_member[like_member_id]
                final_score /= len(like_member_list)
                if room_id in result_df['roomId'].values:
                    result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
                else :
                    result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)

    #결과 확인 
    # print(result_df.sort_values(by='finalScore', ascending=False))
   
    # 0보다 작은 값 제외 
    #result_df = result_df[result_df['finalScore'] > 0]

    #결과 확인 
    # print(result_df.sort_values(by='finalScore', ascending=False))
    return result_df.sort_values(by='finalScore', ascending=False)

#가입한 방들과 유사한 방
def join_room_base(rooms, member_id):
    joins = read_data.get_data('joins')
    joins = joins.fillna(" ")
    target = joins[joins['memberId'] == member_id]
    target = target[target['isDefault'] != True]
    room_ids = target['roomId'].tolist()

    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    for room_id in room_ids:
        temp_df = content_based.get_rec_room_list_id(rooms, room_id, False)
        
        #date 정보 
        this_data = target[target['roomId'] == room_id].iloc[0]
        #diff_create_date = content_based.cul_date((this_data['createdDate']))
        
        if 'pinDate' in this_data.index and pd.notna(this_data['pinDate']):
            pin_date = this_data['pinDate']
        else:
            pin_date = " "

        if pin_date == " " : # pin 이 없는 경우 -> 30으로 해야 0
            diff_pin_date = 30
        else: diff_pin_date = min(content_based.cul_date(pin_date), 30) # 최소 30이어야  0 
        
        for index, row in temp_df.iterrows():
            room_id = row['roomId']
            final_score = row['finalScore']
            #스터디룸 가입한 date 처리
            final_score = final_score * 0.75+(1-diff_pin_date*0.03) * 0.15
            
            final_score = final_score/len(room_ids)
            if room_id in result_df['roomId'].values:
                result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
            else:
                row['finalScore'] = final_score
                result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
   
    # 0보다 작은 값 제외 
    #result_df = result_df[result_df['finalScore'] > 0]
    return result_df.sort_values(by='finalScore', ascending=False)


# 관심있는 방 기반으로 가져오기
def default_room_based(rooms, member_id):
    joins = read_data.get_data('joins')
    joins = joins[joins['memberId'] == member_id]
    joins = joins[joins['isDefault'] != False]
    default_roomIds = joins['roomId'].to_list()

    default_rooms = read_data.get_data('defaultRooms')
    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    for room_id in default_roomIds :
        target_row = default_rooms[default_rooms['roomId'] == room_id].iloc[0]
        target_row['roomId'] = 0
        temp_df = content_based.get_rec_room_list_row(rooms, target_row.to_frame().T)
        for index, row in temp_df.iterrows():
            room_id = row['roomId']
            final_score = row['finalScore'] / len(default_roomIds)
            if room_id in result_df['roomId'].values:
                result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
            else :
                result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    # 0보다 작은 값 제외 
    #result_df = result_df[result_df['finalScore'] > 0]
    return result_df.sort_values(by='finalScore', ascending=False)

# 깃허브 언어기반 리스트 받아오기 
def git_lang_based(rooms_p_set, rooms, member_id):
    like_member = user_based.get_lang_member_list(member_id)
    if(like_member is None): return None
    like_member_list = like_member.index.tolist()

    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    # 비슷한 사용자 3명 -> 서비스 확대시 5명으로 수정
    like_member_list = like_member_list[:3]
    for like_member_id in like_member_list:
        room_ids = user_based.find_member_rooms(like_member_id)
        for room_id in room_ids:
            temp_df = content_based.get_rec_room_list_id(rooms_p_set, room_id, True)
            for index, row in temp_df.iterrows():
                room_id = row['roomId']
                #사용자 유사도 기반 
                final_score = row['finalScore'] * like_member[like_member_id]
                final_score /= len(like_member_list)
                if room_id in result_df['roomId'].values:
                    result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
                else:
                    result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)

    # 사용자 기반 : 0.5
    result_df['finalScore'] = result_df['finalScore'] * 0.5

    #개발 언어와 비슷한 언어 
    temp_df = content_based.get_rec_room_list_based_lang(rooms, member_id)
    for index, row in temp_df.iterrows():
        room_id = row['roomId']
        final_score = row['finalScore'] * 0.5 # 콘텐츠 기반 0.5
        if room_id in result_df['roomId'].values:
            result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
        else :
            result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    # 0보다 작은 값 제외 
    #result_df = result_df[result_df['finalScore'] > 0]
    return result_df.sort_values(by='finalScore', ascending=False)



def check_room_info(result_df):
  rooms = read_data.get_data('rooms')

  merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
  return merged_df.sort_values(by='finalScore', ascending=False)

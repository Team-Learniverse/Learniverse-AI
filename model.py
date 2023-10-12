import pandas as pd
import read_data
import content_based, user_based

def learniverse_model(member_id):
    rooms = read_data.get_data('rooms')
    rooms = rooms.fillna(" ")
    def_rooms = read_data.get_data('defaultRooms')

    target = read_data.get_data_find_member('joins',member_id)
    joins_default = target[target['isDefault'] == True] 
    joins = target[target['isDefault'] == False] 
    print("join_room")
    print(pd.merge(rooms, joins, on='roomId', how='inner'))
    print("dafault_room")
    print(pd.merge(def_rooms, joins_default, on='roomId', how='inner'))
    
    result_df = pd.DataFrame(columns = ['roomId','finalScore'])

    #관심있는 방 기반 
    default_room_based_list = default_room_based(member_id)
    
    #깃헙 : 깃허브 사용 코드에 따른 정보 20
    git_lang_based_list = git_lang_based(member_id)

    ##사용자 기록 
    #유사 사용자 - 방 접속 횟수에 따른 
    enter_based_list = enter_room_base(member_id)
    #가입했던 방과 유사한 방 
    join_room_based_list = join_room_base(member_id)
    #검색어 기반
    history_based_list = content_based.get_rec_room_list_based_history(member_id)

    #
    ##결과 합치기 
    # 관심 있는 방 가중치 : 사용자 방 가입 정보 없으면 80 이후에는 createdDate에 따라 떨어지기
    if(read_data.cnt_member_join_room(member_id) == 0):
        default_weight = 0.8
    else: 
        member_data = read_data.get_data_find_member('members', member_id).iloc[0]
        diff_date = content_based.cul_date(member_data['createdDate'])
        default_weight = 0.8 - (0.003*diff_date)
    if(default_weight < 0): default_weight = 0
    # 관심 있는 방 외의 가중치 
    entire_weight = 1 - default_weight
    lang_weight = entire_weight * 0.15
    enter_weight = entire_weight * 0.25
    join_weight = entire_weight * 0.35
    history_weight = entire_weight * 0.25

    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    result_df = cul_finalScore(result_df, default_room_based_list, default_weight)
    #print(result_df.sort_values(by='finalScore', ascending=False))
    result_df = cul_finalScore(result_df, git_lang_based_list, lang_weight)
    #print(result_df.sort_values(by='finalScore', ascending=False))
    result_df = cul_finalScore(result_df, enter_based_list, enter_weight)
    #print(result_df.sort_values(by='finalScore', ascending=False))
    result_df = cul_finalScore(result_df, join_room_based_list, join_weight)
    #print(result_df.sort_values(by='finalScore', ascending=False))
    result_df = cul_finalScore(result_df, history_based_list, history_weight)
    
    result_df = result_df.sort_values(by='finalScore', ascending=False)
    rec_ids = result_df['roomId'].tolist()

    #가입한 방 삭제
    joins = read_data.get_data_find_member('joins', member_id)
    if(joins is not None):
        joins = joins[joins['isDefault'] != True]
        if(joins.shape[0] != 0):
            joins_ids = joins['roomId'].tolist()
            rec_ids = [item for item in rec_ids if item not in joins_ids]
    
    ret = rec_ids[:5]

    print("-----result-----")
    merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
    print(merged_df.sort_values(by='finalScore', ascending=False))
    return [int(x) for x in ret]

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
        elif final_score > 0:
            row['finalScore'] = final_score
            result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    #print("-----after----")
    #print(result_df.sort_values(by='finalScore', ascending=False))
    return result_df
    

#방 접속한 횟수에 따른 사용자 + 사용자 정보와 유사한 방
def enter_room_base(member_id):
    like_member_list = user_based.member_rec_list_based_enter(member_id)
    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    # 비슷한 사용자 3명 -> 서비스 확대시 5명으로 수정
    if(like_member_list is None): return None
    like_member_list = like_member_list[:3]
    for like_member_id in like_member_list:
        room_ids = user_based.find_member_rooms(like_member_id)
        for room_id in room_ids:
            print(room_id)
            temp_df = content_based.get_rec_room_list_id(room_id, True)
            for index, row in temp_df.iterrows():
                room_id = row['roomId']
                final_score = row['finalScore']
                if room_id in result_df['roomId'].values:
                    result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
                elif final_score > 0:
                    result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)

    #print(result_df.sort_values(by='finalScore', ascending=False))
    return result_df.sort_values(by='finalScore', ascending=False)

#가입한 방들과 유사한 방
def join_room_base(member_id):
    joins = read_data.get_data('joins')
    joins = joins.fillna(" ")
    target = joins[joins['memberId'] == member_id]
    target = target[target['isDefault'] != True]
    room_ids = target['roomId'].tolist()

    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    for room_id in room_ids:
        temp_df = content_based.get_rec_room_list_id(room_id, False)
        
        #date 정보 
        this_data = target[target['roomId'] == room_id].iloc[0]
        diff_create_date = content_based.cul_date((this_data['createdDate']))
        
        if this_data.name == 'pinDate':
            pin_date = this_data['pinDate']
        else:
            pin_date = " "
        if pin_date == " " :
            diff_pin_date = 30
        else: diff_pin_date = min(content_based.cul_date(pin_date), 30)

        for index, row in temp_df.iterrows():
            room_id = row['roomId']
            final_score = row['finalScore']
            #스터디룸 가입한 date 처리
            final_score = final_score * 0.5 +(1-diff_create_date*0.03) * 0.35+(1-diff_pin_date*0.03) * 0.15
            final_score = final_score/len(room_ids)
            if room_id in result_df['roomId'].values:
                result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
            elif final_score > 0:
                row['finalScore'] = final_score
                result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
   
    return result_df.sort_values(by='finalScore', ascending=False)


# 관심있는 방 기반으로 가져오기
def default_room_based(member_id):
    joins = read_data.get_data('joins')
    joins = joins[joins['memberId'] == member_id]
    joins = joins[joins['isDefault'] != False]
    default_roomIds = joins['roomId'].to_list()

    default_rooms = read_data.get_data('defaultRooms')
    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    for room_id in default_roomIds :
        target_row = default_rooms[default_rooms['roomId'] == room_id].iloc[0]
        target_row['roomId'] = 0
        temp_df = content_based.get_rec_room_list_row(target_row.to_frame().T)
        for index, row in temp_df.iterrows():
            room_id = row['roomId']
            final_score = row['finalScore']
            if room_id in result_df['roomId'].values:
                result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
            elif final_score > 0:
                result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    return result_df.sort_values(by='finalScore', ascending=False)

# 깃허브 언어기반 리스트 받아오기 
def git_lang_based(member_id):
    like_member_list = user_based.get_lang_member_list(member_id)
    if(like_member_list is None): return None

    result_df = pd.DataFrame(columns = ['roomId','finalScore'])
    # 비슷한 사용자 3명 -> 서비스 확대시 5명으로 수정
    like_member_list = like_member_list[:3]
    for like_member_id in like_member_list:
        room_ids = user_based.find_member_rooms(like_member_id)
        for room_id in room_ids:
            temp_df = content_based.get_rec_room_list_id(room_id, True)
            for index, row in temp_df.iterrows():
                room_id = row['roomId']
                final_score = row['finalScore']
                if room_id in result_df['roomId'].values:
                    result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
                elif final_score > 0:
                    result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)

    # 사용자 기반 : 0.5
    result_df['finalScore'] = result_df['finalScore'] * 0.5

    #개발 언어와 비슷한 언어 
    temp_df = content_based.get_rec_room_list_based_lang(member_id)
    for index, row in temp_df.iterrows():
        room_id = row['roomId']
        final_score = row['finalScore'] * 0.5 # 콘텐츠 기반 0.5
        if room_id in result_df['roomId'].values:
            result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
        elif final_score > 0:
            result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    return result_df.sort_values(by='finalScore', ascending=False)



def check_room_info(result_df):
  rooms = read_data.get_data('rooms')

  merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
  return merged_df.sort_values(by='finalScore', ascending=False)

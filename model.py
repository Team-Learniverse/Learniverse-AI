import pandas as pd
import read_data
import content_based

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
        temp_df = content_based.get_rec_room_list(target_row.to_frame().T, 50)
        print(target_row.to_frame().T)
        for index, row in temp_df.iterrows():
            room_id = row['roomId']
            final_score = row['finalScore']
            if room_id in result_df['roomId'].values:
                result_df.loc[result_df['roomId'] == room_id, 'finalScore'] += final_score
            elif final_score > 0:
                result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
    
    return result_df.sort_values(by='finalScore', ascending=False)

def check_room_info(result_df):
  rooms = read_data.get_data('rooms')

  merged_df = pd.merge(rooms, result_df, on='roomId', how='inner')
  return merged_df.sort_values(by='finalScore', ascending=False)

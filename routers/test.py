from fastapi import APIRouter
import user_based, content_based, read_data, model

router = APIRouter(
	prefix="/test",
    tags=["test"]
)

@router.get("/recommendRoomTest")
def get_rec_room_test():
    member_room_list = user_based.get_member_room_list()
    recommend_list = content_based.get_rec_room_list(member_room_list[0], 5)
    print(recommend_list)
    

@router.get("/recommendRoom")
def get_rec_room(memberId:int):
    member_room_list = user_based.get_member_room_list()
    recommend_list = content_based.get_rec_room_list(member_room_list[0], 5)
    room_id_list = recommend_list['roomId'].to_list()
    return {"status":200, "success": "OK", "data":room_id_list}

@router.get("/datatest")
def get_room():
    df = read_data.get_data('rooms')
    print(df.head())

@router.get("/defult")
def test_def(memberId:int):
    recommend_list = model.default_room_based(memberId)
    print(model.check_room_info(recommend_list))
    #return recommend_list

@router.get("/member/lang")
def test_member_lang(memberId:int):
    recommend_list = user_based.get_lang_member_list(memberId)
    print(recommend_list)

@router.get("/room/lang")
def test_member_lang(memberId:int):
    recommend_list = content_based.get_rec_room_list_based_lang(memberId, 30)
    print(recommend_list)

@router.get("/history")
def test_history(memberId:int):
    recommend_list = content_based.get_rec_room_list_based_history(memberId, 30)
    print(recommend_list)
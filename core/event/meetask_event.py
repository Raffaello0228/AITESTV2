import uuid
import time

from core.model.meetask_model import MeetAskModel
from core.service.meetask_service import meetask_stream_ask_question


def meetask_question_ask(request, **kwargs):
    # 使用时间戳后6位和UUID前6位组合生成唯一ID
    if not hasattr(request.session, "user"):
        timestamp = str(int(time.time()))[-6:]  # 取时间戳后6位
        short_uuid = str(uuid.uuid4())[:6]  # 取UUID前6位
        request.session.user = (
            f"test_{timestamp}{short_uuid}"  # 格式：t + 6位时间戳 + 6位UUID
        )

    question = kwargs.get("query")
    user = request.session.user

    response_data = meetask_stream_ask_question(question, user)
    ma_model = MeetAskModel(**kwargs, **response_data)
    ma_model.query_data()
    excel_data = ma_model.to_execl()
    request.session.export_excel.append(excel_data)
    while ma_model.should_follow_up():
        question = ma_model.follow_up_question
        response_data = meetask_stream_ask_question(question, user)
        ma_model = MeetAskModel(**kwargs, **response_data)
        ma_model.query_data()
        excel_data = ma_model.to_execl()
        request.session.export_excel.append(excel_data)

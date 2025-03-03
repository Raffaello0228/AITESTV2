import functools
import pdb
import time
from datetime import datetime
import json
import requests
from func_timeout import func_set_timeout

from core.common.method import receive_stream_content
from core.utils.logger import logger
from constant import MEETASK_URL


@func_set_timeout(180)
def meetask_stream_ask_question(query, user):
    logger.info(f"用户{user}向MeetAsk查询: {query}")
    payload = json.dumps({"llmType": "openai", "query": query, "user": user})
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"{MEETASK_URL}/meetask/stream/askQuestion", headers=headers, data=payload
    )
    res = receive_stream_content(response)
    content = res.split("\n\n")[-2].replace("data:", "")
    data = json.loads(content).get("result", {})
    answer = data.get("answer", "")
    qa_id = data.get("qaId", "")
    logger.info(f"QAID:{qa_id}|MeetAsk回答：{answer}")
    return {"response": answer, "qa_id": qa_id}

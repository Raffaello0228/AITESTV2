from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import time

from func_timeout import FunctionTimedOut
from constant import ADSHUB_PRE_APP_AGENT_CODEDE, ADSHUB_PRE_EC_AGENT_CODEDE
from core.model.adshub_pre_model import AdshubRequest
from core.model.factory import factory
from core.service.adshub_pre_service import (
    adshub_ad_detail_backend,
    adshub_ad_generate_backend,
    adshub_ask_question_stream,
)
from core.service.llm_service import chat_gpt_pure_text, create_messages
from core.utils.logger import logger
from core.utils.database import DBPool
from core.template.prompt.prompt import adshub_pre_chat_helper, adshub_pre_background
from core.common.method import retry_decorator


@dataclass
class AdshubPreConfig:
    """广告预处理配置类"""

    max_retries: int = 3
    retry_delay: int = 2
    default_language: str = "zh_CN"


class DatabaseError(Exception):
    """数据库操作异常"""

    pass


class APIError(Exception):
    """API调用异常"""

    pass


class AdshubPreProcessor:
    """广告预处理器类"""

    def __init__(self, config: AdshubPreConfig = AdshubPreConfig()):
        self.config = config

    def _process_fields(self, raw_data: Dict) -> Dict[str, Any]:
        """处理字段,将其转换为扁平结构"""
        result = {}
        for _, data in raw_data.items():
            if not isinstance(data, dict):
                continue
            fields = data.get("fields", {})
            for field_name, field_data in fields.items():
                if isinstance(field_data, dict):
                    result[field_name] = field_data.get("value", "")
        return result

    @retry_decorator(max_retries=3, delay=2)
    def _query_database(self, conversation_id: str) -> Dict:
        """查询数据库"""
        sql = """select extracted_fields from conversation_info 
                where external_conversation_id="{0}" 
                order by create_time desc limit 100;""".format(
            conversation_id
        )
        try:
            data_res = DBPool().query(sql)
            if not data_res:
                raise DatabaseError("未找到数据")
            return data_res[0]
        except Exception as e:
            raise DatabaseError(f"数据库查询失败: {str(e)}")

    def collect_request(self, request: Any, agent_code: str, **kwargs) -> Optional[str]:
        """收集请求信息"""
        request.session.current_case = {}

        # 获取问题
        question = self._get_question(request, **kwargs)
        logger.info(f"用户提问:\n{question}")
        request.session.current_case.update({"question": question})

        # 调用问答API
        try:
            api_res = self._call_question_api(
                question,
                request,
                agent_code,
                kwargs.get("language", self.config.default_language),
            )
        except FunctionTimedOut:
            logger.error("请求超时")
            return None

        # 处理响应
        conversation_id = api_res.get("conversation_id")
        if not conversation_id:
            return None
        request.session.current_case.update({"conversation_id": conversation_id})

        try:
            data_res = self._query_database(conversation_id)
            brief = (
                json.loads(data_res["extracted_fields"])
                if "extracted_fields" in data_res
                else {}
            )

            # 处理数据
            adrequest = self._process_fields(brief)
            request.session.adrequest = adrequest

            # 更新导出数据
            row = {"question": question}
            request_dict = {f"request_{k}": v for k, v in adrequest.items()}
            row.update(**request_dict)
            request.session.export_excel.append(row)

            return conversation_id
        except Exception as e:
            logger.error(f"处理请求失败: {str(e)}")
            return None

    def _get_question(self, request: Any, **kwargs) -> str:
        """获取问题"""
        question = kwargs.get("query")
        if question:
            return question

        history = (
            json.dumps(request.session.history)
            if hasattr(request.session, "history")
            else ""
        )
        item_desc = kwargs.get("item_desc", "")
        price = kwargs.get("price", "")
        objective = kwargs.get("objective", "")

        prompt = adshub_pre_chat_helper.format(
            history=history,
            item_info=json.dumps({"item_desc": item_desc, "price": price}),
            objective=objective,
        )
        messages = create_messages([{"q": prompt}], system=adshub_pre_background)
        ai_res = chat_gpt_pure_text(messages)

        try:
            return list(json.loads(ai_res).values())[0]
        except Exception:
            return ai_res

    @retry_decorator(max_retries=3, delay=2)
    def _call_question_api(
        self, question: str, request: Any, agent_code: str, language: str
    ) -> Dict:
        """调用问答API"""
        conversation_id = (
            request.session.conversation_id
            if hasattr(request.session, "conversation_id")
            else None
        )
        return adshub_ask_question_stream(
            question,
            language=language,
            session_id=conversation_id,
            _agent_code=agent_code,
        )

    def generate_ads_by_id(
        self, request: Any, agent_code: str, conversation_id: str
    ) -> None:
        """根据会话ID生成广告"""
        if not conversation_id:
            return

        try:
            # 获取广告计划
            plan_id = adshub_ad_generate_backend(
                conversation_id, _agent_code=agent_code
            ).get("planId")
            ad_detail_response = adshub_ad_detail_backend(
                plan_id, _agent_code=agent_code
            )

            case_dict = request.session.current_case.copy()
            adrequest = request.session.adrequest.copy()
            request_dict = {f"request_{k}": v for k, v in adrequest.items()}

            # 处理响应
            if ad_detail_response and ad_detail_response.get("planStatus") == "SUCCESS":
                self._process_successful_response(
                    request, ad_detail_response, case_dict, request_dict
                )
            else:
                row = {}
                row.update(**request_dict)
                request.session.export_excel.append(row)
        except Exception as e:
            logger.error(f"生成广告失败: {str(e)}")

    def _process_successful_response(
        self, request: Any, response: Dict, case_dict: Dict, request_dict: Dict
    ) -> None:
        """处理成功的响应"""
        plan_detail = response.get("planDetail", {})
        ad = factory.create_model("adshubad", **plan_detail)

        for campaign_data in ad.campaignList:
            campaign = factory.create_model("adshubcampaign", **campaign_data)
            campaigns_dict = campaign.__dict__.copy()
            campaigns_dict.pop("adGroupList")

            for adgroup_data in campaign.adGroupList:
                adgroup = factory.create_model("adshubadgroup", **adgroup_data)
                row = {}
                row.update(**case_dict)
                row.update(**request_dict)
                row.update(**{f"campaign_{k}": v for k, v in campaigns_dict.items()})
                row.update(**{f"adgroup_{k}": v for k, v in adgroup.__dict__.items()})
                request.session.export_excel.append(row)


# 创建全局处理器实例
processor = AdshubPreProcessor()


def adshub_pre_eb(request: Any, **kwargs) -> None:
    """电商广告预处理入口"""
    agent_code = ADSHUB_PRE_EC_AGENT_CODEDE
    conversation_id = processor.collect_request(
        request, agent_code=agent_code, **kwargs
    )
    if conversation_id:
        processor.generate_ads_by_id(request, agent_code, conversation_id)


def adshub_pre_app(request: Any, **kwargs) -> None:
    """APP广告预处理入口"""
    agent_code = ADSHUB_PRE_APP_AGENT_CODEDE
    conversation_id = processor.collect_request(
        request, agent_code=agent_code, **kwargs
    )
    if conversation_id:
        processor.generate_ads_by_id(request, agent_code, conversation_id)

import json
from core.model.rag_model import RAGModel
from core.service.llm_service import chat_gpt_pure_text, create_messages
from core.utils.database import DBPool
from core.common.method import num_tokens_from_string
from core.utils.logger import logger
from constant import meetask_db_info


meet_ask_his = """请你作为用户模拟与广告营销知识问答系统对话
历史对话：
{0}
目标问题：{1}
请站在用户角度,作为提问者根据历史对话向系统提问，引导系统回答目标问题
回答保持简洁，限制在20字以内
请用json格式输出,key为q,value为输出结果
"""
meetask_db_pool = DBPool()
meetask_field_dict = {
    "qa_id": "a.id",
    "answer_first_char_time": "answer_first_char_time",
    "ask_time": "ask_time",
    "answer_time": "answer_time",
    "creator": "creator",
    "answer": "a.answer",
    "adjusted_question": "adjusted_question",
    "intent": "intent",
    "answer_type": "a.answer_type",
    "source_level": "a.source_level",
    "faq1_source": "faq1_source",
    "doc_source": "doc_source",
    "es_doc_source": "es_doc_source",
    "faq2_source": "faq2_source",
    "merged_doc_source": "merged_doc_source",
    "ranked_doc_source": "ranked_doc_source",
    "ask_intent_time_cost": "ask_intent_time_cost",
    "search_faq_time_cost": "search_faq_time_cost",
    "search_doc_time_cost": "search_doc_time_cost",
    "search_es_time_cost": "search_es_time_cost",
    "ranking_time_cost": "ranking_time_cost",
    "faq1_ai_time_cost": "faq1_ai_time_cost",
    "decision_ai_time_cost": "decision_ai_time_cost",
    "doc_ai_time_cost": "doc_ai_time_cost",
    "doc_first_answer_time_cost": "doc_first_answer_time_cost",
    "faq1_llm_response": "faq1_llm_response",
    "doc_llm_response": "doc_llm_response",
    "answer_trace": "answer_trace",
    "original_dialogue_history": "original_dialogue_history",
    "source": "source",
    "all_source": "all_source",
    "source_ai_time_cost": "source_ai_time_cost",
    "source_and_decision_ai_time_cost": "source_and_decision_ai_time_cost",
}
meetask_field_sql = ",".join(f"{v} as {k}" for k, v in meetask_field_dict.items())
meetask_sql_template = """select 
            {0}
            from (select * from sino_ask_qa 
            where  id = "{1}") a
            left join sino_ask_qa_process_trace c
            on a.id=c.qa_id
            order by a.create_time desc;"""


class MeetAskModel:

    def __init__(
        self,
        qa_id=None,
        query=None,
        target_question=None,
        gt_answer=None,
        response=None,
        **kwargs,
    ):
        # super().__init__(**kwargs)
        self.qa_id = qa_id
        self.query = query
        self.gt_answer = gt_answer
        self.response = response
        self.target_question = target_question
        self.follow_up_question = None
        self.history = []

    def query_data(self):
        """查询并处理数据"""
        if not self.qa_id:
            logger.error("qa_id 不能为空")
            raise ValueError("qa_id is required")

        logger.info(f"正在查询 qa_id: {self.qa_id} 的日志...")
        debug_sql = meetask_sql_template.format(meetask_field_sql, self.qa_id)

        try:
            # 使用优化后的查询方法（带重试机制）
            data = meetask_db_pool.query(debug_sql)

            if not data:
                logger.warning(f"未找到 qa_id 为 {self.qa_id} 的记录")
                return

            self.sql_result = data[0]
            logger.info(f"成功查询到记录，qa_id: {self.qa_id}")

            # 处理查询结果
            self._process_query_result()

        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}")
            logger.error(f"SQL: {debug_sql}")
            raise

    def _process_query_result(self):
        """处理查询结果"""
        self.output_result = {
            "Respones": self.response,
            "query": self.query,
            "gt_answer": self.gt_answer,
        }
        self.history.append({"Q": self.query})
        self.history.append({"A": self.sql_result["answer"]})

        for k, v in self.sql_result.items():
            try:
                self._process_field(k, v)
            except Exception as e:
                logger.error(f"处理字段 {k} 时出错: {str(e)}")
                continue

    def _process_field(self, key, value):
        """处理单个字段"""
        self.output_result[key] = value

        if not value:
            return

        processors = {
            "source": self._process_source,
            "all_source": self._process_all_source,
            "faq1_source": self._process_faq1,
            "doc_source": self._process_doc,
            "es_doc_source": self._process_es_doc,
            "faq2_source": self._process_faq2,
            "merged_doc_source": self._process_merged_doc,
            "ranked_doc_source": self._process_ranked_doc,
            "source_and_decision_ai_time_cost": self._process_time_cost,
        }

        if key in processors:
            processors[key](value)

    def to_execl(self):

        return self.output_result

    def should_follow_up(self):
        if self.sql_result.get("answer_type", "") == 3:
            prompt = meet_ask_his.format(
                self.history,
                self.target_question if self.target_question else self.query,
            )
            meet_ask_dial_response = chat_gpt_pure_text(
                create_messages([{"q": prompt}])
            )
            try:
                question = json.loads(meet_ask_dial_response)
                question = question.get("q", "")
            except:
                question = meet_ask_dial_response
            logger.info(f"生成追问问题：{question}")
            self.follow_up_question = question
            return True
        return False

    def _process_source(self, value):
        """处理 source 字段"""
        try:
            source = json.loads(value)
            source_data = source.get("similarityResults", [])
            google_source = source.get("googleVectorResults", [])
            # 过滤掉id为xinmeitibaodian的source
            all_source = source_data + google_source
            if all_source:
                all_source = [
                    {"id": s.get("id"), "text": s.get("answerOrContent")}
                    for s in all_source
                    if s.get("id") != "xinmeitibaodian"
                ]
            source_ids = [s.get("id") for s in all_source]

            self.output_result.update(
                {
                    "google_source": google_source,
                    "source": source_data,
                    "all_source": all_source,
                    "source_ids": source_ids,
                }
            )
        except Exception as e:
            logger.error(f"处理 source 字段失败: {str(e)}")

    def _process_all_source(self, value):
        """处理 source 字段"""
        try:
            source = json.loads(value)
            source_data = source.get("similarityResults", [])
            google_source = source.get("googleVectorResults", [])
            # 过滤掉id为xinmeitibaodian的source
            all_source = source_data + google_source
            if all_source:
                all_source = [
                    {"id": s.get("id"), "text": s.get("answerOrContent")}
                    for s in all_source
                    if s.get("id") != "xinmeitibaodian"
                ]

            self.output_result.update({"all_source": all_source})
        except Exception as e:
            logger.error(f"处理 source 字段失败: {str(e)}")

    def _process_faq1(self, value):
        """处理 faq1_source 字段"""
        try:
            faq_97 = json.loads(value) if value else None
            self.output_result.update(
                {
                    "faq_97": faq_97,
                    "faq_97_token": num_tokens_from_string(value or ""),
                    "faq_97_len": len(faq_97 or ""),
                }
            )
        except Exception as e:
            logger.error(f"处理 faq1_source 字段失败: {str(e)}")

    def _process_doc(self, value):
        """处理 doc_source 字段"""
        try:
            milvus_doc = json.loads(value) if value else None
            self.output_result.update(
                {
                    "milvus_doc": milvus_doc,
                    "milvus_doc_token": num_tokens_from_string(value or ""),
                    "milvus_doc_len": len(milvus_doc or ""),
                }
            )
        except Exception as e:
            logger.error(f"处理 doc_source 字段失败: {str(e)}")

    def _process_es_doc(self, value):
        """处理 es_doc_source 字段"""
        try:
            es_doc = json.loads(value) if value else None
            self.output_result.update(
                {
                    "es_doc": es_doc,
                    "es_doc_token": num_tokens_from_string(value or ""),
                    "es_doc_len": len(es_doc or ""),
                }
            )
        except Exception as e:
            logger.error(f"处理 es_doc_source 字段失败: {str(e)}")

    def _process_faq2(self, value):
        """处理 faq2_source 字段"""
        try:
            faq_93 = json.loads(value) if value else None
            self.output_result.update(
                {
                    "faq_93": faq_93,
                    "faq_93_token": num_tokens_from_string(value or ""),
                    "faq_93_len": len(faq_93 or ""),
                }
            )
        except Exception as e:
            logger.error(f"处理 faq2_source 字段失败: {str(e)}")

    def _process_merged_doc(self, value):
        """处理 merged_doc_source 字段"""
        try:
            merged_doc = json.loads(value) if value else None
            self.output_result.update(
                {
                    "merged_doc": value,
                    "merged_doc_token": num_tokens_from_string(value or ""),
                    "merged_doc_len": len(merged_doc or ""),
                }
            )
        except Exception as e:
            logger.error(f"处理 merged_doc_source 字段失败: {str(e)}")

    def _process_ranked_doc(self, value):
        """处理 ranked_doc_source 字段"""
        try:
            ranked_doc = json.loads(value) if value else None

            self.output_result.update(
                {
                    "ranked_doc": ranked_doc,
                    "ranked_doc_token": num_tokens_from_string(value or ""),
                    "ranked_doc_len": len(ranked_doc or ""),
                }
            )
        except Exception as e:
            logger.error(f"处理 ranked_doc_source 字段失败: {str(e)}")

    def _process_time_cost(self, value):
        """处理时间相关字段"""
        try:
            first_char_cost = (
                self.sql_result["answer_first_char_time"] - self.sql_result["ask_time"]
            ).seconds
            total_cost = (
                self.sql_result["answer_time"] - self.sql_result["ask_time"]
            ).seconds
            source_and_decision_ai_time_cost = self.sql_result[
                "source_and_decision_ai_time_cost"
            ]
            doc_first_answer_time_cost = self.sql_result["doc_first_answer_time_cost"]

            a4_first_char_cost = (source_and_decision_ai_time_cost or 0) + (
                doc_first_answer_time_cost or 0
            )

            self.output_result.update(
                {
                    "A4_first_char_cost": a4_first_char_cost,
                    "first_char_cost": first_char_cost,
                    "total_cost": total_cost,
                }
            )
        except Exception as e:
            logger.error(f"处理时间成本字段失败: {str(e)}")

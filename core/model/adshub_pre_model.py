from typing import Any, Dict, Optional
from core.model.factory import ModelFactory


@ModelFactory.register()
class AdshubAd:
    """广告模型"""


@ModelFactory.register()
class AdshubAdgroup:
    """广告组模型"""


@ModelFactory.register()
class AdshubCampaign:
    """广告系列模型"""


@ModelFactory.register()
class AdshubRequest:
    """广告请求模型"""

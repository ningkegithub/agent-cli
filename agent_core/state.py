import operator
from typing import Annotated, List, TypedDict, Dict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    智能体状态定义。
    
    属性:
        messages: 对话历史记录，使用 operator.add 实现自动追加。
        active_skills: 已激活的技能字典，键为技能名称，值为技能的具体协议/指令内容。
    """
    messages: Annotated[List[BaseMessage], operator.add]
    active_skills: Dict[str, str]

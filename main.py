from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
from astrbot.api import logger
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext

from pydantic import Field
from pydantic.dataclasses import dataclass

from .byrdocs import search_byrdocs, query_byrdocs_guide
from .wts_bridge import WTSBridge


wts = WTSBridge()
global RTN_LIMIT
RTN_LIMIT = 5

@dataclass
class ByrdocsTool(FunctionTool[AstrAgentContext]):
    name: str = "byrdocs_search"  # 工具名称
    description: str = "A tool to fetch books,documents and testpaperes from byrdocs"  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Keywords to search documents.",
                },
                "type": {
                    "type": "string",
                    "description": "types, including: book,doc,test,all.",
                },
                "limit": {
                    "type": "number",
                    "description": "limit of return count."
                }
            },
            "required": ["keywords", "type", "limit"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        keyword = (kwargs.get("keywords") or "").strip()
        type = (kwargs.get("type") or "all").strip()
        limit = kwargs.get("limit") or 5
        ret = await search_byrdocs(keyword=keyword, type_=type, limit=limit, jmespath="[].{data: data, url:url}")
        return ret if ret else "no result"

@dataclass
class ByrdocsGuidTool(FunctionTool[AstrAgentContext]):
    name: str = "byrdocs_guide_search"  # 工具名称
    description: str = "A tool to fetch daily helps from guide.byrdocs.org, provide for BUPTers"  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Keywords to search in byrdocs_guide.",
                }
            },
            "required": ["keywords"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        keyword = (kwargs.get("keywords") or "").strip()
        ret = await query_byrdocs_guide(query=keyword)
        return str(ret) if ret else "no result"

@dataclass
class WTSPoly(FunctionTool[AstrAgentContext]):
    name: str = "wtspoly"  # 工具名称
    description: str = "A tool to fetch shuttle bus info, course shedule, important events, empty classrooms, current and all terms, grades of exams or exam shedules"  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "callable": {
                    "type": "string",
                    "description": "Which callable you need, including {get_shuttle_bus, get_important_events, get_empty_classroom, get_personal_schedule, get_terms, get_grads, get_exams}",
                }
            },
            "required": ["callable"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        callable = (kwargs.get("callable") or "").strip()
        ret = await wts.str2callable(callable)
        return ret if ret else "no result"

PLUGIN_NAME = "astrbot_plugin_BUPT_search"

@register(f"{PLUGIN_NAME}", "xiewoc", "一个柏油信息的综合查询插件，支持AI自主查询", "1.0.0", "https://github.com/xiewoc/astrbot_plugin_BUPT_search")
class astrbot_plugin_BUPT_search(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.config = config
        global RTN_LIMIT
        # wts
        self.config_curr = self.config.get("config_curri", {})
        wts.ACCOUNT = self.account = self.config_curr.get("account")
        wts.PSWD_JW = self.password_jw = self.config_curr.get("password_jw")
        wts.PSWD_JXY = self.password_jxy = self.config_curr.get("password_jxy")

        # byr
        self.config_byr = self.config.get("config_byr", {})
        self.rtn_limit = RTN_LIMIT = self.config_byr.get("rtn_limit")

        self.context.add_llm_tools(ByrdocsTool(), ByrdocsGuidTool(),WTSPoly())

    @filter.command_group("bupt")
    def bupt():
        pass

    @bupt.command("set")
    async def set(self, event: AstrMessageEvent, ac: str, ps_jw: str, ps_jxy: str):
        try:
            await wts.set_acpw(ac, ps_jw, ps_jxy)
            yield event.plain_result("successfully set the account and passwords")
        except Exception as e:
            logger.error(e)

    @bupt.command("docs")
    async def guide(self, event: AstrMessageEvent, keyword: str):
        ret = await search_byrdocs(keyword, jmespath="[].{data: data, url:url}")
        yield event.plain_result(f"{ret}")

#
#    @bupt.command("get_bus")
#    async def get_bus(self, event: AstrMessageEvent):
#        yield event.plain_result(str(await wts.get_shuttle_bus()))3
#
#    @bupt.command("get_events")
#    async def get_event(self, event: AstrMessageEvent):
#        return wts.get_important_events()
#
#    @bupt.command("get_holidays")
#    async def get_holidays(self, event: AstrMessageEvent, YYYY: int):
#        return wts.get_holidays(YYYY)
#
#    @bupt.command("get_empty_classroom")
#    async def get_empty_classroom(self, event: AstrMessageEvent):
#        return wts.get_empty_classroom()

"""多年以后：woc，巴普特今天网怎么又炸了"""
"""
MCP Server：对外暴露 Prompt 模板
mcp 1.x FastMCP
"""
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

# 初始化服务
mcp = FastMCP("prompt‑demo‑server")


# Prompt 1：单参数，返回字符串提示词
@mcp.prompt()
def summarize_content(text: str, style: str = "简洁") -> str:
    """
    生成内容摘要提示词
    :param text: 需要总结的原文
    :param style: 输出风格：简洁/详细/口语
    """
    return f"""请以{style}的风格，总结下面这段文字，不要多余内容：
---原文开始---
{text}
---原文结束---
"""


# Prompt 2：多轮对话模板，返回 PromptMessage 消息列表
@mcp.prompt()
def code_review_prompt(language: str, target: str = "代码质量") -> list[PromptMessage]:
    """
    代码审查多轮提示模板
    :param language: 编程语言 python/java/js
    :param target: 审查方向：安全/性能/代码质量
    """
    system_instruction = f"你是一名资深{language}工程师，请重点从【{target}】角度审查代码，给出优化建议。"
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=f"【系统指令】\n{system_instruction}\n下面是待审查的代码，请开始分析：")
        )
    ]

if __name__ == "__main__":
    # stdio 模式等待客户端连接
    mcp.run(transport="stdio")

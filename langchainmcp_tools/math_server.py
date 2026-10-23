"""
MCP Server 示例：数学计算服务
使用官方 mcp SDK (FastMCP) 构建，通过 stdio 传输暴露工具。
"""
import re
from mcp.server.fastmcp import FastMCP

# 创建一个名为 "math" 的 MCP Server 实例
mcp = FastMCP("math")


# 安全的数学表达式计算（禁止函数调用和危险操作）
def _safe_eval(expression: str) -> float:
    # 只允许数字、运算符、括号、小数点、空格
    if not re.fullmatch(r'[\d\s\+\-\*\/\(\)\.]+', expression):
        raise ValueError("表达式包含非法字符，仅支持数字和 + - * / ( )")
    # 用受限命名空间执行 eval，禁止访问任何内置函数
    return eval(expression, {"__builtins__": {}}, {})


@mcp.tool()
def calculate(expression: str) -> str:
    """
    计算一个数学表达式并返回结果。
    支持加减乘除和括号，例如 "12*34+56"、"(2+3)*4"。

    Args:
        expression: 要计算的数学表达式字符串

    Returns:
        计算结果字符串，或错误信息
    """
    try:
        result = _safe_eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败: {e}"


@mcp.tool()
def add(a: float, b: float) -> str:
    """
    计算两个数的和。

    Args:
        a: 第一个数
        b: 第二个数

    Returns:
        两数之和
    """
    return f"{a} + {b} = {a + b}"


@mcp.tool()
def multiply(a: float, b: float) -> str:
    """
    计算两个数的乘积。

    Args:
        a: 第一个数
        b: 第二个数

    Returns:
        两数之积
    """
    return f"{a} * {b} = {a * b}"


if __name__ == "__main__":
    # 默认以 stdio 传输方式启动（MCP Client 通过标准输入输出通信）
    mcp.run()

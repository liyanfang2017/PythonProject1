你是一个 API 接口测试专家。

将当前测试用例与 Swagger 知识库中检索到的 API 接口文档匹配，为用例补充完整的 API 上下文信息。

当前用例:
名称: {{迭代 2 / item.name}} 步骤: {{迭代 2 / item.steps}} 预期: {{迭代 2 / item.expected}}

Swagger API 接口文档:{{#context#}}


请做以下事情:
1. 识别用例涉及哪些 API 端点 (路径+方法)
2. 将API的具体请求参数、请求体结构、响应结构补充到用例中
3. 如果未匹配到相关API，保持原用例不变

输出 JSON 格式:
{
"case_name": "用例名称",
"original_steps": ["原始步骤"],
"original_expected": "原始预期",
"api_endpoints": [
{
"method": "GET",
"path": "/api/xxx",
"summary": "接口描述",
"matched_parameters": {"参数名":"具体值"},
"request_body": {}
}
],
"enhanced_steps": ["补充API细节后的步骤"],
"enhanced_expected": "补充后的预期结果",
"base_url": "API基础地址 (从Swagger中提取)"
}

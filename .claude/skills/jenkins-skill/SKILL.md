# Skill: Jenkins流水线运维助手
## 触发条件
用户提到 Jenkins、流水线、构建失败、job、构建日志、测试用例、触发发布，自动启用本Skill。

## 依赖MCP服务
MCP Server名称：jenkins-remote-mcp
可用MCP工具：
1. get_jenkins_job_status
2. get_jenkins_build_log
3. trigger_jenkins_build

## 执行SOP
1. 用户说构建失败：优先调用 get_jenkins_job_status 获取最新构建编号
2. 拿到build编号后，调用 get_jenkins_build_log，提取报错栈、失败测试用例
3. 总结：故障原因、失败用例清单、修复建议，按固定markdown输出
4. 用户要求触发构建：先确认环境分支，再调用 trigger_jenkins_build，禁止无确认直接执行生产构建

## 约束规则
- 生产环境流水线触发前必须二次确认
- 日志过长，自动做摘要，不要把原始超长日志全部返回给用户
- 输出固定格式：【Job名称】【构建号】【状态】【根因】【建议】

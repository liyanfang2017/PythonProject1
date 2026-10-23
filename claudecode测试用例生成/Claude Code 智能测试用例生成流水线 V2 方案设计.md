# Claude Code 智能测试用例生成流水线 V2 方案设计

> 部分内容由豆包生成
> 
> 

# 背景与问题定义

## 现状痛点

当前测试用例主要依赖人工编写，存在三类问题：

1. 文档（PRD、接口文档、技术方案）到用例的转换依赖人工阅读与翻译，产出速度慢、质量因人而异；

2. 用例与需求、接口之间缺乏显式追溯关系，需求变更时难以判断影响范围，回归范围靠经验猜测；

3. AI 生成内容无人工把关则不可信，容易产生"生成即算数"的失控风险。

## 方案目标定位

本方案基于 Claude Code 构建一条可落地的测试用例生成流水线：以产品 PRD、接口文档、技术方案为输入，自动完成文档解析与测试用例生成，并通过知识关联图谱将"需求—接口—技术约束—测试用例"四类对象显式关联，同时在全流程设置多道人工确认门禁，最终格式化输出可交付产物。其中"知识关联图谱"在本方案中承担引擎角色，而非单纯的结果产物。

## 业界实践参照

业界智能测试实践呈现两个明确趋势：其一，知识图谱被用作前置建模的知识底座，支撑智能用例生成、覆盖缺口检测与变更影响分析，而不仅是末尾输出；其二，质量保障从"测试活动"升级为贯穿需求生命周期的洞察服务。本方案据此设计，将图谱前移、贯穿全流程。

# 目标与非目标

## 目标

|目标项|说明|
|---|---|
|自动化解析|自动解析 PRD、接口文档、技术方案，生成结构化中间产物（需求清单、接口清单、技术约束清单）|
|图谱驱动生成|知识图谱作为引擎贯穿全流程，驱动用例生成、覆盖缺口检测、追溯与影响分析|
|人工确认门禁|在文档理解、用例草稿、缺口补测、最终签发四处设置强制人工确认，Hook 硬性拦截不可跳过|
|格式化输出|输出测试用例规格说明书、可导入测试管理平台的用例库、追溯矩阵、图谱沉淀与汇总报告|

## 非目标

- 不替代人工评审：AI 仅产出草稿与建议，最终质量由人工把关；

- 不做代码级测试执行：本方案止步于用例生成与知识管理，不负责自动化测试执行与缺陷提交；

- 不追求一次覆盖全部需求：缺口允许标注"不测/存疑"，由人工决定。

# 总体架构

流水线以知识图谱引擎为中央知识底座，五个阶段围绕同一份图谱文件读写，人工确认门禁分布在关键阶段之间。

架构说明：所有阶段均围绕 work/graph\.json 读写。阶段一将文档实体化进图（建骨架）；阶段二读图做覆盖缺口检测并辅助生成；阶段三将确认结果回写图（追加用例节点与验证边）；阶段四直接消费图做追溯与影响分析；阶段五把图导出为多种格式沉淀为团队资产。

核心原则：图谱不是末尾才产出的交付物，而是从解析阶段就开始构建、贯穿全流程、持续演进的"引擎"。末尾的图谱导出只是引擎的沉淀快照。

# 知识图谱引擎设计

## 本体 Schema

节点类型（统一 ID 前缀，全流程稳定引用）：

|类型|ID 前缀|来源|示例|
|---|---|---|---|
|需求|REQ\-xxx|PRD|REQ\-003 创建订单|
|接口|API\-xxx|接口文档|API\-001 POST /api/v1/orders|
|技术约束|TECH\-xxx|技术方案|TECH\-002 订单状态机|
|测试用例|TC\-xxx|生成阶段|TC\-001 未登录创建订单返回 401|
|功能模块|MOD\-xxx|技术方案（可选）|MOD\-01 订单模块|

关系类型（边，带方向与语义）：

|关系|语义|用途|
|---|---|---|
|IMPLEMENTS|REQ → API|需求由哪些接口实现|
|DEPENDS\_ON|REQ → TECH / API → TECH|依赖的技术约束|
|CONSTRAINS|TECH → TC|约束被哪些用例覆盖|
|COVERS|API → TC|接口被用例覆盖|
|VALIDATES|REQ → TC|需求被用例验证|
|BELONGS\_TO|TC → MOD|用例归属模块|
|AFFECTS|MOD → API|模块变更波及接口（变更分析用）|

## 图谱生命周期

1. 构建：阶段一解析文档，生成 REQ / API / TECH 节点与 IMPLEMENTS / DEPENDS\_ON 边；

2. 确认：门禁 G1 人工确认图谱骨架与结构化文件；

3. 扩充：阶段二生成用例，追加 TC 节点与 COVERS / VALIDATES / CONSTRAINS 边；

4. 演进：阶段三把确认结果回写图，修正节点属性、补齐缺失边；

5. 沉淀：阶段五导出图谱快照（Mermaid / JSON / Cypher / 追溯矩阵）；

6. 复用：后续需求变更时沿图做影响分析，输出回归范围。

## 引擎三大能力

|能力|说明|
|---|---|
|覆盖缺口检测|遍历图中无 COVERS / VALIDATES 边的 REQ / API 节点，生成"未被覆盖"清单，驱动补充生成|
|变更影响分析|给定变更节点（如某需求改规则），沿边传播得到受影响接口与用例集合，输出回归范围建议|
|知识检索与上下文供给|生成与评审阶段，各子代理从图上取该需求/接口的完整上下文，保证精准知识、避免上下文污染|

# 详细流程与人工确认门禁

## 阶段 0 · 输入规范

```text
docs/
├── 01_prd/  PRD-2026-08-订单系统.md
├── 02_api/  api-order-v1.yaml
└── 03_tech/ 技术方案-订单状态机.md / 数据模型.md
```

约定：接口文档优先提供 OpenAPI/Swagger（字段级精确、机器可解析）；PRD 与技术方案为 Markdown 即可。

## 阶段 1 · 解析建模与图谱骨架

doc\-parser 与 graph\-engine 协同，产出：requirements\.json、api\_spec\.json、tech\_constraints\.json、graph\.json（图谱骨架）、parse\_report\.md（解析条目数、歧义点、缺失项清单）。

## 门禁 G1 · 需求/接口理解确认

目的：源头防偏——AI 对文档的理解必须经人工确认后才允许进入生成。确认对象为三个结构化文件、图谱骨架预览与解析报告；人工逐项标记"正确/修正"，补充缺失需求，澄清歧义。不通过则带修正意见回阶段 1 重解析。

## 阶段 2 · 图谱驱动用例生成

1. 读图取全部需求、接口、约束的完整上下文（引擎检索能力）；

2. 分层生成用例：功能用例、接口用例、业务规则用例、边界异常用例；

3. 每条用例必须携带 trace 追溯字段（对应图谱的边）；

4. 基于图谱做覆盖缺口检测，对无覆盖边的节点自动补生成建议用例。

## 门禁 G2 · 用例草稿确认（主门禁）

确认对象为每条用例（ID、标题、步骤、预期、追溯、优先级）。人工逐条给出"通过/修改/拒绝"并附意见，结果落盘到 gate 文件与评审清单。修改或拒绝的用例回阶段 2 定向重生成后再确认。

## 阶段 3 · 图谱演进与缺口补测

将确认通过的用例作为 TC 节点，连同 COVERS / VALIDATES 边回写 graph\.json；对缺口清单中"确认需补测"的节点触发补生成。

## 门禁 G3 · 覆盖缺口补测确认

缺口可能是"真漏测"也可能是"需求本身不需要测"，必须人工拍板。对每个未覆盖节点给出处理决定：补测 / 不测（注明原因）/ 需求存疑。处理后缺口归零或全部标注原因。

## 阶段 4 · 图谱应用

引擎价值显性出口：追溯查询（任意需求/接口查出全部关联用例）与影响分析预演（假设某需求变更，沿边输出受影响用例清单），产出影响分析预览文档，供评审与后续回归使用。

## 门禁 G4 · 最终产物签发

对全部最终产物（用例规格书、用例库、追溯矩阵、图谱沉淀、汇总报告）整体审核，签署版本号、评审人、日期。通过后正式发布。

## 阶段 5 · 格式化输出与图谱沉淀

产出测试用例规格说明书（Markdown）、用例库（xlsx，兼容 TestLink/Xray 导入）、图谱沉淀（graph\.mmd / graph\.json / graph\.cypher，Neo4j 可导入）、追溯矩阵、测试汇总报告。

## 门禁总览

|门禁|位置|确认对象|目的|产物|
|---|---|---|---|---|
|G1|解析建模后|结构化文件 \+ 图谱骨架 \+ 歧义清单|确保理解正确|gate\_g1\.json|
|G2|用例生成后|每条用例草稿|用例质量（主门禁）|gate\_g2\.json \+ 评审清单|
|G3|缺口补测后|未覆盖节点处理决定|缺口是否真缺|gate\_g3\.json|
|G4|输出前|全部最终产物|签发发布|gate\_g4\.json|

## 流程状态机

由 work/flow\_state\.json 记录当前阶段与已通过门禁，任何子代理与 Hook 均以此为准，防止跳步。

```text
PENDING ─G1─▶ G1_PASS ─G2─▶ G2_PASS ─G3─▶ G3_PASS ─G4─▶ RELEASED
   │失败           │失败           │失败           │失败
   └─▶回阶段1      └─▶回阶段2     └─▶回阶段3     └─▶回阶段5
```

门禁强制原则：Hook 由 Claude Code 运行时框架执行，模型无法绕过。即使以跳过权限模式运行，四道人工门禁依然生效。

# 接口、数据与状态设计

## 目录结构

```text
order-system/
├── CLAUDE.md
├── .claude/
│   ├── settings.json
│   ├── agents/
│   │   ├── doc-parser.yaml
│   │   ├── graph-engine.yaml
│   │   ├── test-case-generator.yaml
│   │   └── formatter.yaml
│   ├── commands/gen-tests.md
│   └── hooks/
│       ├── gate_check.sh
│       └── guard_bash.sh
├── docs/            # 输入文档
├── work/            # 中间产物 + 门禁文件 + 流程状态
│   ├── graph.json
│   ├── requirements.json / api_spec.json / tech_constraints.json
│   ├── testcases.draft.json
│   ├── gap_report.md / review_sheet.md
│   ├── flow_state.json
│   └── gate_g1.json ~ gate_g4.json
└── output/          # 最终交付 + 图谱沉淀
```

## 核心数据文件契约

图谱文件 graph\.json（图谱引擎唯一数据源，只增不改删）：

```json
{
  "version": "1.0",
  "nodes": [
    {"id": "REQ-003", "type": "Requirement", "title": "创建订单", "source": "docs/01_prd/..."},
    {"id": "API-001", "type": "Api", "method": "POST", "path": "/api/v1/orders"},
    {"id": "TECH-002", "type": "TechConstraint", "title": "订单状态机"},
    {"id": "TC-001", "type": "TestCase", "title": "未登录创建订单返回401"}
  ],
  "edges": [
    {"from": "REQ-003", "to": "API-001", "type": "IMPLEMENTS"},
    {"from": "REQ-003", "to": "TECH-002", "type": "DEPENDS_ON"},
    {"from": "API-001", "to": "TC-001", "type": "COVERS"},
    {"from": "REQ-003", "to": "TC-001", "type": "VALIDATES"}
  ]
}
```

用例草稿 testcases\.draft\.json（每条用例的追溯字段即图谱的边）：

```json
{
  "id": "TC-001",
  "title": "未登录用户创建订单返回401",
  "type": "接口/异常",
  "priority": "P1",
  "precondition": "无有效登录态",
  "steps": ["POST /api/v1/orders", "body: {}"],
  "expected": "HTTP 401, code=UNAUTHORIZED",
  "trace": {"req": ["REQ-003"], "api": ["API-001"], "tech": []},
  "status": "draft"
}
```

门禁文件 gate\_gN\.json（人工确认落盘）：

```json
{
  "approved": true,
  "reviewer": "张三",
  "reviewed_at": "2026-08-26T15:30:00+08:00",
  "decisions": {
    "TC-001": {"verdict": "pass", "comment": ""},
    "TC-002": {"verdict": "modify", "comment": "补充403场景"}
  }
}
```

流程状态 flow\_state\.json：

```json
{"stage": "stage2", "gates_passed": ["G1"]}
```

## CLAUDE\.md 项目记忆

```markdown
# 测试用例生成工程规范
## 文档约定
- 输入文档放 docs/：01_prd、02_api、03_tech
- 接口文档优先 OpenAPI/YAML
## ID 编码规则
- 需求 REQ-xxx / 接口 API-xxx / 技术约束 TECH-xxx / 用例 TC-xxx / 模块 MOD-xxx
## 强制规则
- 所有用例必须带 trace 追溯字段
- 图谱 graph.json 是唯一知识底座，任何阶段只增不改删
- 未经 gate_g1~gate_g4 确认，不得进入下一阶段
## 命令
- /gen-tests 一键执行全流水线
```

## Subagent 定义

graph\-engine\.yaml（图谱引擎，本方案核心子代理）：

```yaml
name: graph-engine
description: 知识图谱引擎。负责读取/维护 work/graph.json：从结构化文件建骨架、
  追加TC节点与边、覆盖缺口检测、变更影响分析、导出 Mermaid/JSON/Cypher/追溯矩阵。
  任何阶段不得删除已有节点。
tools: Read, Write, Glob, Grep, Bash
model: inherit
```

其余三个子代理同构定义：doc\-parser（只读文档 \+ 写 work 结构化文件）、test\-case\-generator（读图生成用例草稿）、formatter（读确认后产物 \+ 写 output）。每个子代理通过系统提示词、工具权限与独立上下文实现角色焊定。

## Hooks 与门禁脚本

settings\.json 注册门禁 Hook：

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "Write(**/*.json)",
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/gate_check.sh",
        "timeout": 10
      }]
    }]
  }
}
```

gate\_check\.sh（按当前阶段校验对应门禁，非 0 退出即拦截）：

```bash
#!/bin/bash
state=$(jq -r '.stage' work/flow_state.json)
case "$state" in
  stage1) need="gate_g1";;
  stage2) need="gate_g2";;
  stage3) need="gate_g3";;
  stage5) need="gate_g4";;
  *) exit 0;;
esac
approved=$(jq -r '.approved' "work/${need}.json" 2>/dev/null)
if [ "$approved" != "true" ]; then
  echo "门禁 ${need} 未通过，禁止进入下一阶段，请人工确认" >&2
  exit 1
fi
exit 0
```

## 一键命令

\.claude/commands/gen\-tests\.md：

```markdown
---
description: 全流程：解析建图→图谱驱动生成→人工门禁(G1-G4)→图谱应用→格式化输出
---
依次执行，每阶段严格遵守 flow_state.json 与门禁：
1. doc-parser 解析 docs/，graph-engine 建图谱骨架，产出结构化文件与 parse_report.md
2. 停下等【门禁G1】人工确认理解正确
3. test-case-generator 读图生成用例 + 缺口检测
4. 停下等【门禁G2】逐条确认用例
5. graph-engine 回写确认结果；对缺口触发补生成
6. 停下等【门禁G3】确认缺口处理
7. graph-engine 做追溯查询与影响分析预演
8. formatter 产出全部最终产物
9. 停下等【门禁G4】签发
10. graph-engine 导出图谱沉淀快照 + 追溯矩阵，流程结束
```

## 启动方式

```bash
# 交互式（推荐，便于人工确认介入）
claude
# 会话内触发
/gen-tests
# headless 无人值守（门禁仍强制人工，适合 CI 编排）
claude -p "运行 /gen-tests" --output-format json
```

# 失败、安全与兼容

## 门禁防绕过

Hook 由 Claude Code 运行时框架执行，不依赖模型判断，即使以 \-\-dangerously\-skip\-permissions 启动依然生效，人工确认成为硬性前置条件，无法被 AI 跳过。

## 权限与安全

- 原始文档只读保护：PreToolUse Hook 拦截对 docs/ 目录的 Write/Edit；

- 危险命令护栏：拦截 rm \-rf、git push 等高风险操作；

- 子代理权限最小化：doc\-parser 等只授予读取与指定目录写入权限。

## 兼容与迁移

- 接口文档兼容 OpenAPI、YAML、Markdown 三种形态，解析层输出缺失项清单；

- 图谱格式兼容 Neo4j 导入（Cypher），可平滑迁移到 NebulaGraph 等图数据库；

- 输出用例库兼容 TestLink / Xray 导入模板，可对接主流测试管理平台。

# 上线、回滚与验收

## 落地里程碑

|周期|里程碑|
|---|---|
|第 1 周|目录骨架 \+ CLAUDE\.md \+ 四个子代理 \+ graph\-engine 建图/检索跑通，门禁 G1 落地|
|第 2 周|图谱驱动生成 \+ 缺口检测，门禁 G2/G3 落地（评审清单 \+ 门禁文件 \+ Hook）|
|第 3 周|影响分析预演 \+ 图谱四格式导出 \+ 门禁 G4 签发 \+ 质量校验脚本，整体联调试点|

## 质量校验

|校验项|方法|触发点|
|---|---|---|
|图谱一致性|边引用的节点必须存在，否则报错|每次 graph\.json 写入后|
|用例可追溯性|TC 的 trace 必须命中图中节点|门禁 G2 前|
|覆盖度真实性|缺口清单 = 图中无覆盖边的 REQ/API|门禁 G3 前|
|门禁完整性|四个门禁文件齐全且 approved 为 true|门禁 G4 后|
|文档只读|PreToolUse 拦截 docs/ 目录写入|全程|

## 验收标准

- 以一个小型模块（如订单创建）为试点，完整跑通五阶段与四道门禁；

- 输出物齐全：用例规格书、用例库 xlsx、图谱四格式沉淀、追溯矩阵、汇总报告；

- 每条用例可沿图谱追溯到对应需求与接口，覆盖缺口清单全部有处理决定；

- 跳过任意门禁即流程终止，可验证人工确认不可绕过。

## 回滚策略

流水线为纯文件式本地操作，不涉及线上系统变更。回滚方式：恢复上一版本中间产物目录，重新执行对应阶段；图谱与门禁文件均在 work/ 下可版本管理，任何阶段可安全回到前一确认点。

# 风险与未决决定

## 风险清单

|风险|对策|
|---|---|
|图谱节点/关系抽取错误|门禁 G1 强制确认图谱骨架；G2/G3 回写边前做一致性校验|
|人工确认流于形式|四道硬门禁 \+ 逐条 verdict \+ 评审留痕可审计|
|图谱数据膨胀失控|按模块分图维护 \+ 边类型收敛到七种|
|长文档超上下文窗口|分块解析落结构化文件，子代理只读图与文件，不读全文|

## 未决决定

- 知识关联图谱的最终落库形态：文件快照先行，还是直接引入 Neo4j 图数据库；

- 是否在后续版本接入 CI 与测试管理平台双向同步（MCP 对接 TestLink/Xray）；

- 四类子代理的模型档位选择（默认继承主模型，可按成本调整）。

> （注：部分内容可能由 AI 生成）

---
name: api-test-pipeline
description: >
  需求+API用例生成全流程。从用户需求描述或测试用例出发，自动解析Swagger/OpenAPI文档，
  为每个用例匹配并补充API上下文，最终生成可执行的pytest测试脚本。
  当用户说"根据需求生成接口测试"、"帮我把这个需求转成API测试用例"、
  "用swagger生成测试"、"需求转pytest"、"接口用例生成"、"API测试全流程"时必须使用。
  支持两种输入模式：(1)纯需求描述 → 自动生成用例+脚本 (2)已有测试用例 → 补充API上下文+生成脚本。
---

# 需求+API用例生成全流程

## 流程概览

```text
用户输入 (需求描述 或 已有测试用例 + Swagger文档)
  │
  ▼
┌─ Step 1: 分类输入 ──────────────────────────────────┐
│  判断用户输入是否包含"测试步骤+预期结果"结构          │
│  → 有case: 提取结构化用例                             │
│  → 无case: 纯需求描述，后续用LLM生成用例              │
└──────────────────────────────────────────────────────┘
  │
  ▼
┌─ Step 2: 解析 Swagger → JSON ──────────────────────┐
│  python3 scripts/swagger_parser.py swagger.json      │
│  输出: endpoints.json（结构化端点列表，保留完整字段）  │
└──────────────────────────────────────────────────────┘
  │
  ▼
┌─ Step 3: 检索相关端点 ─────────────────────────────┐
│  python3 scripts/search_endpoints.py endpoints.json   │
│    --path user --method POST --tag 用户管理           │
│  只取与需求相关的端点，避免全量喂给 LLM               │
└──────────────────────────────────────────────────────┘
  │
  ▼
┌─ Step 4: 用例生成/提取 ─────────────────────────────┐
│  无case分支: LLM根据需求+检索到的端点生成测试用例     │
│  有case分支: 直接使用用户提供的用例                    │
└──────────────────────────────────────────────────────┘
  │
  ▼
┌─ Step 5: Swagger上下文补充 ─────────────────────────┐
│  逐用例匹配API端点，补充请求参数、请求体、响应结构    │
│  使用 search_endpoints.py 按路径精确检索              │
└──────────────────────────────────────────────────────┘
  │
  ▼
┌─ Step 6: 生成 pytest 脚本 ─────────────────────────┐
│  LLM 根据 enriched cases + Swagger 端点信息          │
│  直接生成可执行的 pytest 脚本                         │
│  → references/prompts.md#generate_pytest             │
└──────────────────────────────────────────────────────┘
  │
  ▼
用户获得: test_{project}.py（可直接 pytest -v 运行）
```

## 执行步骤

### Step 1: 确认输入

与用户确认：

1. **用户输入** — 需求描述文本 或 已有测试用例（步骤+预期结果）
2. **Swagger 文档** — JSON/YAML 文件路径、URL、或直接粘贴内容（必需）
3. **Base URL** — 可选，默认 `http://localhost:8000`
4. **认证信息** — 可选（login接口 / API Key / Basic Auth）
5. **项目名称** — 可选，用于命名输出文件

### Step 2: 分类用户输入

```bash
python3 scripts/case_classifier.py --input "用户输入内容" --json
```

输出格式：
```json
{
  "has_case": false,
  "query": "纯需求描述",
  "cases": []
}
```

**分支逻辑**：
- `has_case=false` → 进入 Step 4a（需求生成用例）
- `has_case=true` → 进入 Step 4b（直接使用用例）

### Step 3: 解析 Swagger → JSON

**关键：先输出 JSON，保留结构化数据，后续检索和 LLM 都用 JSON。**

```bash
# 解析 Swagger 输出结构化 JSON
python3 scripts/swagger_parser.py swagger.json > endpoints.json
```

输出示例：
```json
[
  {
    "path": "/api/users",
    "method": "GET",
    "summary": "获取用户列表",
    "tags": ["用户管理"],
    "parameters": [{"name": "page", "in": "query", "type": "integer", "required": false}],
    "request_body": null,
    "responses": {"200": {"type": "array", "items": {"$ref": "#/User"}}},
    "security": [{"Bearer": []}],
    "base_url": "http://localhost:8000"
  }
]
```

解析完成后打印摘要：
```bash
python3 scripts/search_endpoints.py endpoints.json --summary-only
```

### Step 4: 检索相关端点

**用 search_endpoints.py 做跨平台检索（替代 grep/jq，Windows/Mac/Linux 通用）。**

```bash
# 按路径关键词检索
python3 scripts/search_endpoints.py endpoints.json --path user

# 按方法+标签组合检索
python3 scripts/search_endpoints.py endpoints.json --method POST --tag 用户

# 按参数名检索
python3 scripts/search_endpoints.py endpoints.json --param petId

# 仅获取有请求体的端点
python3 scripts/search_endpoints.py endpoints.json --method POST --has-body

# 输出 Markdown 喂给 LLM
python3 scripts/search_endpoints.py endpoints.json --path user --markdown
```

支持的检索参数：
| 参数 | 说明 | 示例 |
|------|------|------|
| `--path` | 路径关键词（模糊） | `--path user` |
| `--method` | HTTP方法（精确） | `--method POST` |
| `--tag` | 标签关键词（模糊） | `--tag 用户` |
| `--param` | 参数名关键词（模糊） | `--param petId` |
| `--summary` | 描述关键词（模糊） | `--summary 登录` |
| `--has-body` | 仅返回有请求体的端点 | `--has-body` |
| `--no-auth` | 仅返回不需要认证的端点 | `--no-auth` |
| `--limit` | 限制返回数量 | `--limit 10` |
| `--markdown` | 输出Markdown格式 | `--markdown` |

### Step 5: 用例生成/提取

#### 5a: 无case分支 — LLM生成用例

将需求 + 检索到的相关端点 JSON 喂给 LLM：

```
用户需求: {requirement}

相关 API 端点（已检索）:
{search_results_json}

→ 使用 references/prompts.md#generate_from_requirement
→ LLM 输出结构化测试用例
```

#### 5b: 有case分支 — 直接使用用例

直接使用 Step 2 提取的 `cases` 列表。

### Step 6: Swagger 上下文补充

对每个用例，用 search_endpoints.py 精确匹配相关端点：

```bash
# 按用例涉及的路径精确检索
python3 scripts/search_endpoints.py endpoints.json --path "/api/users" --method GET
```

然后使用 `references/prompts.md#enrich` 让 LLM 补充 API 上下文。

### Step 7: LLM 生成 pytest 脚本

将 Step 6 输出的 enriched cases（已包含完整 API 上下文）+ 相关 Swagger 端点信息喂给 LLM，
使用 `references/prompts.md#generate_pytest` prompt 模板，直接生成可执行的 pytest 脚本。

```markdown
→ LLM 输入：
   - enriched_cases_json: {enriched_cases}
   - endpoints_json: {相关 Swagger 端点完整定义}
   - auth_type: {认证类型}
   - base_url: {Base URL}

→ 使用 references/prompts.md#generate_pytest

→ LLM 输出：完整的 test_{project}.py（纯 Python 代码，无 markdown 包裹）
```

### Step 8: 验证

```bash
python3 -m py_compile test_api.py
pytest test_api.py --collect-only
```

## 脚本引用

| 脚本 | 用途 | 跨平台 |
|------|------|--------|
| `scripts/swagger_parser.py` | Swagger → JSON（结构化端点） | ✅ |
| `scripts/search_endpoints.py` | JSON 端点检索（替代 grep/jq） | ✅ |
| `scripts/case_classifier.py` | 输入分类（有/无case） | ✅ |

## Prompt 引用

LLM 调用使用的完整 Prompt 模板见 `references/prompts.md`。

## 使用示例

### 示例 1: 纯需求 + Swagger

```
用户: "帮我根据这个需求生成接口测试用例，swagger.json 在项目根目录"

→ python3 scripts/case_classifier.py -i "帮我测试用户管理" --json
  → has_case=false

→ python3 scripts/swagger_parser.py swagger.json > endpoints.json
→ python3 scripts/search_endpoints.py endpoints.json --summary-only
  → 发现 23 个端点

→ python3 scripts/search_endpoints.py endpoints.json --path user --markdown
  → 检索到 5 个用户相关端点，喂给 LLM

→ LLM 生成测试用例
→ python3 scripts/search_endpoints.py endpoints.json --path "/api/users" --method GET
  → 精确匹配端点，补充 API 上下文

→ LLM 根据 enriched cases + Swagger 端点信息生成 pytest 脚本
  → references/prompts.md#generate_pytest
→ 输出 test_api.py
```

### 示例 2: 已有用例 + Swagger

```
用户: "用例：1.登录获取token 2.查询用户列表 3.验证返回正确。swagger文档在./swagger.json"

→ 分类: has_case=true, 提取3条用例
→ 解析 swagger → endpoints.json
→ 逐用例检索匹配端点 + LLM 补充上下文
→ 生成 test_api.py
```

## 验证清单

- [ ] 生成的 .py 语法正确（`python3 -m py_compile`）
- [ ] pytest 可正常收集用例（`pytest --collect-only`）
- [ ] 每个端点至少覆盖正常+异常场景
- [ ] 认证逻辑正确（bearer/apikey/basic）
- [ ] Swagger 的 $ref 已全部解析
- [ ] 请求参数/请求体/响应结构已补充到用例中
- [ ] 检索结果数量合理（不是全量端点）

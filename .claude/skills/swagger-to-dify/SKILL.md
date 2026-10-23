---
name: swagger-to-dify
description: >
  Swagger/OpenAPI 文档 → Dify 知识库 Markdown 预处理。
  将 Swagger JSON/YAML 解析为段落清晰的 Markdown 文档（$ref 已递归展开、allOf 已合并），
  支持一键上传至 Dify 知识库。
  当用户说"把 swagger 转成知识库文档"、"生成 Dify 知识库 md"、"swagger 转 markdown" 时使用。
---

# Swagger → Dify 知识库预处理

## 用途

将 Swagger/OpenAPI 文档解析为适合导入 Dify 知识库的 Markdown 文档：

- ✅ `$ref` 递归展开（最大 8 层），allOf 合并，oneOf/anyOf 取首项
- ✅ 嵌套 Schema 渲染为 Markdown **表格**（字段名、类型、必填、描述），支持 3 层递归
- ✅ 请求体结构 + JSON 示例
- ✅ 响应体 Schema（每状态码）+ JSON 示例
- ✅ 响应头信息
- ✅ 鉴权方式说明
- ✅ 自定义分段格式（`## METHOD /path` 为分隔符，Dify 按端点分段）
- ✅ 可选：通过 Dify API 自动上传知识库

对比 `swagger_parser.py --markdown`，此脚本生成的 Markdown **信息密度更高**：
- Schema 用表格呈现而非纯 JSON
- 嵌套对象递归展开为子表格
- 响应按状态码分别展示
- 包含安全方案说明

## 用法

```bash
# 当前目录执行
python3 scripts/swagger_to_knowledge.py petclin.json -o ./output/

# 单文件模式（推荐 Dify 用）
python3 scripts/swagger_to_knowledge.py petclin.json --single-file -o ./output/

# 生成 + 自动上传到 Dify 知识库
python3 scripts/swagger_to_knowledge.py petclin.json \
  --dify-base-url http://localhost:4800 \
  --dify-api-key dataset-xxx \
  --dify-dataset-id xxx
```

## 参数

| 参数 | 说明 |
|------|------|
| `swagger` | Swagger JSON/YAML 文件路径（必需） |
| `-o, --output` | 输出目录，默认 `./swagger_knowledge/` |
| `--single-file` | 合并为单文件 `swagger_docs.md`（Dify 推荐） |
| `--dify-base-url` | Dify 服务地址 |
| `--dify-api-key` | Dify Dataset API Key |
| `--dify-dataset-id` | Dify 知识库 Dataset ID |

## 输出说明

### 单文件模式（`--single-file`）

输出 `swagger_docs.md`，每个端点以 `## METHOD /path` 分段：

```markdown
# Swagger API 接口文档（知识库版）

共 49 个端点 | 方法: GET, POST, PUT, ... | 标签: owner, pet, visit, ...

---

## GET /petclinic/api/owners

**描述**: Lists pet owners
**基础地址**: `https://spring-petclinic-rest.k8s.hogwarts.ceshiren.com:443`
**标签**: owner

**请求参数**:
| 参数名 | 位置 | 类型 | 必填 | 描述 |
|--------|------|------|------|------|
| lastName | query | string | 否 | Last name. |

**响应**:
**200 OK**
响应体 (`application/json`):
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 否 | |
| firstName | string | 否 | |
| ...
```

### 多文件模式（`--single-file` 不指定时）

每个端点一个 `.md` 文件 + `_index.md` 索引文件，适合按端点分别上传。

## Dify 导入建议

1. **创建知识库** → 选择"导入已有文档"
2. **分段策略** → 选择"自定义"，分隔符设为 `\n## `（按端点分段）
3. **检索方式** → 推荐"向量检索"

## 上传到 Dify

指定 `--dify-*` 参数时会自动：
1. 生成 Markdown（强制单文件模式）
2. 通过 Dify Dataset API 上传文档
3. 等待索引完成

```bash
python3 scripts/swagger_to_knowledge.py petclin.json \
  --dify-base-url http://localhost:4800 \
  --dify-api-key app-xxxxxxxxxxxxxxxx \
  --dify-dataset-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 效果对比

对比 `swagger_parser.py --markdown`，此脚本的 Markdown 输出多了：

| swagger_parser.py | swagger_to_knowledge.py |
|---|---|
| JSON 示例展示 | Schema 表格 + JSON 示例 |
| 无嵌套表格 | 3 层递归嵌套表格 |
| 无响应头 | 含响应头信息 |
| 无鉴权说明 | 含鉴权方式说明 |
| 无 Dify 上传 | 支持自动上传 |

## 脚本引用

| 脚本 | 用途 |
|------|------|
| `scripts/swagger_to_knowledge.py` | Swagger → Markdown（含 Dify 上传） |

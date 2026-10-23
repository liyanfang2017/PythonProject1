#!/usr/bin/env python3
"""
Swagger/OpenAPI 解析器
支持 Swagger 2.0 和 OpenAPI 3.x，解析 $ref、allOf，输出结构化端点列表和 Markdown 文档。

用法:
    # 解析并输出JSON
    python swagger_parser.py petstore.json

    # 解析并输出Markdown
    python swagger_parser.py petstore.json --markdown -o ./output/

    # 从URL解析
    python swagger_parser.py https://petstore.swagger.io/v2/swagger.json
"""
import json
import os
import sys
import argparse
import urllib.request
import urllib.error


def parse(swagger_source: str) -> list[dict]:
    """解析 Swagger/OpenAPI 文档，返回端点列表。"""
    raw = _load(swagger_source)
    spec = _parse_spec(raw)
    version = _detect_version(spec)
    base_url = _extract_base_url(spec, version)

    endpoints = []
    for path, methods in spec.get('paths', {}).items():
        for method in ('get', 'post', 'put', 'delete', 'patch', 'head', 'options'):
            if method not in methods:
                continue
            detail = methods[method]
            if isinstance(detail, dict) and '$ref' in detail:
                detail = _resolve_ref(detail['$ref'], spec)

            ep = {
                'path': path,
                'method': method.upper(),
                'summary': detail.get('summary', '') or detail.get('description', ''),
                'operation_id': detail.get('operationId', ''),
                'tags': detail.get('tags', []),
                'parameters': _extract_params(detail, spec),
                'request_body': _extract_body(detail, spec, version),
                'responses': _extract_responses(detail, spec),
                'security': detail.get('security', spec.get('security', [])),
                'deprecated': detail.get('deprecated', False),
                'base_url': base_url,
            }
            endpoints.append(ep)

    return endpoints


def to_markdown(endpoints: list[dict]) -> str:
    """将端点列表渲染为 Markdown 文档。"""
    lines = ["# API 接口文档\n"]
    lines.append(f"> 自动生成，共 {len(endpoints)} 个端点\n")

    # 按 tag 分组
    grouped = {}
    for ep in endpoints:
        tag = ep['tags'][0] if ep['tags'] else '未分类'
        grouped.setdefault(tag, []).append(ep)

    for tag, eps in grouped.items():
        lines.append(f"\n## {tag}\n")
        for ep in eps:
            lines.append(_render_endpoint_md(ep))

    return '\n'.join(lines)


def summary(endpoints: list[dict]) -> dict:
    """生成端点的概要统计。"""
    methods = {}
    tags = {}
    for ep in endpoints:
        methods[ep['method']] = methods.get(ep['method'], 0) + 1
        for t in ep['tags']:
            tags[t] = tags.get(t, 0) + 1
    return {
        'total': len(endpoints),
        'methods': methods,
        'tags': tags,
        'has_auth': any(ep['security'] for ep in endpoints),
        'has_deprecated': any(ep['deprecated'] for ep in endpoints),
        'has_path_params': any(
            any(p['in'] == 'path' for p in ep['parameters'])
            for ep in endpoints
        ),
    }


# ─── 内部函数 ───

def _load(source: str) -> str:
    """加载 Swagger 内容：文件路径、URL、或直接JSON字符串。"""
    # 尝试作为URL
    if source.startswith('http://') or source.startswith('https://'):
        try:
            req = urllib.request.Request(source, headers={'User-Agent': 'swagger-parser/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except Exception as e:
            print(f"[WARN] 无法从URL获取: {e}", file=sys.stderr)
            return source

    # 尝试作为文件路径
    if os.path.isfile(source):
        with open(source, encoding='utf-8') as f:
            return f.read()

    # 直接作为内容
    return source


def _parse_spec(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith('{') or cleaned.startswith('['):
        return json.loads(cleaned)
    try:
        import yaml
        return yaml.safe_load(cleaned)
    except ImportError:
        return json.loads(cleaned)


def _detect_version(spec: dict) -> str:
    if 'openapi' in spec:
        return spec['openapi']
    if 'swagger' in spec:
        return spec['swagger']
    return 'unknown'


def _extract_base_url(spec: dict, version: str) -> str:
    """从 spec 中提取 base URL。"""
    if version.startswith('2'):
        host = spec.get('host', 'localhost')
        basePath = spec.get('basePath', '/')
        schemes = spec.get('schemes', ['https'])
        scheme = schemes[0] if schemes else 'https'
        return f"{scheme}://{host}{basePath}"
    else:
        servers = spec.get('servers', [])
        if servers:
            return servers[0].get('url', 'http://localhost')
        return 'http://localhost'


def _resolve_ref(ref: str, spec: dict, depth: int = 0) -> dict:
    if not ref or depth > 8:
        return {}
    parts = ref.lstrip('#/').split('/')
    cur = spec
    for part in parts:
        if isinstance(cur, dict):
            cur = cur.get(part, {})
        else:
            return {}
    if isinstance(cur, dict) and '$ref' in cur and depth < 8:
        return _resolve_ref(cur['$ref'], spec, depth + 1)
    return cur


def _normalize_schema(node: dict, spec: dict, depth: int = 0) -> dict:
    """递归规范化 schema：展开 $ref、合并 allOf、处理 oneOf/anyOf。"""
    if not isinstance(node, dict) or depth > 8:
        return node if isinstance(node, dict) else {}

    node = dict(node)

    # 1. Resolve $ref
    if '$ref' in node:
        resolved = dict(_resolve_ref(node['$ref'], spec))
        for key in ('description', 'example', 'nullable', 'deprecated', 'readOnly', 'writeOnly', 'title'):
            if key in node and key not in resolved:
                resolved[key] = node[key]
        node = resolved

    # 2. Merge allOf
    if 'allOf' in node:
        merged = {}
        for item in node['allOf']:
            item = _normalize_schema(item, spec, depth + 1)
            if isinstance(item, dict):
                for k, v in item.items():
                    if k == 'properties' and isinstance(v, dict):
                        merged.setdefault('properties', {}).update(v)
                    elif k == 'required' and isinstance(v, list):
                        merged.setdefault('required', []).extend(v)
                    else:
                        merged[k] = v
        for k, v in node.items():
            if k != 'allOf':
                merged[k] = v
        node = merged

    # 3. oneOf / anyOf → 取第一个
    for key in ('oneOf', 'anyOf'):
        if key in node:
            options = node[key]
            if options:
                first = _normalize_schema(options[0], spec, depth + 1)
                node = {**node, **first}
            del node[key]

    # 4. 递归处理 properties / items
    if 'properties' in node:
        node['properties'] = {
            k: _normalize_schema(v, spec, depth + 1)
            for k, v in node['properties'].items()
        }
    if 'items' in node and isinstance(node['items'], dict):
        node['items'] = _normalize_schema(node['items'], spec, depth + 1)

    return node


def _extract_params(detail: dict, spec: dict) -> list[dict]:
    params = []
    for p in detail.get('parameters', []):
        if '$ref' in p:
            p = _resolve_ref(p['$ref'], spec)
        schema = p.get('schema', {})
        if isinstance(schema, dict):
            schema = _normalize_schema(schema, spec)
        params.append({
            'name': p.get('name', ''),
            'in': p.get('in', 'query'),
            'type': schema.get('type', 'string'),
            'required': p.get('required', False),
            'description': p.get('description', ''),
            'enum': schema.get('enum'),
            'example': schema.get('example'),
            'default': schema.get('default'),
            'format': schema.get('format', ''),
        })
    return params


def _extract_body(detail: dict, spec: dict, version: str) -> dict | None:
    if version.startswith('2'):
        for p in detail.get('parameters', []):
            if '$ref' in p:
                p = _resolve_ref(p['$ref'], spec)
            if p.get('in') == 'body':
                schema = p.get('schema', {})
                if isinstance(schema, dict):
                    schema = _normalize_schema(schema, spec)
                return schema
        return None

    body = detail.get('requestBody', {})
    if '$ref' in body:
        body = _resolve_ref(body['$ref'], spec)
    content = body.get('content', {})
    for ct in ('application/json', '*/*'):
        if ct in content:
            schema = content[ct].get('schema', {})
            if isinstance(schema, dict):
                schema = _normalize_schema(schema, spec)
            return schema
    for ct, val in content.items():
        schema = val.get('schema', {})
        if isinstance(schema, dict):
            schema = _normalize_schema(schema, spec)
        return schema
    return None


def _extract_responses(detail: dict, spec: dict) -> dict:
    responses = {}
    for code, resp in detail.get('responses', {}).items():
        if '$ref' in resp:
            resp = _resolve_ref(resp['$ref'], spec)
        content = resp.get('content', {})
        if not content:
            # Swagger 2.0 可能直接有 schema
            schema = resp.get('schema', {})
            if isinstance(schema, dict) and schema:
                schema = _normalize_schema(schema, spec)
                responses[code] = schema
            continue
        for ct in ('application/json', '*/*'):
            if ct in content:
                schema = content[ct].get('schema', {})
                if isinstance(schema, dict):
                    schema = _normalize_schema(schema, spec)
                responses[code] = schema
                break
    return responses


def _render_endpoint_md(ep: dict) -> str:
    """渲染单个端点为 Markdown。"""
    lines = []
    lines.append(f"\n### `{ep['method']}` {ep['path']}\n")
    if ep['summary']:
        lines.append(f"**{ep['summary']}**\n")
    if ep['deprecated']:
        lines.append("> **DEPRECATED**\n")
    if ep['operation_id']:
        lines.append(f"- OperationId: `{ep['operation_id']}`\n")

    # Parameters
    if ep['parameters']:
        lines.append("\n**Parameters:**\n")
        lines.append("| Name | In | Type | Required | Description |")
        lines.append("|------|-----|------|----------|-------------|")
        for p in ep['parameters']:
            req = "Yes" if p['required'] else "No"
            lines.append(f"| `{p['name']}` | {p['in']} | {p['type']} | {req} | {p.get('description', '')} |")

    # Request Body
    if ep['request_body']:
        lines.append("\n**Request Body (application/json):**\n")
        lines.append("```json")
        lines.append(json.dumps(_schema_to_example(ep['request_body']), indent=2, ensure_ascii=False))
        lines.append("```\n")

    # Responses
    if ep['responses']:
        lines.append("\n**Responses:**\n")
        for code, schema in ep['responses'].items():
            lines.append(f"- `{code}`:")
            if schema:
                lines.append("  ```json")
                lines.append(f"  {json.dumps(_schema_to_example(schema), indent=2, ensure_ascii=False)}")
                lines.append("  ```")
        lines.append("")

    # Security
    if ep['security']:
        lines.append("\n**Security:**\n")
        for s in ep['security']:
            if isinstance(s, dict):
                for scheme in s.keys():
                    lines.append(f"- `{scheme}`")
            else:
                lines.append(f"- `{s}`")
        lines.append("")

    return '\n'.join(lines)


def _schema_to_example(schema: dict, depth: int = 0) -> any:
    """将 schema 转换为示例值。"""
    if not schema or depth > 5:
        return {}

    if 'example' in schema:
        return schema['example']

    t = schema.get('type', 'object')
    if t == 'object':
        result = {}
        for name, prop in schema.get('properties', {}).items():
            result[name] = _schema_to_example(prop, depth + 1)
        return result if result else {}
    elif t == 'array':
        items = schema.get('items', {})
        return [_schema_to_example(items, depth + 1)] if items else []
    elif t == 'string':
        if schema.get('enum'):
            return schema['enum'][0]
        fmt = schema.get('format', '')
        if fmt == 'date':
            return '2024-01-01'
        elif fmt == 'date-time':
            return '2024-01-01T00:00:00Z'
        elif fmt == 'email':
            return 'test@example.com'
        elif fmt == 'uri':
            return 'https://example.com'
        return 'string'
    elif t == 'integer':
        return 0
    elif t == 'number':
        return 0.0
    elif t == 'boolean':
        return True
    return {}


def _print_summary(endpoints: list[dict]):
    s = summary(endpoints)
    print(f"\n=== Swagger 解析完成 ===", file=sys.stderr)
    print(f"总端点数: {s['total']}", file=sys.stderr)
    print(f"方法分布: {s['methods']}", file=sys.stderr)
    print(f"标签分类: {s['tags']}", file=sys.stderr)
    print(f"需要认证: {'是' if s['has_auth'] else '否'}", file=sys.stderr)
    print(f"已弃用接口: {s['has_deprecated']}", file=sys.stderr)
    print(f"路径参数: {'有' if s['has_path_params'] else '无'}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Swagger/OpenAPI 解析器')
    parser.add_argument('source', help='Swagger文件路径、URL、或JSON字符串')
    parser.add_argument('--markdown', '-m', action='store_true', help='输出Markdown格式')
    parser.add_argument('--output', '-o', help='输出目录（Markdown模式）')
    parser.add_argument('--quiet', '-q', action='store_true', help='不输出摘要到stderr')
    args = parser.parse_args()

    endpoints = parse(args.source)
    if not args.quiet:
        _print_summary(endpoints)

    if args.markdown:
        md = to_markdown(endpoints)
        if args.output:
            os.makedirs(args.output, exist_ok=True)
            out_path = os.path.join(args.output, 'swagger_docs.md')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"\nMarkdown 已写入: {out_path}", file=sys.stderr)
        else:
            print(md)
    else:
        print(json.dumps(endpoints, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

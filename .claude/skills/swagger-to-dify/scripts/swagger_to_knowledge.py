"""
Swagger → Dify知识库 预处理脚本

用法:
    # 本地生成
    python swagger_to_knowledge.py petstore.json -o ./swagger_knowledge/
    python swagger_to_knowledge.py petstore.json --single-file -o swagger_docs.md

    # 生成 + 自动上传 Dify 知识库
    python swagger_to_knowledge.py petstore.json \\
        --dify-base-url http://localhost:4800 \\
        --dify-api-key dataset-xxx \\
        --dify-dataset-id xxx

输出: Markdown格式API文档，$ref已解析，allOf已合并。
配合 --dify-* 参数可自动上传至 Dify 知识库（启用向量检索）。
"""
import json
import os
import argparse
import time
import urllib.parse
import urllib.request
import urllib.error


def process(swagger_path: str, output_dir: str, single_file: bool = False):
    raw = _load_file(swagger_path)
    spec = _parse(raw)

    endpoints = _extract_all_endpoints(spec)

    os.makedirs(output_dir, exist_ok=True)

    if single_file:
        _write_single_file(endpoints, output_dir)
    else:
        _write_per_endpoint(endpoints, output_dir)

    _print_summary(endpoints, output_dir)


# ─── 解析 ───


def _load_file(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def _parse(raw: str) -> dict:
    import yaml
    cleaned = raw.strip()
    if cleaned.startswith('{') or cleaned.startswith('['):
        return json.loads(cleaned)
    return yaml.safe_load(cleaned)


def _resolve_ref(ref: str, spec: dict, depth: int = 0) -> dict:
    if not ref or depth > 5:
        return {}
    parts = ref.lstrip('#/').split('/')
    cur = spec
    for part in parts:
        if isinstance(cur, dict):
            cur = cur.get(part, {})
        else:
            return {}
    if isinstance(cur, dict) and '$ref' in cur and depth < 5:
        return _resolve_ref(cur['$ref'], spec, depth + 1)
    return cur


def _normalize_schema(node: dict, spec: dict, depth: int = 0) -> dict:
    """
    递归规范化 schema 节点：
    - 展开 $ref
    - 合并 allOf
    - 取 oneOf/anyOf 第一个选项
    - 递归处理 properties / items
    """
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
                    if k == 'properties':
                        merged.setdefault('properties', {}).update(v)
                    elif k == 'required':
                        merged.setdefault('required', []).extend(v if isinstance(v, list) else [])
                    elif k not in merged:
                        merged[k] = v
        if 'properties' in merged:
            merged.setdefault('type', 'object')
        for k in node:
            if k not in ('allOf', 'properties', 'required'):
                if k not in merged:
                    merged[k] = node[k]
        node = merged

    # 3. oneOf/anyOf — pick first option
    for combinator in ('oneOf', 'anyOf'):
        if combinator in node and isinstance(node[combinator], list) and node[combinator]:
            first = _normalize_schema(node[combinator][0], spec, depth + 1)
            for k, v in first.items():
                if k not in node:
                    node[k] = v
            node.pop(combinator, None)

    # 4. Recursively normalize properties
    if 'properties' in node and isinstance(node['properties'], dict):
        for name, prop in list(node['properties'].items()):
            if isinstance(prop, dict):
                node['properties'][name] = _normalize_schema(prop, spec, depth + 1)

    # 5. Recursively normalize items
    if 'items' in node and isinstance(node['items'], dict):
        node['items'] = _normalize_schema(node['items'], spec, depth + 1)

    # 6. additionalProperties
    if 'additionalProperties' in node and isinstance(node['additionalProperties'], dict):
        node['additionalProperties'] = _normalize_schema(node['additionalProperties'], spec, depth + 1)

    return node


def _extract_server(spec: dict) -> str:
    """提取服务器基础 URL"""
    if 'servers' in spec and spec['servers']:
        url = spec['servers'][0].get('url', '')
        desc = spec['servers'][0].get('description', '')
        return f'{url}  ({desc})' if desc else url
    if 'host' in spec:
        scheme = (spec.get('schemes') or ['https'])[0]
        host = spec.get('host', 'localhost')
        base = spec.get('basePath', '')
        return f'{scheme}://{host}{base}'
    return ''


def _extract_all_endpoints(spec: dict) -> list[dict]:
    """提取所有端点，解析 $ref / allOf，展平为列表"""
    server = _extract_server(spec)
    endpoints = []

    for path, methods in spec.get('paths', {}).items():
        for method in ('get', 'post', 'put', 'delete', 'patch', 'head', 'options'):
            if method not in methods:
                continue
            detail = methods[method]

            # 参数
            params = []
            for p in detail.get('parameters', []):
                if '$ref' in p:
                    p = _resolve_ref(p['$ref'], spec)
                schema = p.get('schema', {})
                if isinstance(schema, dict) and '$ref' in schema:
                    schema = _resolve_ref(schema['$ref'], spec)
                params.append({
                    'name': p.get('name', ''),
                    'in': p.get('in', 'query'),
                    'type': schema.get('type', 'string'),
                    'required': '是' if p.get('required') else '否',
                    'description': p.get('description', ''),
                    'enum': schema.get('enum'),
                    'default': schema.get('default'),
                    'example': schema.get('example'),
                })

            # 请求体（完整规范化）
            version = _detect_version(spec)
            request_body = None
            if version.startswith('2'):
                for p in detail.get('parameters', []):
                    if '$ref' in p:
                        p = _resolve_ref(p['$ref'], spec)
                    if p.get('in') == 'body':
                        schema = p.get('schema', {})
                        if isinstance(schema, dict) and '$ref' in schema:
                            schema = _resolve_ref(schema['$ref'], spec)
                        request_body = _normalize_schema(schema, spec)
                        break
            else:
                body = detail.get('requestBody', {})
                if '$ref' in body:
                    body = _resolve_ref(body['$ref'], spec)
                content = body.get('content', {})
                for ct in ('application/json', '*/*'):
                    if ct in content:
                        schema = content[ct].get('schema', {})
                        if isinstance(schema, dict) and '$ref' in schema:
                            schema = _resolve_ref(schema['$ref'], spec)
                        request_body = _normalize_schema(schema, spec)
                        break
                if not request_body and content:
                    first_ct = list(content.values())[0]
                    schema = first_ct.get('schema', {})
                    if isinstance(schema, dict) and '$ref' in schema:
                        schema = _resolve_ref(schema['$ref'], spec)
                    request_body = _normalize_schema(schema, spec)

            # 响应（含 headers + 规范化 schema）
            responses_processed = {}
            for code, resp in detail.get('responses', {}).items():
                if '$ref' in resp:
                    resp = _resolve_ref(resp['$ref'], spec)
                proc = {'description': resp.get('description', '')}

                # 响应头
                headers = {}
                for hname, hdef in resp.get('headers', {}).items():
                    if '$ref' in hdef:
                        hdef = _resolve_ref(hdef['$ref'], spec)
                    hs = hdef.get('schema', hdef)
                    if isinstance(hs, dict) and '$ref' in hs:
                        hs = _resolve_ref(hs['$ref'], spec)
                    headers[hname] = {
                        'type': hs.get('type', 'string'),
                        'description': hdef.get('description', ''),
                    }
                proc['headers'] = headers

                # 响应体 schema（完整规范化）
                schemas = {}
                content = resp.get('content', {})
                if content:
                    for ct in ('application/json', '*/*'):
                        if ct in content:
                            schema = content[ct].get('schema', {})
                            if isinstance(schema, dict) and '$ref' in schema:
                                schema = _resolve_ref(schema['$ref'], spec)
                            schemas[ct] = _normalize_schema(schema, spec)
                            break
                    if not schemas:
                        first_ct = list(content.values())[0]
                        schema = first_ct.get('schema', {})
                        if isinstance(schema, dict) and '$ref' in schema:
                            schema = _resolve_ref(schema['$ref'], spec)
                        schemas[list(content.keys())[0]] = _normalize_schema(schema, spec)
                else:
                    schema = resp.get('schema', {})
                    if isinstance(schema, dict) and '$ref' in schema:
                        schema = _resolve_ref(schema['$ref'], spec)
                    if schema:
                        schemas['application/json'] = _normalize_schema(schema, spec)

                proc['schemas'] = schemas
                responses_processed[code] = proc

            security_required = detail.get('security', spec.get('security', []))
            security_schemas = _extract_security_schemas(spec)
            security_enriched = _enrich_security(security_required, security_schemas)

            endpoints.append({
                'server': server,
                'path': path,
                'method': method.upper(),
                'summary': detail.get('summary', '') or detail.get('description', ''),
                'operation_id': detail.get('operationId', ''),
                'tags': detail.get('tags', []),
                'parameters': params,
                'request_body': request_body,
                'responses': responses_processed,
                'security': security_enriched,
                'deprecated': detail.get('deprecated', False),
            })

    return endpoints


def _extract_security_schemas(spec: dict) -> dict:
    """提取安全方案定义"""
    # OpenAPI 3.0
    schemes = spec.get('components', {}).get('securitySchemes', {})
    if not schemes:
        # Swagger 2.0
        schemes = spec.get('securityDefinitions', {})
    result = {}
    for name, definition in schemes.items():
        definition = dict(definition)
        if '$ref' in definition:
            definition = _resolve_ref(definition['$ref'], spec)
        # 统一字段
        entry = {
            'type': definition.get('type', ''),
            'description': definition.get('description', ''),
            'in': definition.get('in', 'header'),
            'parameter_name': definition.get('name', ''),
            'scheme': definition.get('scheme', ''),
            'bearer_format': definition.get('bearerFormat', ''),
        }
        # OAuth2 fields
        if entry['type'] == 'oauth2':
            flows = definition.get('flows', {}) or {}
            flow = next(iter(flows.values()), {})
            entry['authorization_url'] = flow.get('authorizationUrl', '')
            entry['token_url'] = flow.get('tokenUrl', '')
        result[name] = entry
    return result


def _enrich_security(required: list, schemas: dict) -> list:
    """将安全需求与方案定义合并"""
    enriched = []
    for requirement in required:
        if not isinstance(requirement, dict):
            continue
        for name, scopes in requirement.items():
            entry = dict(schemas.get(name, {}))
            entry['name'] = name
            entry['scopes'] = scopes if isinstance(scopes, list) else []
            enriched.append(entry)
    return enriched


def _render_security_scheme(sec: dict) -> str:
    """将安全方案渲染为人可读的描述"""
    name = sec.get('name', '')
    stype = sec.get('type', '')
    scheme = sec.get('scheme', '')
    refmt = sec.get('bearer_format', '')
    param_name = sec.get('parameter_name', '')
    location = sec.get('in', 'header')
    desc = sec.get('description', '')
    scopes = sec.get('scopes', [])

    parts = [f'`{name}`']

    if stype == 'http' and scheme == 'bearer':
        fmt = f' ({refmt})' if refmt else ''
        auth_instr = f'Authorization头: Bearer <token>{fmt}'
        parts.append(f'Bearer认证')
        parts.append(f'方式: {auth_instr}')
    elif stype == 'http' and scheme == 'basic':
        parts.append(f'Basic认证')
        parts.append(f'方式: Authorization头: Basic <base64(用户名:密码)>')
    elif stype == 'apiKey':
        parts.append(f'API Key')
        parts.append(f'方式: {location}中传入`{param_name}`')
    elif stype == 'oauth2':
        parts.append(f'OAuth2')
        if sec.get('authorization_url'):
            parts.append(f'授权地址: {sec["authorization_url"]}')
        if sec.get('token_url'):
            parts.append(f'Token地址: {sec["token_url"]}')
    elif stype:
        parts.append(f'类型: {stype}')
    else:
        parts.append('(未定义安全方案)')

    if scopes:
        parts.append(f'作用域: {", ".join(scopes)}')
    if desc:
        parts.append(f'说明: {desc}')

    return '  \n'.join(parts)


def _detect_version(spec: dict) -> str:
    if 'openapi' in spec:
        return spec['openapi']
    if 'swagger' in spec:
        return spec['swagger']
    return 'unknown'


# ─── 渲染 ───


def _render_schema(schema: dict, lines: list, prefix: str = '', depth: int = 0, parent_path: str = ''):
    """递归渲染JSON Schema为Markdown表格"""
    if depth > 3:
        return

    props = schema.get('properties', {})
    required_list = schema.get('required', [])
    if not props:
        return
    if depth == 0:
        lines.append(f'{prefix}| 字段 | 类型 | 必填 | 描述 |')
        lines.append(f'{prefix}|------|------|------|------|')
    for name, prop in props.items():
        full_path = f'{parent_path}.{name}' if parent_path else name
        ptype = _format_type(prop)
        req = '是' if name in required_list else '否'
        desc = prop.get('description', '')
        enum = prop.get('enum')
        if enum:
            desc += f' 枚举值: {enum}'
        default = prop.get('default')
        if default is not None:
            desc += f' 默认: {default}'
        if prop.get('nullable'):
            desc += ' (可为null)'
        lines.append(f'{prefix}| {full_path} | {ptype} | {req} | {desc} |')
        # 递归嵌套属性
        if prop.get('type') == 'object' and prop.get('properties'):
            _render_schema(prop, lines, prefix, depth + 1, full_path)
        elif prop.get('type') == 'array' and prop.get('items'):
            items = prop['items']
            if isinstance(items, dict):
                if items.get('type') == 'object' and items.get('properties'):
                    _render_schema(items, lines, prefix, depth + 1, f'{full_path}[]')
                elif items.get('type'):
                    pass


def _format_type(prop: dict) -> str:
    """格式化类型显示"""
    ptype = prop.get('type', 'any')
    fmt = prop.get('format', '')
    items_type = ''
    if ptype == 'array' and prop.get('items'):
        if isinstance(prop['items'], dict):
            items_type = prop['items'].get('type', 'any')
    if items_type:
        ptype = f'{ptype}<{items_type}>'
    if fmt:
        ptype = f'{ptype}({fmt})'
    if prop.get('nullable'):
        ptype = f'{ptype}?'
    return ptype


def _schema_to_example(schema: dict) -> any:
    """根据Schema生成示例JSON（优先使用 spec 自带的 example）"""
    if schema.get('example'):
        return schema['example']
    stype = schema.get('type', 'object')
    if stype == 'object' and schema.get('properties'):
        example = {}
        for name, prop in schema['properties'].items():
            example[name] = _schema_to_example(prop)
        return example
    if stype == 'array' and schema.get('items'):
        return [_schema_to_example(schema['items'])]
    if stype == 'string':
        enum = schema.get('enum')
        return enum[0] if enum else 'string'
    if stype in ('integer', 'number'):
        # 使用 example 或 default 如果存在
        ex = schema.get('example', schema.get('default', 0))
        return ex
    if stype == 'boolean':
        return False
    return None


def _render_endpoint(ep: dict) -> str:
    """将单个端点渲染为Markdown"""
    lines = []
    tag = (ep['tags'] or ['default'])[0]
    lines.append(f'## {ep["method"]} {ep["path"]}')
    lines.append('')
    if ep['summary']:
        lines.append(f'**描述**: {ep["summary"]}')
        lines.append('')

    # 服务器地址
    if ep['server']:
        lines.append(f'**基础地址**: `{ep["server"]}`')
        lines.append('')

    if ep['operation_id']:
        lines.append(f'**操作ID**: `{ep["operation_id"]}`')
        lines.append('')
    if ep['deprecated']:
        lines.append('> ⚠️ **已废弃**')
        lines.append('')
    lines.append(f'**标签**: {tag}')
    lines.append('')

    # 请求参数
    if ep['parameters']:
        lines.append('**请求参数**:')
        lines.append('')
        lines.append('| 参数名 | 位置 | 类型 | 必填 | 描述 |')
        lines.append('|--------|------|------|------|------|')
        for p in ep['parameters']:
            desc = p['description'] or ''
            if p['enum']:
                desc += f' 枚举值: {p["enum"]}'
            if p['default'] is not None:
                desc += f' 默认: {p["default"]}'
            lines.append(f'| {p["name"]} | {p["in"]} | {p["type"]} | {p["required"]} | {desc} |')
        lines.append('')
    else:
        lines.append('**请求参数**: 无')
        lines.append('')

    # 请求体
    if ep['request_body']:
        lines.append('**请求体结构**:')
        lines.append('')
        _render_schema(ep['request_body'], lines, prefix='')
        example = _schema_to_example(ep['request_body'])
        if example:
            lines.append('')
            lines.append('请求体示例:')
            lines.append('```json')
            lines.append(json.dumps(example, indent=2, ensure_ascii=False))
            lines.append('```')
        lines.append('')

    # 响应
    if ep['responses']:
        lines.append('**响应**:')
        lines.append('')
        for code, resp in ep['responses'].items():
            desc = resp.get('description', '')
            lines.append(f'**{code} {desc}**')
            lines.append('')

            # 响应头
            if resp.get('headers'):
                lines.append('响应头:')
                lines.append('')
                lines.append('| 头名称 | 类型 | 描述 |')
                lines.append('|--------|------|------|')
                for hname, hdef in resp['headers'].items():
                    lines.append(f'| {hname} | {hdef["type"]} | {hdef["description"]} |')
                lines.append('')

            # 响应体 schema
            if resp.get('schemas') and code.startswith('2'):
                for ct, schema in resp['schemas'].items():
                    if schema and isinstance(schema, dict) and ('properties' in schema or 'items' in schema):
                        lines.append(f'响应体 (`{ct}`):')
                        lines.append('')
                        _render_schema(schema, lines, prefix='')
                        lines.append('')
                        example = _schema_to_example(schema)
                        if example:
                            lines.append('示例:')
                            lines.append('```json')
                            lines.append(json.dumps(example, indent=2, ensure_ascii=False))
                            lines.append('```')
                            lines.append('')
            lines.append('')

    # 安全（不用 ### 标题，防 Dify 自动切分）
    if ep['security']:
        lines.append('**鉴权方式**:')
        for sec in ep['security']:
            rendered = _render_security_scheme(sec)
            for i, line in enumerate(rendered.split('\n')):
                prefix = ' ' if i == 0 else '  '
                lines.append(f'{prefix}{line}')

    return '\n'.join(lines)


# ─── 输出 ───


def _write_per_endpoint(endpoints: list[dict], output_dir: str):
    """每个端点一个文件 + 一个索引文件"""
    index_lines = ['# Swagger API 端点索引', '', f'共 {len(endpoints)} 个端点', '']

    for i, ep in enumerate(endpoints):
        safe_path = ep['path'].replace('/', '_').replace('{', '').replace('}', '').strip('_')
        fname = f"{i:03d}_{ep['method']}_{safe_path}.md"
        filepath = os.path.join(output_dir, fname)

        md = _render_endpoint(ep)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

        index_lines.append(f'- [{ep["method"]} {ep["path"]}]({fname}) — {ep["summary"][:50]}')

    with open(os.path.join(output_dir, '_index.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))

    print(f'  每个端点独立文件: {output_dir}/*.md')
    print(f'  索引文件: {output_dir}/_index.md')


def _single_file_header(endpoints: list[dict]) -> list[str]:
    """生成文件头部（不含端点的纯说明）"""
    methods = set(ep['method'] for ep in endpoints)
    tags = set(t for ep in endpoints for t in ep.get('tags', []))
    has_auth = any(ep.get('security') for ep in endpoints)
    lines = [
        '# Swagger API 接口文档（知识库版）',
        '',
        f'共 {len(endpoints)} 个端点  |  方法: {", ".join(sorted(methods))}  |  标签: {", ".join(sorted(tags)) if tags else "-"}  |  鉴权: {"需要" if has_auth else "无"}',
        '',
        '---',
        '',
        '> 以下每个 `## METHOD /path` 段落是一个独立的API端点。',
        '> LLM使用本知识库时，只关注以 HTTP 方法开头的段落（GET / POST / PUT / DELETE / PATCH），其余内容为辅助说明。',
        '',
    ]
    return lines


def _write_single_file(endpoints: list[dict], output_dir: str):
    """合并为单个Markdown文件，分段符为 \\n## """
    lines = _single_file_header(endpoints)

    for ep in endpoints:
        lines.append(_render_endpoint(ep))
        lines.append('---')
        lines.append('')

    filepath = os.path.join(output_dir, 'swagger_docs.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'  合并文件: {filepath}')


def _print_summary(endpoints: list[dict], output_dir: str):
    """打印处理摘要"""
    methods = {}
    tags = {}
    for ep in endpoints:
        methods[ep['method']] = methods.get(ep['method'], 0) + 1
        for t in ep.get('tags', []):
            tags[t] = tags.get(t, 0) + 1

    has_auth = any(ep.get('security') for ep in endpoints)
    has_deprecated = any(ep.get('deprecated') for ep in endpoints)
    has_server = any(ep.get('server') for ep in endpoints)
    has_allof = any('allOf' in str(ep) for ep in endpoints)  # rough check

    print(f'\n=== 处理完成 ===')
    print(f'  文件: {output_dir}/')
    print(f'  端点数: {len(endpoints)}')
    print(f'  方法分布: {dict(sorted(methods.items()))}')
    print(f'  标签: {dict(sorted(tags.items(), key=lambda x: -x[1]))}')
    print(f'  基础地址: {"有" if has_server else "无"}')
    print(f'  鉴权: {"有" if has_auth else "无"}')
    print(f'  废弃: {"有" if has_deprecated else "无"}')
    print(f'  allOf展开: {"有" if has_allof else "无（无需处理）"}')
    print(f'\n上传方式:')
    print(f'  方案A: 在Dify知识库中点击"导入" → 选择 {output_dir}/ 下的所有 .md 文件')
    print(f'  方案B: 上传 {output_dir}/swagger_docs.md（单文件）')
    print(f'  分段策略选择"自定义" → 分隔符设为 "\\n## "（按端点分段）')


# ─── Dify Knowledge Base API ───


class DifyClient:
    """封装 Dify Dataset (知识库) API 调用"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

    def _request(self, method: str, path: str, data: dict = None, files: dict = None, timeout: int = 60):
        """发送 HTTP 请求，返回 JSON 响应"""
        import json as _json

        url = f'{self.base_url}{path}'
        if files:
            # multipart upload
            import uuid
            boundary = f'----{uuid.uuid4().hex}'
            body = b''
            for field_name, field_value in files.items():
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{field_name}"'.encode()
                if isinstance(field_value, tuple):
                    filename, content = field_value
                    body += f'; filename="{filename}"\r\n'.encode()
                    body += b'Content-Type: application/octet-stream\r\n\r\n'
                    body += content if isinstance(content, bytes) else content.encode()
                else:
                    body += b'\r\n\r\n'
                    body += field_value.encode() if isinstance(field_value, str) else field_value
                body += b'\r\n'
            body += f'--{boundary}--\r\n'.encode()

            headers = dict(self.headers)
            headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
        else:
            body = _json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers=self.headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
                if not raw:
                    return {}
                return _json.loads(raw)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ''
            print(f'  [Dify API 错误] {e.code} {e.reason}: {error_body}')
            raise
        except Exception as e:
            print(f'  [Dify API 请求失败] {e}')
            raise

    def list_documents(self, dataset_id: str, keyword: str = '') -> list[dict]:
        """列出知识库中的文档"""
        path = f'/v1/datasets/{dataset_id}/documents'
        if keyword:
            path += f'?keyword={urllib.parse.quote(keyword)}'
        result = self._request('GET', path)
        return result.get('data', [])

    def delete_document(self, dataset_id: str, document_id: str):
        """删除知识库中的文档"""
        self._request('DELETE', f'/v1/datasets/{dataset_id}/documents/{document_id}')

    def create_document_by_text(self, dataset_id: str, name: str, text: str, separator: str = '\n## '):
        """通过文本创建知识库文档，使用自定义分段规则"""
        payload = {
            'name': name,
            'text': text,
            'indexing_technique': 'high_quality',
            'process_rule': {
                'mode': 'custom',
                'rules': {
                    'pre_processing_rules': [
                        {'id': 'remove_extra_spaces', 'enabled': True},
                        {'id': 'remove_urls_emails', 'enabled': False},
                    ],
                    'segmentation': {
                        'separator': separator,
                        'max_tokens': 500,
                    },
                },
            },
        }
        result = self._request('POST', f'/v1/datasets/{dataset_id}/document/create-by-text', data=payload)
        return result

    def wait_for_indexing(self, dataset_id: str, batch_id: str, poll_interval: int = 3, max_wait: int = 120):
        """等待文档索引完成"""
        start = time.time()
        while time.time() - start < max_wait:
            result = self._request('GET', f'/v1/datasets/{dataset_id}/documents?batch={batch_id}')
            documents = result.get('data', [])
            if documents:
                status = documents[0].get('indexing_status', '')
                if status == 'completed':
                    return True
                elif status == 'error':
                    print(f'  [Dify] 文档索引失败: {documents[0].get("error", "未知错误")}')
                    return False
            time.sleep(poll_interval)
        print('  [Dify] 等待索引超时')
        return False

    def upsert_document(self, dataset_id: str, filepath: str, separator: str = '\n## ', cleanup_old: bool = True):
        """上传/更新文档到 Dify 知识库

        幂等操作: 如果同名文档已存在，先删除再创建。
        """
        filename = os.path.basename(filepath)
        print(f'  [Dify] 准备上传: {filename}')

        # 读取文件内容
        with open(filepath, encoding='utf-8') as f:
            text = f.read()

        # 查找同名文档
        if cleanup_old:
            existing = self.list_documents(dataset_id, keyword=filename)
            if existing:
                doc_id = existing[0].get('id', '')
                if doc_id:
                    print(f'  [Dify] 发现同名文档 {doc_id}，先删除')
                    self.delete_document(dataset_id, doc_id)
                    print(f'  [Dify] 已删除旧文档')

        # 创建新文档
        result = self.create_document_by_text(dataset_id, filename, text, separator=separator)
        batch_id = result.get('batch', '')
        doc_name = result.get('document', {}).get('name', filename)
        print(f'  [Dify] 已提交: {doc_name} (batch={batch_id})')

        # 等待索引
        if batch_id:
            print(f'  [Dify] 等待索引完成...', end='', flush=True)
            ok = self.wait_for_indexing(dataset_id, batch_id)
            if ok:
                print(' ✓')
            else:
                print(' ✗')

        return result


def main():
    parser = argparse.ArgumentParser(description='Swagger → Dify知识库预处理')
    parser.add_argument('swagger', help='Swagger JSON/YAML文件路径')
    parser.add_argument('-o', '--output', default='./swagger_knowledge', help='输出目录')
    parser.add_argument('--single-file', action='store_true', help='合并为单文件')
    parser.add_argument('--dify-base-url', help='Dify 服务地址 (如 http://localhost:4800)')
    parser.add_argument('--dify-api-key', help='Dify Dataset API Key')
    parser.add_argument('--dify-dataset-id', help='Dify 知识库 Dataset ID')
    args = parser.parse_args()

    # 如果指定了 Dify 参数，自动启用单文件模式
    if args.dify_base_url or args.dify_api_key or args.dify_dataset_id:
        if not all([args.dify_base_url, args.dify_api_key, args.dify_dataset_id]):
            parser.error('--dify-base-url, --dify-api-key, --dify-dataset-id 必须同时指定')
        args.single_file = True

    process(args.swagger, args.output, args.single_file)

    # Dify 上传
    if args.dify_base_url:
        if args.single_file:
            md_path = os.path.join(args.output, 'swagger_docs.md')
        else:
            md_path = os.path.join(args.output, '_index.md')

        if not os.path.exists(md_path):
            print(f'\n[错误] 未找到文件: {md_path}，跳过上传')
            return

        print()
        client = DifyClient(args.dify_base_url, args.dify_api_key)
        result = client.upsert_document(
            dataset_id=args.dify_dataset_id,
            filepath=md_path,
            separator='\n## ',
        )
        print(f'\n  ✓ 已上传至 Dify 知识库 (Dataset: {args.dify_dataset_id})')
        print(f'  文档名称: {result.get("document", {}).get("name", "swagger_docs.md")}')
        print(f'  文档ID: {result.get("document", {}).get("id", "N/A")}')


if __name__ == '__main__':
    main()

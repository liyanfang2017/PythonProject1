#!/usr/bin/env python3
"""
端点检索器 — 跨平台替代 grep/jq
从 swagger_parser.py 输出的 JSON 中检索端点。

用法:
    # 按路径关键词检索
    python search_endpoints.py endpoints.json --path user

    # 按方法检索
    python search_endpoints.py endpoints.json --method POST

    # 按标签检索
    python search_endpoints.py endpoints.json --tag pet

    # 组合检索
    python search_endpoints.py endpoints.json --method POST --path user --tag 用户管理

    # 按参数名检索
    python search_endpoints.py endpoints.json --param petId

    # 输出为 Markdown（喂给 LLM）
    python search_endpoints.py endpoints.json --path user --markdown

    # 输出摘要统计
    python search_endpoints.py endpoints.json --summary
"""
import json
import sys
import argparse
import re
from pathlib import Path


def load_endpoints(source: str) -> list[dict]:
    """加载端点列表：支持文件路径或stdin。"""
    if source == '-':
        data = json.load(sys.stdin)
    elif Path(source).is_file():
        with open(source, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.loads(source)

    if isinstance(data, dict):
        from swagger_parser import parse
        return parse(source)
    return data


def search(endpoints: list[dict], **filters) -> list[dict]:
    """
    检索端点。
    
    filters:
        path: 路径关键词（模糊匹配）
        method: HTTP方法（精确，忽略大小写）
        tag: 标签关键词（模糊匹配）
        param: 参数名关键词（模糊匹配）
        summary: 描述关键词（模糊匹配）
        has_body: 是否有请求体 (True/False)
        has_auth: 是否需要认证 (True/False)
    """
    results = endpoints

    if filters.get('path'):
        pattern = re.compile(filters['path'], re.IGNORECASE)
        results = [ep for ep in results if pattern.search(ep.get('path', ''))]

    if filters.get('method'):
        method = filters['method'].upper()
        results = [ep for ep in results if ep.get('method', '').upper() == method]

    if filters.get('tag'):
        pattern = re.compile(filters['tag'], re.IGNORECASE)
        results = [
            ep for ep in results
            if any(pattern.search(t) for t in ep.get('tags', []))
        ]

    if filters.get('param'):
        pattern = re.compile(filters['param'], re.IGNORECASE)
        results = [
            ep for ep in results
            if any(pattern.search(p.get('name', '')) for p in ep.get('parameters', []))
        ]

    if filters.get('summary'):
        pattern = re.compile(filters['summary'], re.IGNORECASE)
        results = [
            ep for ep in results
            if pattern.search(ep.get('summary', ''))
        ]

    if filters.get('has_body') is True:
        results = [ep for ep in results if ep.get('request_body') is not None]
    elif filters.get('has_body') is False:
        results = [ep for ep in results if ep.get('request_body') is None]

    if filters.get('has_auth') is True:
        results = [ep for ep in results if ep.get('security')]
    elif filters.get('has_auth') is False:
        results = [ep for ep in results if not ep.get('security')]

    return results


def to_json(endpoints: list[dict]) -> str:
    return json.dumps(endpoints, indent=2, ensure_ascii=False)


def to_markdown(endpoints: list[dict]) -> str:
    """渲染为 Markdown（喂给 LLM 用）。"""
    lines = [f"## 检索到 {len(endpoints)} 个相关端点\n"]
    for ep in endpoints:
        lines.append(f"### `{ep['method']}` {ep['path']}")
        if ep.get('summary'):
            lines.append(f"**{ep['summary']}**")
        if ep.get('tags'):
            lines.append(f"标签: {', '.join(ep['tags'])}")

        if ep.get('parameters'):
            lines.append("\n参数:")
            for p in ep['parameters']:
                req = "必填" if p.get('required') else "可选"
                lines.append(f"- `{p['name']}` ({p['in']}, {p['type']}, {req})")

        if ep.get('request_body'):
            lines.append("\n请求体:")
            lines.append("```json")
            lines.append(json.dumps(ep['request_body'], indent=2, ensure_ascii=False))
            lines.append("```")

        if ep.get('responses'):
            lines.append("\n响应:")
            for code, schema in ep['responses'].items():
                lines.append(f"- `{code}`: {json.dumps(schema, ensure_ascii=False)[:200]}")

        lines.append("")

    return '\n'.join(lines)


def print_summary(endpoints: list[dict]):
    """打印摘要统计。"""
    methods = {}
    tags = {}
    for ep in endpoints:
        m = ep.get('method', '?')
        methods[m] = methods.get(m, 0) + 1
        for t in ep.get('tags', []):
            tags[t] = tags.get(t, 0) + 1

    print(f"总端点数: {len(endpoints)}")
    print(f"方法分布: {dict(sorted(methods.items()))}")
    print(f"标签分类: {dict(sorted(tags.items()))}")
    print(f"需要认证: {sum(1 for ep in endpoints if ep.get('security'))}")
    print(f"有请求体: {sum(1 for ep in endpoints if ep.get('request_body'))}")


def main():
    parser = argparse.ArgumentParser(description='端点检索器')
    parser.add_argument('source', help='端点JSON文件路径，或 - 从stdin读取')
    parser.add_argument('--path', help='按路径关键词检索')
    parser.add_argument('--method', help='按HTTP方法检索 (GET/POST/PUT/DELETE)')
    parser.add_argument('--tag', help='按标签关键词检索')
    parser.add_argument('--param', help='按参数名关键词检索')
    parser.add_argument('--summary', help='按描述关键词检索')
    parser.add_argument('--has-body', action='store_true', help='仅返回有请求体的端点')
    parser.add_argument('--no-auth', action='store_true', help='仅返回不需要认证的端点')
    parser.add_argument('--markdown', action='store_true', help='输出Markdown格式')
    parser.add_argument('--summary-only', action='store_true', help='仅输出统计摘要')
    parser.add_argument('--limit', type=int, default=0, help='限制返回数量（0=不限）')
    args = parser.parse_args()

    endpoints = load_endpoints(args.source)

    if args.summary_only:
        print_summary(endpoints)
        return

    filters = {}
    if args.path:
        filters['path'] = args.path
    if args.method:
        filters['method'] = args.method
    if args.tag:
        filters['tag'] = args.tag
    if args.param:
        filters['param'] = args.param
    if args.summary:
        filters['summary'] = args.summary
    if args.has_body:
        filters['has_body'] = True
    if args.no_auth:
        filters['has_auth'] = False

    results = search(endpoints, **filters)

    if args.limit > 0:
        results = results[:args.limit]

    if args.markdown:
        print(to_markdown(results))
    else:
        print(to_json(results))


if __name__ == '__main__':
    main()

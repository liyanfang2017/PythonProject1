#!/usr/bin/env python3
"""
输入分类器
判断用户输入是否包含测试用例结构（测试步骤+预期结果）。

用法:
    # 命令行
    python case_classifier.py --input "1. 登录 2. 查询用户列表 3. 验证返回200"

    # 作为模块
    from case_classifier import classify
    result = classify("用户输入内容")
"""
import json
import re
import argparse


# 测试步骤关键词
STEP_KEYWORDS = [
    r'步骤[1-9]',
    r'第[一二三四五六七八九十\d]步',
    r'(?<!\d)[1-9][.、）)]\s',
    r'step[1-9]',
    r'(\d+)\.\s',
]

# 预期结果关键词
EXPECTED_KEYWORDS = [
    r'预期',
    r'期望',
    r'应该',
    r'返回',
    r'断言',
    r'验证',
    r'assert',
    r'expected',
    r'应返回',
    r'应得到',
    r'结果是',
    r'状态码',
]

# 用例名称关键词
CASE_NAME_KEYWORDS = [
    r'用例[1-9]',
    r'测试[1-9]',
    r'场景[1-9]',
    r'case[1-9]',
    r'test[1-9]',
]


def classify(user_input: str) -> dict:
    """
    分类用户输入，判断是否包含测试用例结构。

    返回:
        {
            "has_case": bool,
            "query": "纯需求描述",
            "cases": [{"name": str, "steps": [str], "expected": str}]
        }
    """
    text = user_input.strip()
    if not text:
        return {"has_case": False, "query": "", "cases": []}

    # 检测是否有步骤+预期的结构
    has_steps = _has_step_structure(text)
    has_expected = _has_expected_structure(text)
    has_case_name = _has_case_name(text)

    # 如果同时有步骤和预期，认为是用例
    has_case = has_steps and has_expected

    if has_case:
        cases = _extract_cases(text)
        query = _extract_pure_requirement(text, cases)
        return {"has_case": True, "query": query, "cases": cases}
    else:
        return {"has_case": False, "query": text, "cases": []}


def _has_step_structure(text: str) -> bool:
    """检测是否有步骤结构。"""
    for kw in STEP_KEYWORDS:
        if re.search(kw, text, re.IGNORECASE):
            return True
    return False


def _has_expected_structure(text: str) -> bool:
    """检测是否有预期结果结构。"""
    for kw in EXPECTED_KEYWORDS:
        if re.search(kw, text, re.IGNORECASE):
            return True
    return False


def _has_case_name(text: str) -> bool:
    """检测是否有用例名称。"""
    for kw in CASE_NAME_KEYWORDS:
        if re.search(kw, text, re.IGNORECASE):
            return True
    return False


def _extract_cases(text: str) -> list[dict]:
    """从文本中提取测试用例。"""
    cases = []

    # 尝试按"用例N"或"测试N"分割
    case_pattern = r'(?:用例|测试|场景|case|test)[\s]*[1-9]'
    splits = re.split(f'({case_pattern})', text, flags=re.IGNORECASE)

    if len(splits) > 1:
        # 有明确的用例分割
        i = 1
        while i < len(splits):
            name = splits[i].strip()
            content = splits[i + 1].strip() if i + 1 < len(splits) else ""
            steps, expected = _parse_case_content(content)
            if steps:
                cases.append({"name": name, "steps": steps, "expected": expected})
            i += 2
    else:
        # 没有明确分割，尝试按步骤解析
        steps, expected = _parse_case_content(text)
        if steps:
            # 从文本中提取用例名称
            name_match = re.search(r'[:：](.+?)[\n\r]', text)
            name = name_match.group(1).strip() if name_match else "测试用例"
            cases.append({"name": name, "steps": steps, "expected": expected})

    return cases if cases else [{"name": "测试用例", "steps": [text], "expected": ""}]


def _parse_case_content(content: str) -> tuple[list[str], str]:
    """解析单个用例内容，返回 (steps, expected)。"""
    steps = []
    expected = ""

    # 先按换行分割，也支持内联格式（步骤1: xxx 步骤2: yyy）
    # 将内联的"步骤N:"替换为换行分隔
    normalized = re.sub(r'(步骤[1-9]|[一二三四五六七八九十][.、])', r'\n\1', content)
    normalized = re.sub(r'(预期|期望|断言|验证|应返回)[：:]',
                        r'\n\1', normalized)

    lines = normalized.split('\n')
    in_expected = False
    current_step = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测是否进入预期结果部分
        if re.match(r'(?:预期|期望|断言|验证|assert|expected|应返回)', line, re.IGNORECASE):
            in_expected = True
            expected = re.sub(r'^(?:预期|期望|断言|验证|assert|expected|应返回)[：:\s]*', '', line).strip()
            continue

        if in_expected:
            expected += " " + line
            continue

        # 提取步骤 - 支持多种格式
        step_match = re.match(
            r'(?:步骤\s*[1-9一二三四五六七八九十]|[1-9][.、）)]\s*|[一二三四五六七八九十][.、）)]\s*)(.+)',
            line
        )
        if step_match:
            if current_step:
                steps.append(current_step)
            current_step = step_match.group(1).strip()
        elif current_step:
            current_step += " " + line
        else:
            current_step = line

    if current_step:
        steps.append(current_step)

    return steps, expected.strip()


def _extract_pure_requirement(text: str, cases: list[dict]) -> str:
    """从原文中提取纯需求描述（去除用例部分）。"""
    # 简单策略：去掉所有用例相关的内容
    result = text
    for case in cases:
        for step in case.get('steps', []):
            result = result.replace(step, '')
        if case.get('expected'):
            result = result.replace(case['expected'], '')
        result = result.replace(case.get('name', ''), '')

    # 清理多余空白
    result = re.sub(r'\n\s*\n', '\n', result).strip()
    result = re.sub(r'[ \t]+', ' ', result)
    return result


def main():
    parser = argparse.ArgumentParser(description='输入分类器')
    parser.add_argument('--input', '-i', required=True, help='用户输入内容')
    parser.add_argument('--json', '-j', action='store_true', help='JSON输出')
    args = parser.parse_args()

    result = classify(args.input)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"has_case: {result['has_case']}")
        print(f"query: {result['query']}")
        if result['cases']:
            print(f"cases ({len(result['cases'])}):")
            for i, c in enumerate(result['cases'], 1):
                print(f"  [{i}] {c['name']}")
                print(f"      steps: {c['steps']}")
                print(f"      expected: {c['expected']}")


if __name__ == '__main__':
    main()

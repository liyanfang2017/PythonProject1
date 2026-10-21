"""testcase-generator 用例集机械校验。

用法:
  cat cases.json | python3 validate_cases.py
  python3 validate_cases.py cases.json

退出码: 0=全部合规  1=存在违规(清单打到 stdout)  2=输入错误(原因打到 stderr)
"""
import json
import re
import sys

REQUIRED_KEYS = (
    "id", "module", "title", "preconditions",
    "steps", "expected", "priority", "case_type", "dimension",
)

ENUMS = {
    "priority": ("P0", "P1", "P2"),
    "case_type": ("正向", "反向", "边界"),
    "dimension": ("接口", "UI"),
}

ID_RE = re.compile(r"^TC_[A-Z0-9]+_\d{3}$")


def validate_cases(cases):
    """校验用例对象数组，返回违规清单（空列表 = 全部合规）。"""
    if not cases:
        return ["用例集为空：至少需要 1 条用例"]
    violations = []
    for i, case in enumerate(cases, 1):
        cid = case.get("id", "?") if isinstance(case, dict) else "?"
        prefix = f"用例{i}({cid})"
        if not isinstance(case, dict):
            violations.append(f"{prefix}: 用例不是 JSON 对象")
            continue
        for key in REQUIRED_KEYS:
            value = case.get(key)
            if not isinstance(value, str) or not value.strip():
                violations.append(f"{prefix}: 缺少必填字段或字段为空: {key}")
        for key, allowed in ENUMS.items():
            value = case.get(key)
            if isinstance(value, str) and value and value not in allowed:
                violations.append(
                    f"{prefix}: {key} 枚举非法: {value}（允许: {'/'.join(allowed)}）")
        case_id = case.get("id")
        if isinstance(case_id, str) and case_id and not ID_RE.match(case_id):
            violations.append(
                f"{prefix}: id 不符合 TC_模块大写缩写_三位序号 规范: {case_id}")
        steps = case.get("steps")
        if isinstance(steps, str) and steps and "→" not in steps:
            violations.append(f"{prefix}: steps 必须用 → 分隔，一步一个操作")
    return violations


def main():
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"输入错误：无法读取/解析文件 {sys.argv[1]}: {e}", file=sys.stderr)
            return 2
    else:
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"输入错误：stdin 不是合法 JSON: {e}", file=sys.stderr)
            return 2
    if not isinstance(data, list):
        print("输入错误：JSON 顶层必须是数组（用例对象列表）", file=sys.stderr)
        return 2
    violations = validate_cases(data)
    if violations:
        print("\n".join(violations))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

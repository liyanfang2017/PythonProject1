import json, subprocess, sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / ".claude/skills/testcase-generator/scripts/validate_cases.py"
sys.path.insert(0, str(SCRIPT.parent))
from validate_cases import validate_cases

VALID = [{
    "id": "TC_LOGIN_001", "module": "登录", "title": "正确密码登录成功",
    "preconditions": "用户已注册", "steps": "打开登录页→输入正确密码→点击登录",
    "expected": "跳转首页并显示用户昵称", "priority": "P0", "case_type": "正向", "dimension": "接口",
}]

def run_cli(payload: str):
    return subprocess.run([sys.executable, str(SCRIPT)], input=payload,
                          capture_output=True, text=True)

def test_valid_cases_pass():
    assert validate_cases(VALID) == []

def test_missing_required_field():
    case = dict(VALID[0]); del case["expected"]
    assert any("expected" in v for v in validate_cases([case]))

def test_bad_enums():
    case = dict(VALID[0], priority="P3", case_type="性能", dimension="API")
    out = "\n".join(validate_cases([case]))
    assert "P3" in out and "性能" in out and "API" in out

def test_bad_id():
    for bad_id in ("TC_login_001", "TC_登录_001", "TC-LOGIN-001", "TC_LOGIN_1"):
        case = dict(VALID[0], id=bad_id)
        assert any(bad_id in v for v in validate_cases([case])), bad_id

def test_steps_without_arrow():
    case = dict(VALID[0], steps="点击登录。进入首页")
    assert any("→" in v for v in validate_cases([case]))

def test_empty_cases():
    assert len(validate_cases([])) > 0

def test_cli_stdin_valid():
    r = run_cli(json.dumps(VALID, ensure_ascii=False))
    assert r.returncode == 0

def test_cli_stdin_broken_json():
    r = run_cli("not json{{{")
    assert r.returncode == 2 and r.stderr.strip()

def test_cli_stdin_non_array():
    r = run_cli('{"id": "TC_A_001"}')
    assert r.returncode == 2 and r.stderr.strip()

def test_cli_file_arg(tmp_path):
    f = tmp_path / "cases.json"
    f.write_text(json.dumps(VALID, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
    assert r.returncode == 0

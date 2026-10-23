# testcase-generator Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 spec 交付 `.claude/skills/testcase-generator/` skill：多源输入（OpenAPI/PRD 文本/技术方案/设计稿）→ 9 字段结构化测试用例，含三门禁、反编造机制、三格式输出。

**Architecture:** 一个 SKILL.md 主流程文件 + 两个按需加载的 references + 一个纯标准库校验脚本。LLM 负责判断类工作（提取、生成、溯源），脚本只做机械校验。规格冲突一律以 spec 为准。

**Tech Stack:** Markdown（SKILL.md / references）、Python 3.10 纯标准库（脚本）、pytest 9.1.1（仅测试）。

**Spec:** `create_skill/2026-10-21-testcase-generator-design.md`（本计划与 spec 配套使用，执行者两者都要读）

## Global Constraints

- 项目**当前不是 git 仓库**：每个任务的 Commit 步骤仅在用户确认 `git init` 后执行，否则整条跳过（handoff 时决定）
- 9 字段固定顺序：用例ID、模块、标题、前置条件、操作步骤、预期结果、优先级、用例类型、用例维度；JSON 键名为 `id/module/title/preconditions/steps/expected/priority/case_type/dimension`
- 枚举封闭：用例类型 ∈ {正向, 反向, 边界}；维度 ∈ {接口, UI}；优先级 ∈ {P0, P1, P2}
- ID 正则：`^TC_[A-Z0-9]+_\d{3}$`；操作步骤用 `→` 分隔、一步一个操作
- 输出：默认 `./output/testcases.<md|json|csv>`；CSV = UTF-8 带 BOM（`utf-8-sig`）；JSON = 纯对象数组（统计摘要与【需确认】清单只在对话/Markdown 中）
- SKILL.md 目标 < 400 行；长参考内容一律放 references/，不在主文件展开
- 校验脚本只用 Python 标准库；禁止任何网络访问（含 WebFetch/WebSearch）
- 唯一落盘物是输出文件；校验走 stdin/内存，不产生中间文件
- description 必须包含 4 个触发短语：「帮我生成测试用例」「基于这个页面生成测试用例」「基于这个接口生成用例」「根据 swagger/PRD/设计稿出用例」，并写明路由边界（spec §1.2）
- 门禁豁免时输出标注「本次未经人工门禁确认」（spec §6.2）

## Review Focus

spec 暗示但任务测试未直接覆盖、最容易坑到使用者的五类输入（前三种已钉进 Task 1 的测试，后两种钉进 Task 2 指令与 Task 5 验收）：

1. 损坏/非数组 JSON 从 stdin 进入校验脚本 → 期望：退出码 2、stderr 给出明确原因，不崩溃、不输出部分结果（Task 1 test_cli_stdin_broken_json / test_cli_stdin_non_array）
2. 空用例集 `[]` → 期望：报「用例集为空」违规，而不是 0 违规静默通过（Task 1 test_empty_cases）
3. 模块缩写为中文或含小写（`TC_登录_001`、`TC_login_001`）→ 期望：被 ID 正则拦截（Task 1 test_bad_id）
4. 预期结果含逗号/引号/换行的 CSV 渲染 → 期望：csv 模块引号转义 + BOM 保留，Excel 直开不乱码（Task 2 输出节写明用 Python csv 模块 + `utf-8-sig`；Task 5 验收项 3）
5. 用户给 Figma 链接或 PDF 需求文档 → 期望：按 spec §1.2 路由引导（提示导出截图 / 转 business-test-case），绝不尝试解析（Task 2 不适用场景节；Task 5 验收项 6）

---

### Task 1: `validate_cases.py` 校验脚本（TDD）

**Files:**
- Create: `.claude/skills/testcase-generator/scripts/validate_cases.py`
- Test: `create_skill/tests/test_validate_cases.py`

**Interfaces:**
- Consumes: 无（独立起点）
- Produces:
  - `validate_cases(cases: list[dict]) -> list[str]` — 返回违规清单（每条一个字符串，含用例序号与 ID），空列表 = 全部合规
  - CLI：`python3 .claude/skills/testcase-generator/scripts/validate_cases.py [file]` — 无参数时从 stdin 读 JSON；有参数时读文件路径。输入为「用例对象数组」。退出码：`0`=全部合规；`1`=存在违规（违规清单逐行打到 stdout）；`2`=输入错误（JSON 损坏/非数组/文件不可读，原因打到 stderr）

- [ ] **Step 1: 写失败测试** — 创建 `create_skill/tests/test_validate_cases.py`：

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest create_skill/tests/test_validate_cases.py -v`
Expected: 全部 FAIL（`ModuleNotFoundError: validate_cases`）

- [ ] **Step 3: 实现 `validate_cases.py`**

签名 `validate_cases(cases: list[dict]) -> list[str]`。校验规则（违规消息用中文，包含用例序号与 id）：① 九个必填键齐全且非空字符串 ② 三个枚举字段取值合法 ③ id 匹配 `^TC_[A-Z0-9]+_\d{3}$` ④ steps 含 `→` ⑤ 空数组返回「用例集为空」违规。`main()`：读 stdin 或 `sys.argv[1]`，`json.load` 后类型不是 list → 退出码 2；解析失败 → 退出码 2；有违规逐行打印并退出 1，否则退出 0。只用标准库（`json`/`re`/`sys`）。

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest create_skill/tests/test_validate_cases.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**（若已确认 git init）

```bash
git add .claude/skills/testcase-generator/scripts/validate_cases.py create_skill/tests/test_validate_cases.py
git commit -m "feat(testcase-generator): add validate_cases.py with TDD tests"
```

---

### Task 2: `SKILL.md` 主文件

**Files:**
- Create: `.claude/skills/testcase-generator/SKILL.md`

**Interfaces:**
- Consumes: Task 1 的 CLI 契约（Step 3 自查指令中引用）
- Produces: skill 入口文件；引用 `references/input-guide.md` 与 `references/case-examples.md`（Task 3/4 按这两个固定路径创建）

- [ ] **Step 1: 写 SKILL.md** — frontmatter 逐字采用：

```yaml
---
name: testcase-generator
description: 多源测试用例生成。从 OpenAPI/Swagger 接口文档、PRD 文本、技术方案文档、设计稿截图生成结构化测试用例（用例ID/模块/标题/前置条件/操作步骤/预期结果/优先级/用例类型/用例维度 九字段），支持 Markdown/JSON/CSV 三种输出，含三道人工门禁与反编造溯源。当用户说"帮我生成测试用例"、"基于这个页面生成测试用例"、"基于这个接口生成用例"、"根据 swagger/PRD/设计稿出用例"时使用。不适用：要五类分类（功能/边界值/异常/安全/兼容）或输入为 PDF/DOCX/HTML → 用 business-test-case；要 pytest 等可执行脚本 → 用 api-test-pipeline。
---
```

正文按以下节组织（内容以 spec 对应节为准，标注「逐字收录」的表不许改写）：

1. 概述与适用边界（路由规则，spec §1.2 逐字）
2. 输入规范四种来源总表（spec §4，逐字；细节指向 `references/input-guide.md`）
3. 用例字段规范 9 字段全表（spec §5.1，逐字）+ 三种输出格式与落盘规则（spec §5.2；CSV 明确「用 Python csv 模块生成、`utf-8-sig` 编码」）
4. 主流程 Step 0-4 流程图（spec §6.1）
5. 门禁 G1-G3 全表 + 强制触发 + 豁免规则（spec §6.2 修订版逐字，含「豁免优先，实质不降级」）
6. 生成矩阵与覆盖范围默认（spec §6.3 含 >20 端点子集化建议）
7. 反编造机制：生成时规则 + Step 3 自查（机械部分调用 `cat <用例集.json> | python3 .claude/skills/testcase-generator/scripts/validate_cases.py`，语义部分按指令执行；spec §6.4 + §8）
8. 异常兜底表（spec §6.5，逐字）
9. 触发方式说明（斜杠 + 自然语言，spec §7）
10. 质量自检清单（对照 spec §9 验收项）

- [ ] **Step 2: 机械验证**

```bash
wc -l .claude/skills/testcase-generator/SKILL.md          # 期望 < 400
head -1 .claude/skills/testcase-generator/SKILL.md        # 期望: ---
grep -c "帮我生成测试用例\|基于这个页面生成测试用例\|基于这个接口生成用例" .claude/skills/testcase-generator/SKILL.md   # 期望 ≥ 1（description 内）
grep -c "G1\|G2\|G3" .claude/skills/testcase-generator/SKILL.md    # 期望 ≥ 3
grep -c "business-test-case\|api-test-pipeline" .claude/skills/testcase-generator/SKILL.md   # 期望 ≥ 2（路由边界）
grep -c "本次未经人工门禁确认" .claude/skills/testcase-generator/SKILL.md  # 期望 = 1
grep -c "utf-8-sig" .claude/skills/testcase-generator/SKILL.md     # 期望 ≥ 1
```

- [ ] **Step 3: Commit**（若已确认 git init）

```bash
git add .claude/skills/testcase-generator/SKILL.md
git commit -m "feat(testcase-generator): add SKILL.md with gates and anti-fabrication flow"
```

---

### Task 3: `references/input-guide.md` 输入解析指南

**Files:**
- Create: `.claude/skills/testcase-generator/references/input-guide.md`

**Interfaces:**
- Consumes: 无
- Produces: 被 SKILL.md 第 2 节按需引用的输入解析细节

- [ ] **Step 1: 写 input-guide.md** — 四节对应四种输入，每节含：识别特征表（spec §4）、解析要点、常见坑。必须覆盖的坑：Swagger 2.0 与 OpenAPI 3.x 结构差异（`definitions` vs `components/schemas`）；`$ref` 展开与循环引用处理；PRD 纯截图无文字层时的处理（请求文字补充，不猜）；技术方案文档按「技术变更点/风险点」提取而非业务场景；设计稿只认可见控件原文（按钮文案、输入框 placeholder），Figma 等在线链接一律拒绝并请用户导出截图。

- [ ] **Step 2: 机械验证**

```bash
grep -c "OpenAPI\|PRD\|技术方案\|设计稿" .claude/skills/testcase-generator/references/input-guide.md  # 期望 4 节齐全（≥4）
grep -c "Figma" .claude/skills/testcase-generator/references/input-guide.md   # 期望 ≥ 1（拒绝规则在）
wc -l .claude/skills/testcase-generator/references/input-guide.md   # 期望 < 200（按需加载文件保持精炼）
```

- [ ] **Step 3: Commit**（若已确认 git init）

```bash
git add .claude/skills/testcase-generator/references/input-guide.md
git commit -m "feat(testcase-generator): add input parsing guide"
```

---

### Task 4: `references/case-examples.md` 示例用例集

**Files:**
- Create: `.claude/skills/testcase-generator/references/case-examples.md`

**Interfaces:**
- Consumes: 无
- Produces: few-shot 示例，供 SKILL.md 生成阶段按需引用

- [ ] **Step 1: 写 case-examples.md** — 六个好例（接口×正向/反向/边界 + UI×正向/反向/边界，各至少 1 条，9 字段齐全、符合全部 Global Constraints）+ 三个标注坏例（编造控件名、空泛预期「系统正常」、一步多操作），每个坏例后附一句「错在哪、应改成什么」。

- [ ] **Step 2: 机械验证**

```bash
grep -c "TC_" .claude/skills/testcase-generator/references/case-examples.md   # 期望 ≥ 6（好例数）
grep -c "错在哪" .claude/skills/testcase-generator/references/case-examples.md  # 期望 = 3（坏例数）
grep -c "反向\|边界" .claude/skills/testcase-generator/references/case-examples.md  # 期望 ≥ 4
```

- [ ] **Step 3: Commit**（若已确认 git init）

```bash
git add .claude/skills/testcase-generator/references/case-examples.md
git commit -m "feat(testcase-generator): add few-shot case examples"
```

---

### Task 5: 验收测试（spec §9）

**Files:**
- Create: `create_skill/fixtures/sample-openapi.json`（5-6 个端点的宠物商店风格样例，含 `$ref`、必填参数、错误码定义）
- Create: `create_skill/fixtures/sample-prd.md`（一页登录页 PRD：控件名、字段规则、角色）
- Create: `create_skill/fixtures/acceptance-checklist.md`（验收记录表）

**Interfaces:**
- Consumes: Task 1-4 全部产物（skill 已安装）
- Produces: 验收记录（spec §9 六项的通过/失败结论）

- [ ] **Step 1: 创建两个 fixture**（样例数据，非业务敏感）

- [ ] **Step 2: 重载技能** — 运行 `/reload-skills`，确认 skill 列表出现 `testcase-generator`

- [ ] **Step 3: 按清单逐项验收**（与用户一起在新会话执行）：

| spec §9 项 | 操作 | 通过标准 |
|---|---|---|
| 1 接口维溯源 | 喂 `sample-openapi.json`，生成接口维用例 | 抽查 10 条，字段/参数名 100% 在原文可找到 |
| 2 混合输入两维 | 同喂 PRD + OpenAPI（设计稿用用户随手截图） | 一次产出两维；控件名可溯源 |
| 3 三格式合法 | 依次要 md/json/csv 输出 | `json.load` 通过；csv 读回正常且含 BOM；md 表格渲染正常 |
| 4 兜底路径 | 分别给空输入、损坏 JSON、不可辨认截图 | 行为符合 spec §6.5，绝不硬生成 |
| 5 门禁与豁免 | 正常跑一轮看 G1-G3；再说「跳过确认」跑一轮 | 门禁逐道呈现；豁免生效且输出带「本次未经人工门禁确认」 |
| 6 触发与路由 | 新会话说「帮我生成测试用例」；再说「帮我生成 pytest 脚本」 | 前者唤起本 skill；后者被引导到 api-test-pipeline |

- [ ] **Step 4: 记录验收结论到 `acceptance-checklist.md`**

- [ ] **Step 5: Commit**（若已确认 git init）

```bash
git add create_skill/fixtures/
git commit -m "test(testcase-generator): add acceptance fixtures and checklist"
```

---

## Self-Review 记录

- **Spec coverage**：§1.2 路由→Task 2；§3 约束→Global；§4 输入→Task 2/3；§5 输出→Task 1/2；§6 流程/门禁/反编造/兜底→Task 2；§7 触发→Task 2 frontmatter；§8 结构→File structure+Task 1；§9 验收→Task 5。无缺口。
- **Step scan**：每个代码/内容步骤给出唯一合理产物；Task 1 测试为完整代码块，实现为签名+规则（测试已钉死行为）。
- **Type consistency**：`validate_cases`、脚本路径、references 两个文件名在 Task 1-4 间一致。
- **Review Focus**：五条均有归属（1-3→Task 1 测试；4→Task 2 指令+Task 5；5→Task 2 边界节+Task 5）。
- **Proportion**：计划 ≈ 230 行 < spec ≈ 210 行的 1.2 倍，无成段转录。

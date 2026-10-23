# 手机 App 端自动化测试 Skill 构建 · 实操实例手册

> 依据《从零设计一个 Harness 自动化 Skill：材料清单与落地步骤》逐章填充真实实例。
> 本文回答"每一步该准备哪些材料、按什么步骤落地"——把这些材料在**手机 App 端自动化测试 Skill**这个例子里具体长什么样、每一步填成什么样，逐一列出来。
> 全文示例围绕同一个靶子展开，用 `[方括号]` 标注的内容，是需你按自己项目替换的位置。

---

## 1 示例项目设定

为让每一步有统一靶子，先把这个示例 Skill 立起来。它的任务定义、触发场景、产出格式贯穿全文，后续每一章都复用这套设定。

| 项目 | 示例取值 |
| --- | --- |
| Skill 名称 | `mobile-app-test-automation` |
| 一句话任务定义 | 根据手机 App 功能需求（文字 / PRD / 截图）自动产出符合团队规范的 Appium 自动化测试用例 JSON 与可运行 Python 脚本，经机械校验后落盘 `artifacts/` |
| 产出类型 | 测试用例 JSON + Python 测试脚本（Appium） |
| 消费场景 | 手机 App 原生 UI 自动化（Appium，Android / iOS） |
| 技术栈 | Python 3.10 + pytest + Appium（appium-python-client）+ 真机 / 模拟器 |

---

## 2 第 0 章实例：开工前要准备的材料

动手写代码前，把四类材料凑齐。下面是这个示例"真凑齐"之后的样子，每类材料都给出了可直接照着填的实例。

### 2.1 任务定义材料（决定"总控"怎么写）

**一句话任务定义（示例）**

> 把用户给出的手机 App 功能需求，转化为一套可直接运行的 Appium 自动化测试用例与脚本。产出必须满足：用例含模块、平台、优先级、前置条件、操作步骤、Appium 定位器与断言；脚本遵循 Page Object 分层；全部经机械校验、落盘到 `artifacts/`。

反面作用提示：正因为任务定义明确到"产出什么、约束什么"，总控才能做到只调度不干活——它不自己分析需求，也不自己写代码。

**触发场景清单（示例，4 句用户原话）**

- "帮我给『登录』功能写一套手机 App 自动化测试用例"
- "根据这份 PRD 生成 Appium 自动化测试脚本"
- "把这条需求转成可执行的 App 端自动化测试"
- "给我补一下 XX 模块的回归用例"

不适用边界：用户说"帮我跑一遍测试 / 执行这些用例"，应路由到测试执行工具；"分析一下用例覆盖率"，应路由到覆盖率分析 Skill。边界写进 `description`，防止错误触发。

**输入形态清单（示例）**

| 输入形态 | 是否接受 | 边界与处理 |
| --- | --- | --- |
| 需求文字（直接输入） | 接受 | 需含功能入口、操作步骤、预期结果 |
| PRD 文档（.docx / .pdf） | 接受 | 先解析提取需求点，再进入分析 |
| 需求截图 / 原型图 | 部分接受 | 能识别页面元素（控件、文案）即接受；过密时引导改用文档 |
| 接口文档 | 接受（辅助） | 仅用于补充元素与断言语义 |
| 含糊口语描述 | 不接受 | 引导话术："请补充功能入口、操作步骤、预期结果" |

**期望输出定义（示例）**

| 产物 | 格式 | 必填字段 / 约束 | 落盘路径 |
| --- | --- | --- | --- |
| `test_cases.json` | JSON | `id、title、module、platform、priority、precondition、steps[]、locator、assertion`；`platform ∈ {android, ios}`；`priority ∈ {P0,P1,P2}`；`id` 命名 `case_<模块>_<序号>` | `artifacts/` |
| `test_<module>.py` | Python | 遵循 Page Object 分层；一个用例一个函数；含 Appium 断言 | `artifacts/` |

下游（CI / 报告系统）依赖这套固定格式，所以字段必填、枚举、落盘路径都必须预先定死，不能每次随缘。

### 2.2 领域知识材料（决定"实现 Agent"的质量）

| 材料 | 示例 |
| --- | --- |
| 领域规范文档 | `references/mobile-test-spec.md`：命名规范、Page Object 分层、Appium 定位器规范、断言写法 |
| few-shot 样例 2~3 组 | 3 组"需求输入 → 期望 JSON 用例"对照（登录 / 搜索 / 下单各 1 组） |
| 关键词映射表 | 见下表 |
| 相邻真实案例 | 项目里已有的 `test_login.py`、`test_search.py`（Appium 版），供参照风格 |

**关键词映射表（示例）**

| 需求关键词 | 读取参考文档 |
| --- | --- |
| 登录 / 账号 / 鉴权 | `references/login_spec.md` |
| 购物车 / 下单 / 结算 | `references/order_spec.md` |
| 搜索 / 列表 / 筛选 | `references/search_spec.md` |
| 其他 | `references/mobile-test-spec.md`（通用规范） |

### 2.3 工具与连接材料（决定"工具调用"能不能落地）

**可执行命令清单（示例，每个命令先在终端手动跑通一遍）**

| 命令 | 输入 | 输出 | 退出码 |
| --- | --- | --- | --- |
| `pytest -q artifacts/test_login.py` | 生成的测试脚本 | 测试结果 | 0 通过 / 1 失败 |
| `python3 scripts/validate.py < test_cases.json` | 用例 JSON（stdin） | 违规清单（stdout） | 0 合规 / 1 违规 / 2 传参错误 |
| `appium` | 无 | 启动 Appium Server | 0 启动成功 / 非 0 失败 |
| `adb devices` | 无 | 已连接设备 UDID 列表 | 0 正常 / 非 0 环境异常 |

**机械校验脚本 `validate.py`（示例，退出码 0 / 1 / 2）**

```python
#!/usr/bin/env python3
# 手机 App 用例机械校验：stdin 进 JSON，stdout 出违规清单，退出码 0/1/2。
import json, sys

def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(f'输入错误: {e}', file=sys.stderr); sys.exit(2)
    errors = []
    allowed_platform = {'android', 'ios'}
    allowed_priority = {'P0', 'P1', 'P2'}
    for i, item in enumerate(data):
        for f in ('id', 'title', 'module', 'platform', 'priority',
                  'precondition', 'steps', 'locator', 'assertion'):
            if not item.get(f):
                errors.append(f'第{i}条: 缺必填字段 {f}')
        if item.get('platform') and item['platform'] not in allowed_platform:
            errors.append(f'第{i}条: platform 非法（应为 android/ios）')
        if item.get('priority') and item['priority'] not in allowed_priority:
            errors.append(f'第{i}条: priority 非法（应为 P0/P1/P2）')
        if not str(item.get('id', '')).startswith('case_'):
            errors.append(f'第{i}条: id 未按 case_<模块>_<序号> 命名')
        if item.get('locator'):
            for l in item['locator'].split(';'):
                if l and '=' not in l:
                    errors.append(f'第{i}条: locator 未按 <策略>=<值> 格式（如 id=btn_login）')
    if errors:
        print('\n'.join(errors)); sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
```

**外部连接信息（示例）**

| 项 | 示例 | 注意 |
| --- | --- | --- |
| Appium Server 地址 | 环境变量 `APP_SERVER_BASE`（默认 http://127.0.0.1:4723） | 不硬编码进 prompt |
| 被测设备 | 环境变量 `TEST_DEVICE_UDID`（Android 用 `adb devices` 取得） | 不写进 prompt / 产物 / 日志 |
| 被测 App | 环境变量 `TEST_APP_APK`（APK/IPA 路径或 `appPackage`+`appActivity`） | 连接与启动前先验证一次 |
| 连通性 | 启动前 curl 探活 Appium Server 一次 | 已配置并验证通过 |

**文件访问边界（示例）**

- 可读：用户指定输入文件、`references/` 全部、项目源码（仅 Analyzer 与 Verifier）
- 可写：`artifacts/`、用户明确指定的输出路径
- 禁止：修改 `artifacts/` 之外任何已有文件；产物目录 `artifacts/` 已提前创建

**环境依赖（示例）**

`python 3.10+`；`pytest`；`Appium`（`pip install appium-python-client`，并安装 `appium` 服务端）；Android 还需 `adb` 与对应 SDK；iOS 需 `Xcode`。在 `SKILL.md` / `README` 写清，保证新机器能一键装好。

### 2.4 验收测试材料（决定能不能判断"做完了"）

| 用例 | 输入 | 预期 |
| --- | --- | --- |
| 正常路径（1 个） | "帮我给登录功能写测试用例"（标准需求文字） | 全流程走完，产出符合格式定义的 `test_cases.json` 与 `test_login.py` |
| 边界（1 个） | 一份含 200 个需求点的混合 PRD | G1 门禁触发，圈定范围并给出建议，不一次性硬生成全部 |
| 异常 a（1 个） | 损坏的 JSON 需求文件 | 明确报错（文件名 + 原因），不硬生成 |
| 异常 b（1 个） | 断开 Appium Server / 设备断连 | 报告地址 + 错误，请人工处理，不用假数据顶替 |

### 2.5 材料齐备核对单（勾选实例）

```
[√] 一句话任务定义 + 4 句触发原话
[√] 输入形态清单（含不支持形态及引导话术）
[√] 输出格式定义（字段、必填、落盘路径）
[√] 领域规范文档已放 references/
[√] few-shot 样例 3 组
[√] 校验脚本写好且三种输入各测过（退出码 0/1/2）
[√] 外部凭证在环境变量，连通性验证过
[√] 产物目录 artifacts/ 已建，读写边界已明确
[√] 验收用例 4 个（正常 / 边界 / 异常×2）
```

---

## 3 第 1 章实例：画设计图

### 3.1 判断：这个任务配不配用 Harness

原指南三条特征，占其二才值得上。本示例逐条对照：

| 特征 | 本示例对照 | 是否命中 |
| --- | --- | --- |
| 步骤多且能力类型不同 | 分析 / 实现 / 验证需要不同能力 | 是 |
| 有机器可检查的质量标准 | JSON 字段、platform / priority 枚举、id 格式、locator 格式可脚本校验 | 是 |
| 失败是常态，需结构化重试 | 元素定位失败、App 崩溃、设备断连需分类修复重试 | 是 |

结论：三条全命中，值得用 Harness。若只命中一条，一个普通 SKILL.md 单 Agent 流程就够。

### 3.2 拆角色（示例）

| 能力 | Agent | 类型 | 为什么 |
| --- | --- | --- | --- |
| 读需求 + 检索规范 + 查相邻案例 | Analyzer | 只读探索（Explore） | 只读，不写任何东西 |
| 按规范产出用例 JSON + Appium 脚本 | Implementer | 全能（general-purpose） | 要写文件 |
| 机械 + 语义审查、挑毛病 | Verifier | 全能（general-purpose） | 要跑命令；绝不能用 Implementer 兼任 |

判断标准应用：两个阶段若总是由同一批上下文完成、从不需要独立视角就合并；但实现与验证绝不能是同一个 Agent——自己查自己等于没查。

### 3.3 状态机流程图（示例，动笔前必画）

```
START -> ANALYZE -> 【G1 用户确认】 -> IMPLEMENT -> VERIFY -> JUDGE
  JUDGE:
    PASS             -> OUTPUT -> DONE
    FORMAT_VIOLATION -> IMPLEMENT(fix) -> VERIFY -> JUDGE（不计重试）
    FAIL             -> IMPLEMENT(retry_fix) -> VERIFY -> JUDGE（计入重试，上限 2）
    retry > 2        -> 停止，报告人类
```

设计时必须回答的四个问题（答案已填入本示例）：

- 哪几处需要用户确认？只有 G1（分析后、动手产出前）一处；G1 不通过回 ANALYZE 修正。
- 失败怎么分类？格式违规（字段 / 枚举 / id / locator）→ 走 fix 分支不计重试；运行失败（元素定位失败、App 崩溃、设备断连）→ 分类后按对应修复模式，计入重试。
- 重试上限是多少？2 次；纯格式问题修了就消失，不计入重试。
- 输入不认识 / 连接不通怎么办？明确报错请求人工，禁止硬生成。

### 3.4 定义产物契约（Agent 之间传什么文件）

| 产物 | 生产者 | 消费者 | 关键字段 |
| --- | --- | --- | --- |
| `artifacts/_analysis.md` | Analyzer | Implementer | 需求理解、参考案例、复用计划、完整代码上下文 |
| `artifacts/_verification.md` | Verifier | 总控 | status（通过 / 格式违规 / 失败）、错误分类、修复建议 |

原则：总控只读产物文件做判断，不听任何 Agent 的口头汇报。每个跨 Agent 传递的信息都必须落成文件、格式预先定死。

### 3.5 分工：哪些给脚本，哪些给 LLM

| 判断维度 | 交给谁 | 本示例 |
| --- | --- | --- |
| 可用代码精确判定的 | 脚本 | JSON 合法、必填字段、platform / priority 枚举、id 格式、locator 格式 |
| 需要理解语义的 | LLM | 需求理解、控件语义识别、断言语义、根因分析、修复建议 |
| 两者都涉及的 | 脚本先跑机械校验，LLM 再做语义审查，结论合并 | 反编造溯源：字段回查需求原文（语义）+ 格式校验（脚本） |

铁律：机械的交给脚本，语义的交给 LLM。

---

## 4 第 2 章实例：按步骤实现

### 4.1 Step1 建目录骨架（示例）

```bash
mkdir -p .claude/skills/mobile-app-test-automation/{references,scripts,agents,artifacts}
touch .claude/skills/mobile-app-test-automation/SKILL.md
```

```
.claude/skills/mobile-app-test-automation/
├── SKILL.md          <- 总控（第 2~4 步填充）
├── references/       <- mobile-test-spec.md、login_spec.md、order_spec.md、few-shot.md
├── scripts/          <- validate.py（机械校验）
├── agents/           <- analyzer.md、implementer.md、verifier.md
└── artifacts/        <- 产物中转站（_analysis.md、test_cases.json 等）
```

### 4.2 Step2 写 SKILL.md 头部（决定触发）

```markdown
---
name: mobile-app-test-automation
description: 根据手机 App 功能需求自动生成可运行的 Appium 自动化测试用例（JSON）与 Python 脚本，经机械校验后落盘。当用户说"帮我给『登录』写手机 App 自动化测试用例"、"根据这份 PRD 生成 Appium 自动化测试脚本"、"把这条需求转成可执行的 App 端自动化测试"、"补一下 XX 模块的回归用例"时使用。不适用：用户要求"执行 / 跑一遍测试" -> 用测试执行工具；"分析用例覆盖率" -> 用覆盖率分析 skill。
---
```

`description` 写法三要素（本示例均已填）：1）做什么 + 产出物；2）3~4 句用户真实的触发原话；3）不适用边界与分流规则。这是路由依据，缺一项都可能导致不触发或误触发。

### 4.3 Step3 写总控五要素（示例：总控最终写成什么样）

**要素一：角色定义（最重要的一段）**

```markdown
## 你的角色
你是流程总控，职责只有三件事：
1. 按状态机调度子 Agent 执行
2. 读取 artifacts/ 产物文件判断每步结果，决定下一步
3. 保证不跳步、不遗漏、不突破重试上限

默认不要自己分析需求、自己写用例代码、自己跑校验命令——这些交给子 Agent。
```

**要素二：子 Agent 列表（表格，含调度方式与产物）**

| 阶段 | prompt 文件 | 调度方式 | 职责 | 产物 |
| --- | --- | --- | --- | --- |
| 分析 | `agents/analyzer.md` | Agent 工具（subagent_type=Explore） | 读需求 + 检索 references + 查相邻案例 | `artifacts/_analysis.md` |
| 实现 | `agents/implementer.md` | Agent 工具（subagent_type=general-purpose） | 按分析结果生成 JSON + Appium 脚本 | `artifacts/test_cases.json` 等 |
| 验证 | `agents/verifier.md` | Agent 工具（subagent_type=general-purpose） | 机械 + 语义审查、跑校验 | `artifacts/_verification.md` |

`agent_type` 怎么选：只读探索型（Explore）给分析 Agent——大量读文件、检索，不写任何东西；全能型（general-purpose）给实现 / 验证 Agent——要写文件、跑命令。

**要素三：状态机（含重试计数）**

```markdown
## 状态机
START -> ANALYZE -> 【G1 用户确认】 -> IMPLEMENT -> VERIFY -> JUDGE
  PASS    -> OUTPUT -> DONE
  FORMAT_VIOLATION -> IMPLEMENT(fix) -> VERIFY -> JUDGE（不计重试）
  FAIL    -> IMPLEMENT(retry_fix) -> VERIFY -> JUDGE（计入重试）
  retry > 2 -> 报告失败，停止

重试计数：retry 初始 0；仅 FAIL 时 +1；上限 2 次。
用户交互：仅 G1 一处。G1 不通过则回 ANALYZE 修正。
```

**要素四：调度协议（每次调度传什么，具体到参数）**

```markdown
## 调度总则
1. 调度前先 Read 对应 agent prompt 文件的完整内容
2. 将 prompt 正文 + 用户输入 + 前序产物文件路径 拼进任务描述，通过 Agent 工具发出
3. 等待子 Agent 完成，读取其写入的产物文件（不听口头汇报）
```

**要素五：禁止行为清单（堵死每条偷懒路径）**

| # | 禁止 |
| --- | --- |
| 1 | 跳过分析直接实现；实现后不验证 |
| 2 | 总控亲自写用例 / 亲自跑校验 |
| 3 | 校验失败后不分类错误就盲目重试 |
| 4 | 重试超过 2 次继续自动执行 |
| 5 | Agent 间口头传信，不落 artifacts/ |
| 6 | 校验脚本报错时基于残缺输入硬生成 |
| 7 | 未经 G1 确认就开始产出最终文件 |

### 4.4 Step4 写子 Agent prompt（五段式，一份文件一个 Agent）

**`agents/analyzer.md`（示例）**

```markdown
# 角色
我是 Analyzer，唯一职责：把用户需求转成结构化分析报告，写入 artifacts/_analysis.md。

# 输入
- 用户需求原文（由总控在任务描述中给出）
- references/ 下的规范文档（按关键词映射表选取 1~2 份）

# 工作流程
1. 解析需求，拆成有序功能点（功能入口 / 操作步骤 / 预期结果）
2. 按关键词映射表读取对应 references/ 文档（如"登录"读 login_spec.md）
3. 检索项目相邻真实案例（test_login.py 等），提取可复用 Page Object 与 Appium 定位器
4. 对每一步标注：复用 / 扩展 / 新建 / 修改（修改需用户在 G1 审批）
5. 将全部实现所需上下文写入 _analysis.md（Page Object 类名、locator 策略、断言写法必须完整）
6. 返回消息中报告 _analysis.md 路径与摘要，等待用户确认

# 输出格式
artifacts/_analysis.md，章节固定：原始需求 / 参考资料 / 操作步骤 / 复用计划 / 代码上下文

# 约束
- 不写实现代码、不跑校验、不写最终产物
- "代码上下文"章节必须完整到 Implementer 无需再读项目源码
```

**`agents/implementer.md`（示例）**

```markdown
# 角色
我是 Implementer，唯一职责：按 _analysis.md 产出可运行的用例 JSON 与 Appium Python 脚本。

# 输入
- artifacts/_analysis.md（完整代码上下文，由总控提供路径）
- references/mobile-test-spec.md（命名、分层、Appium 定位器规范）

# 工作流程（分模式）
1. 首做（new）：按分析产出完整 test_cases.json 与 test_<module>.py
2. 修格式（fix）：仅按校验清单修正字段 / 枚举 / 命名 / locator，不重写内容
3. 修内容（retry_fix）：按失败分类定位根因后修正（如定位策略不对、平台差异）
4. 改已有函数前必须查 G1 审批清单；不在清单就停下报告

# 输出格式
- artifacts/test_cases.json（字段 id/title/module/platform/priority/precondition/steps/locator/assertion）
- artifacts/test_<module>.py（Page Object 分层，一个用例一个函数，含 Appium 断言）

# 约束
- 不自行改变需求范围；不修改 artifacts/ 之外任何已有文件
- 产出必须能通过 scripts/validate.py（退出码 0）
```

**`agents/verifier.md`（示例）**

```markdown
# 角色
我是 Verifier，唯一职责：对产物做机械 + 语义审查并写 _verification.md。

# 输入
- artifacts/test_cases.json、test_<module>.py
- references/mobile-test-spec.md（用于语义核验）

# 工作流程
1. 先跑机械校验：cat test_cases.json | python3 scripts/validate.py，记录退出码与违规清单
2. 再做语义审查：断言是否对应需求原文、Appium 定位器是否合理（反编造溯源）
3. 分类错误：格式违规 / 运行失败（元素定位失败、App 崩溃、设备断连）等
4. 写 _verification.md，日志 / 报告完整不截断

# 输出格式
artifacts/_verification.md，字段：status（通过 / 格式违规 / 失败）、错误分类、修复建议

# 约束
- 只审查，绝不修改任何产物（验证者绝不动手改）
- 报告必须完整，不截断
```

三个 Agent 设计要点：Analyzer 产出要完整到下游免读源码、"修改已有文件"必须标出供审批；Implementer 分模式（首做 / 修格式 / 修内容）、改已有函数前查审批清单；Verifier 先跑脚本机械校验再做语义审查、报告不截断、绝不修改任何产物。

### 4.5 Step5 实现三类"复杂操作"的写法（示例）

**A. 工具调用（跑脚本）—— SKILL.md 中写明精确命令与退出码语义**

```markdown
## 机械校验
将产物的 JSON 表示传入校验脚本：

    cat artifacts/test_cases.json | python3 .claude/skills/mobile-app-test-automation/scripts/validate.py

退出码：0=全部合规；1=违规（清单打到 stdout，逐条修正后重跑）；2=输入错误。
```

对应脚本的最小骨架见 2.3 节的 `validate.py`。

**B. 文件访问 —— 明确读写边界，产物统一走 artifacts/**

```markdown
## 文件访问规则
- 可读：用户指定的输入文件、references/ 全部、项目源码（仅 Analyzer 与 Verifier）
- 可写：artifacts/ 下的产物文件、用户明确指定的输出路径
- 禁止：修改 artifacts/ 之外任何已有文件（Implementer 修改已有函数须走审批清单）
```

**C. 外部连接访问 —— 凭证进环境变量，连接失败必须走兜底**

```markdown
## 外部接口调用
- Appium Server 地址：从环境变量 APP_SERVER_BASE 读取（默认 http://127.0.0.1:4723）
- 被测设备 / App：从环境变量 TEST_DEVICE_UDID、TEST_APP_APK 读取
- 禁止在 prompt、产物文件、日志中出现凭证明文
- 连接失败 / 超时 / 设备断连：报告具体错误（地址 + 失败原因），请求用户提供网络、设备或凭证；禁止用猜测数据代替真实响应
```

```bash
# SKILL.md 中的调用写法（凭证不落盘）
curl -sS "$APP_SERVER_BASE/status"   # 探活 Appium Server
adb devices                          # 确认被测设备已连接
```

### 4.6 Step6 写异常兜底表（示例）

把能想到的异常场景逐条列进 SKILL.md，行为只有一种正确姿势——报错 + 请求人工，禁止硬生成。

| 场景 | 行为 |
| --- | --- |
| 无任何输入 / 输入形态不支持 | 列出支持的形态请求提供；含糊口语引导补充功能入口 / 步骤 / 预期 |
| 文件损坏 / JSON 解析失败 | 明确报错（文件名 + 原因）；禁止基于残缺内容猜测 |
| 两个来源信息冲突（PRD 与接口文档） | 不擅自取舍，列入 G1 提问清单请用户裁决 |
| Appium Server 不通 / 设备断连 / App 未启动 | 报告地址 + 错误，请求人工处理；不用假数据顶替 |
| 元素定位失败（元素不存在 / 平台差异） | 明确报错（定位策略 + 页面快照线索）；按失败分类走修复分支 |
| 校验连续 2 次不过 | 停止，呈现违规清单与已尝试的修复，请人工介入 |

### 4.7 Step7 写质量自检清单（SKILL.md 最后一节）

```markdown
## 输出前自检
1. 机械校验退出码为 0（或违规项已全部修正）
2. 每条用例的关键内容可溯源到需求原文（语义自查）
3. G1 门禁已通过（或用户明确豁免，输出标注"未经人工确认"）
4. 产物已落盘到 artifacts/，格式与定义一致
5. 全程未发生禁止行为清单中的任何一条
```

---

## 5 第 3 章实例：测试与迭代

用第 0 章准备的 4 个验收用例按顺序跑（正常 → 边界 → 异常 a → 异常 b）。每个用例跑完检查三件事：状态机走位正确吗（有无跳步、重试是否超限、G1 是否拦住）；产物契约被遵守了吗（打开 `artifacts/`，格式与定义一致）；禁止行为被触碰了吗（有无自己动手、口头传信、截断日志）。

| 顺序 | 用例 | 喂给 Skill 的输入 | 期待走位 | 关键检查点 |
| --- | --- | --- | --- | --- |
| 1 | 正常路径 | "帮我给登录功能写手机 App 自动化测试用例" | ANALYZE→G1→IMPLEMENT→VERIFY→PASS→OUTPUT | `test_cases.json` 全字段合规、`validate.py` 退出码 0 |
| 2 | 边界 | 含 200 需求点的混合 PRD | ANALYZE 后 G1 触发圈定 | G1 拦住，给出范围建议，未硬生成 |
| 3 | 异常 a | 损坏的 JSON 需求文件 | ANALYZE 阶段报错 | 明确报错（文件名 + 原因），未硬生成 |
| 4 | 异常 b | 断开 Appium Server / 设备断连 | 连接阶段报错 | 报告地址 + 错误，请人工，未编造 |

发现问题的修法：优先改 SKILL.md 的规则表述（更具体、更可判定），其次改 agent prompt，最后才考虑加脚本。每轮只改一处，重跑验收，避免改了 A 坏了 B。

---

## 6 附：可直接抄的 SKILL.md（手机 App 端 Appium 填充完整版）

把下面这份已经按本示例填好的 SKILL.md 直接放进 `.claude/skills/mobile-app-test-automation/SKILL.md`，再把 `references/`、`scripts/`、`agents/` 三个子目录补齐，就是一个能跑的最小 Harness Skill。

```markdown
---
name: mobile-app-test-automation
description: 根据手机 App 功能需求自动生成可运行的 Appium 自动化测试用例（JSON）与 Python 脚本，经机械校验后落盘。当用户说"帮我给『登录』写手机 App 自动化测试用例"、"根据这份 PRD 生成 Appium 自动化测试脚本"、"把这条需求转成可执行的 App 端自动化测试"、"补一下 XX 模块的回归用例"时使用。不适用：要求"执行 / 跑一遍测试" -> 用测试执行工具；"分析用例覆盖率" -> 用覆盖率分析 skill。
---

# mobile-app-test-automation

## 你的角色
你是流程总控，职责只有三件事：
1. 按状态机调度子 Agent 执行
2. 读取产物文件判断结果，决定下一步
3. 保证不跳步、不遗漏、不突破重试上限
默认不要自己分析需求、自己写用例、自己跑校验，交给子 Agent。

## 子 Agent
| 阶段 | prompt 文件 | 类型 | 职责 | 产物 |
|------|------------|------|------|------|
| 分析 | agents/analyzer.md | 只读探索 | 读需求 + 检索规范 | artifacts/_analysis.md |
| 实现 | agents/implementer.md | 全能 | 生成 JSON + Appium 脚本 | artifacts/test_cases.json 等 |
| 验证 | agents/verifier.md | 全能 | 机械 + 语义审查 | artifacts/_verification.md |

## 状态机
START -> ANALYZE -> 【G1 用户确认】 -> IMPLEMENT -> VERIFY -> JUDGE
  JUDGE: PASS -> 输出 -> DONE
         FORMAT_VIOLATION -> IMPLEMENT(fix) -> VERIFY -> JUDGE（不计重试）
         FAIL -> IMPLEMENT(retry_fix) -> VERIFY -> JUDGE（计入重试，上限 2）

## 机械校验
    cat artifacts/test_cases.json | python3 .claude/skills/mobile-app-test-automation/scripts/validate.py
退出码：0=合规；1=违规（stdout 清单）；2=传参错误。

## 文件访问
- 可读：输入文件、references/、项目源码（仅 Analyzer 与 Verifier）
- 可写：artifacts/、用户指定输出路径
- 禁止：修改其他已有文件

## 外部连接
- Appium Server 地址从环境变量 APP_SERVER_BASE 读取；设备 / App 从 TEST_DEVICE_UDID、TEST_APP_APK 读取，禁止明文落盘
- 连接失败 / 设备断连：报告地址 + 错误，请求人工；禁止编造响应

## 异常兜底
| 场景 | 行为 |
|------|------|
| 输入缺失 / 不支持 | 列出支持形态请求提供 |
| 解析失败 | 报错（文件 + 原因），禁止硬生成 |
| Appium 不通 / 设备断连 / App 未启动 | 报告地址 + 错误，请求人工 |
| 校验 2 次不过 | 停止，呈现清单，请人工介入 |

## 禁止行为
1. 跳过分析直接实现；实现后不验证
2. 总控亲自实现 / 亲自跑校验
3. 盲目重试；超过 2 次继续执行
4. Agent 间口头传信不落盘
5. 未经 G1 确认产出最终文件

## 输出前自检
1. 机械校验退出码 0
2. 语义溯源完成
3. G1 已通过或已标注豁免
4. 产物落盘、格式一致
```

---

## 7 新手八坑在本示例中的对照

| # | 原指南的坑 | 本示例的防法 |
| --- | --- | --- |
| 1 | 跳过材料准备直接写 SKILL.md | 按第 2 章核对单齐备后再动笔 |
| 2 | description 不写触发原话 | 头部含 4 句触发原话 + 不适用边界 |
| 3 | 总控里写实现细节 | 细节进 agent prompt，规范进 references/ |
| 4 | 产物契约没有固定格式 | _analysis / _verification 字段预先定死 |
| 5 | 实现者和验证者是同一个 Agent | Verifier 独立，绝不兼任 |
| 6 | 把语义压给脚本、机械压给 LLM | 按 3.5 分工表执行 |
| 7 | 异常路径没写 | 4.6 兜底表是防编造的最后一道墙 |
| 8 | 一次改一堆规则 | 每轮只改一处，重跑 4 个验收用例 |

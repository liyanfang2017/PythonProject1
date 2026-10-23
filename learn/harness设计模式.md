第 0 章：什么是 Harness 设计模式？
在星球的过往文章中，其实已经介绍了很多编写skill的技巧，而把他们组合起来，其实就是Harness了。 其实Harness没有一个业界规定好的，固定的规范， 一切让智能体运行的更稳定，高效，准确的方法，其实都算作Harness的实践方法。所以Harness是一个方法论，而不是一个固定的实现规范。 我在这篇文章中介绍的， 也只是比较常见的一些设计技巧。

0.1 从「马具」说起
Harness 这个词，英文原意是「马具」——套在马身上、控制马匹方向和力量的一套装置。

在 AI 工作流领域，Harness 设计模式借用了同样的比喻：

用一套结构化的「约束装置」，把强大但方向不稳定的 AI 能力，精确地引导到正确的轨道上，让它高效、稳定、准确地完成复杂任务。

AI 本身很强大，就像一匹快马。但如果没有 Harness，它可能：

走错方向（做了你没让它做的事）
中途卸力（跳过某些步骤，比如你希望它执行测试， 但它为了完成任务， 直接跳过测试步骤， 甚至直接修改测试用例，强行通过。我见过一个同事， 他经历过AI直接改了需求工单，就为了能通过本次任务）
跑飞了收不回来（进入无限循环或过度生成）
Harness 不是限制 AI，而是给 AI 提供明确的结构，让它的能量用在对的地方。

0.2 Harness 的四个核心要素
我认为一个Harness 至少应该由四个部分组成：

┌─────────────────────────────────────────────────┐
│                   HARNESS                        │
│                                                  │
│  ① 角色边界    → 每个 Agent 只做一件事           │
│  ② 状态机（工作流） → 定义流程走向，防止跳步          │
│  ③ 产物契约    → Agent 间用文件传递，不靠记忆     │
│  ④ 护栏规则    → 明确禁止清单，防止越权          │
│                                                  │
└─────────────────────────────────────────────────┘
① 角色边界（Role Boundary）
每个参与工作流的 Agent，都只被授权做一件明确定义的事。

没有 Harness 的情况：
你对 AI 说「帮我写测试」，它同时在分析需求、写代码、还顺手改了几个旧文件。你根本不知道它改了什么。

有 Harness 的情况：
分析 Agent 只能读文件、产出分析报告，它没有权限写代码。实现 Agent 只能按照分析报告写代码，它没有权限运行测试。每个 Agent 的边界清晰，行为可预测。

② 状态机（State Machine）
Harness 不是简单的「一步接一步」，而是一张完整的状态转移图，涵盖正常路径和所有异常路径。

正常路径：A → B → C → 完成
异常路径：C 失败 → 分类错误 → 选择修复策略 → 回到 B → C → 再判断
上限保护：失败超过 N 次 → 停止，报告给人类
有了状态机，AI 遇到失败时不会「不知道该怎么办」，也不会无限循环。

③ 产物契约（Artifact Contract）
Agent 之间的信息传递，不能依赖对话上下文（对话会被截断、遗忘），必须通过写入文件来传递。

每个 Agent 的输出格式在 Harness 里预先约定好：

分析 Agent 输出 _analysis.md，格式固定
验证 Agent 输出 _verification.md，格式固定
总控通过读取这些文件来做判断，不依赖 Agent 的口头汇报
这让整个工作流可审查、可重放、可调试。

④ 护栏规则（Guard Rails）
Harness 的最后一道防线：明确列出每个 Agent 绝对不能做的事。

这不是因为不信任 AI，而是因为 AI 在面对复杂问题时，有时会「走捷径」——比如实现 Agent 为了让测试通过，悄悄修改了一个已有的 Page 方法，破坏了其他 10 个测试。护栏规则明确禁止这种行为。

0.3 Harness vs 普通提示词，差别在哪？
很多人用 AI 辅助工作时，习惯写一段很长的提示词，把所有要求都塞进去。这和 Harness 有什么区别？

维度	普通提示词	Harness 设计模式
结构	单个 Agent，线性执行	多个专职 Agent，状态机调度
信息传递	靠对话上下文（容易丢失）	靠 Artifact 文件（持久可查）
错误处理	失败了重新说一遍	分类错误，选择对应修复模式
越权防护	没有，AI 可能做额外的事	有护栏规则，行为可预测
可维护性	提示词改一处，影响所有逻辑	每个 Agent prompt 独立维护
适用规模	简单、一次性任务	复杂、重复执行的工作流
普通提示词适合「帮我写一段代码」这样的一次性任务。Harness 适合「每次有新需求，都要走完分析→实现→验证流程」这样需要反复、可靠执行的工作流。

0.4 UI 自动化测试为什么特别适合 Harness？
UI 自动化测试有三个特点，让它天然适合用 Harness 来管理：

1. 步骤多，分工明确
分析需求、扫描代码库、写代码、跑测试、分析失败——这五件事的技能要求完全不同，天然适合拆给不同的 Agent。

2. 有现成的质量标准
代码分层规范、AI 定位方式、命名规范——这些都是可以被机器检查的约束，可以直接写进 Verifier Agent 的护栏规则里。

3. 失败是常态，需要结构化的修复流程
UI 测试不可能第一次就100%通过。Harness 的状态机可以优雅地处理「失败→分析→修复→重试」这个循环，而不是每次都要人工介入。

0.5 我的这个UI自动化测试的 Harness 长什么样？
接下来的章节会教你从零设计下面这套完整的 Harness：

┌──────────────────────────────────────────────────────────┐
│                   UI 自动化 Harness                        │
│                                                           │
│  SKILL.md（总控状态机）                                    │
│       ↓ 调度                                              │
│  [Analyzer]  ──→  _analysis.md  ──→  [Implementer]       │
│                                           ↓               │
│  [Verifier]  ←──  源码变更  ←────────────┘               │
│       ↓                                                   │
│  _verification.md  ──→  总控判断  ──→  完成 / 修复重试    │
│                                                           │
└──────────────────────────────────────────────────────────┘
SKILL.md：Harness 的总控，定义状态机和调度规则
三个 Agent prompt：分别定义角色边界和护栏规则
两个 Artifact 文件：产物契约，Agent 间的信息中转站
需要说明的是， 我使用的是字节的midsence UI自动化测试框架。 支持在后台配置一个多模态大模型做视觉理解（我使用的是千问VL3.5）。关于这个框架的底层原理， 使用API教程等，我在星球的前几篇文章中都有写过。 大家可以自行去翻阅。

理解了上面这些，你就理解了整篇教程的核心。

第 1 章：为什么一个 AI 搞不定测试？
1.1 先从一次失败的尝试说起
假设你第一次尝试用 AI 写 UI 自动化测试，你对 AI 说：

"帮我写一个测试：打开应用列表，点击新建按钮，填入名称，保存，验证应用出现在列表里。"

AI 可能给你生成了一段代码，看起来像那么回事。但你跑起来——失败了。

问题可能是：

AI 不知道你项目里的页面对象叫什么、方法签名是什么
生成的代码把定位逻辑直接写在了测试文件里（违反了你们的分层规范）
生成了 CSS 选择器，但那个元素在你们的 UI 框架里根本没有稳定的选择器
测试结构和你们已有的测试用例风格完全不一样，没法合并
根本原因：你把一件需要「调研 → 实现 → 验证」三种不同能力的事情，全部丢给了一个 Agent，它没有足够的上下文，也没有自我纠错的机制。

1.2 三件事，三种能力
写一个合格的 UI 自动化测试，实际上需要三种截然不同的能力：

阶段	核心能力	问题
分析	读懂需求、扫描代码库、判断复用边界	"现有代码覆盖了哪些步骤？哪些要新写？"
实现	按规范写代码、遵守分层约束、输出可运行文件	"怎么写才符合项目架构？"
验证	运行测试、看日志、看截图、分析根因	"跑失败了是哪里出问题？"
如果让一个 Agent 承担全部三件事，它会在「分析和实现之间反复横跳」，或者「实现完了不去跑验证就宣布完成」。

1.3 解决方案：流水线 + 职责分离
把三种能力分给三个专职 Agent，由一个总控（Harness）按顺序调度。这就是本教程要教你设计的东西：

用户说需求
    ↓
[总控 Harness]
    ↓ 调度
[分析 Agent] → 产出分析报告
    ↓ 确认
[实现 Agent] → 写测试代码
    ↓
[验证 Agent] → 跑测试 + 分析结果
    ↓
判断是否通过 → 通过则完成 / 失败则修复重试
第 2 章：认识这套多 Agent 架构
在本项目里，这套架构已经实现。我们先整体了解它，再学如何自己设计。

2.1 四个核心文件
docs/codex/ui-automation/
├── SKILL.md                  ← 总控指令（Harness），告诉主 Agent 如何调度
├── agents/
│   ├── analyzer-agent.md     ← 分析 Agent 的 prompt
│   ├── implementer-agent.md  ← 实现 Agent 的 prompt
│   └── verifier-agent.md     ← 验证 Agent 的 prompt
└── artifacts/
    ├── _analysis.md          ← 分析结果（Agent 间传递信息的中转站）
    └── _verification.md      ← 验证结果（同上）
关键概念：Artifact（产物文件）
Agent 之间不靠口头对话传递信息，而是通过文件。分析 Agent 把结论写进 _analysis.md，实现 Agent 读这个文件来编写代码；验证 Agent 把结论写进 _verification.md，总控读这个文件来判断下一步。
这样设计的好处：信息不会在多轮对话中丢失，每次都能读到完整上下文。

2.2 状态机：总控的核心逻辑
总控不是随机调度，而是按状态机运行。你可以把它理解成一张流程图：

START
  ↓
ANALYZE（分析）
  ↓ [用户确认]
IMPLEMENT（实现）
  ↓
VERIFY（验证）
  ↓
JUDGE（判断）
  ├── ✅ 通过 → DONE（完成）
  ├── ARCHITECTURE_VIOLATION → IMPLEMENT(architecture_fix) → VERIFY → JUDGE
  ├── AI_ONLY_VIOLATION      → IMPLEMENT(review_fix)       → VERIFY → JUDGE
  └── ❌ 失败（retry <= 2）  → IMPLEMENT(retry_fix)        → VERIFY → JUDGE
                  失败（retry > 2）  → 报告失败，停止
两个关键设计决策：

只有一个用户交互节点：在分析完成后、实现开始前，展示摘要让用户确认。其余流程全自动。这避免了 AI 频繁打断你。

错误分类驱动修复模式：验证失败时，不是简单重试，而是先分类错误（架构违规 / AI 定位规范违规 / 测试运行失败），再用不同的修复模式调度实现 Agent。这大大提高了修复的准确率。

2.3 项目的四层代码架构
这套 skill 是为特定的代码分层架构设计的。了解这个架构，才能理解 Agent 的规则是从哪里来的：

tests/（测试层）
  只能调用 ↓
services/（服务层）
  只能调用 ↓
pages/（页面层）
  只能调用 ↓
components/（组件层）
每层的职责：

层级	职责	禁止做的事
tests/	调用 Service、写 expect 断言	直接操作页面、直接调 AI 方法
services/	编排业务步骤，调 Page 方法	直接操作 DOM、直接调 AI 方法
pages/	封装页面交互，用 AI 定位元素	跨页面操作、写 expect
components/	封装通用 UI 控件	依赖 Page 或 Service
为什么要分这么多层？
当 UI 变了，你只需要改 Page 层，不用动 Service 层和测试层。当业务逻辑变了，你只改 Service 层。分层让变更影响范围最小化。

第 3 章：从零设计你的总控层（Harness）
现在开始实战。假设你要为自己的项目设计一套类似的多 Agent Skill，总控（SKILL.md）怎么写？

3.1 总控的五要素
一个好的总控文件必须包含这五部分：

要素	作用	对应本项目
角色定义	告诉主 Agent 它是总控，不要自己做实现	"你是流程总控，只负责调度"
子 Agent 列表	列出每个子 Agent 的职责和产物	三个 Agent 的表格
状态机	定义流程走向和跳转条件	START→ANALYZE→IMPLEMENT→VERIFY→JUDGE
调度细则	每次调度子 Agent 时传什么参数	spawn_agent 的调用示例
禁止行为	防止主 Agent 越权	8 条禁止清单
3.2 第一步：写角色定义
角色定义是整个文件最重要的一句话。它决定了主 Agent 有没有「越权」的冲动。

反面示例（模糊）：

你是一个帮助用户写测试的 AI 助手。
这样写，AI 会自己动手写测试代码，而不是去调度子 Agent。

正面示例（本项目的写法）：

## 你的角色

你是流程总控。在这个工作流里，你的职责只有三件事：
1. 调度三个子 Agent 按正确顺序执行
2. 判断每个 Agent 的输出，决定下一步
3. 保证不跳步、不遗漏、不突破重试上限

默认不要在这个工作流里自己做需求分析、直接改测试代码、或自己跑验证命令；这些工作交给子 Agent 完成。
写法要点：
- 用列表明确列出「你的职责只有 N 件事」
- 在最后用一行反向约束：「默认不要自己做 X / Y / Z」
- 越具体越好，不要留模糊空间

3.3 第二步：设计状态机
状态机是总控的大脑。画清楚状态流转，AI 才不会在循环里迷失。

模板框架：

## 状态机

​```text
START -> [阶段1] -> [阶段2] -> [阶段3] -> JUDGE
                                       |
                                       +-> DONE（成功条件）
                                       |
                                       +-> [阶段2(修复模式A)] -> [阶段3] -> JUDGE
                                       |
                                       +-> [阶段2(修复模式B)] -> [阶段3] -> JUDGE
                                       |
                                       +-> FAILED（失败上限）
​```

### 重试计数

- retry 初始值为 0
- [不计入重试的情况] 不计入重试
- 仅当 [真正的失败条件] 时，retry += 1
- 最多自动重试 [N] 次
关键决策：什么情况不计入重试？

本项目把「架构违规」和「AI 定位规范违规」排除在重试计数之外，原因是：这两类错误是代码质量问题，修复后理论上就消失了，不会反复出现。只有「测试运行失败」才计入重试，因为这可能是环境问题或 AI 定位不准，需要限制次数。

3.4 第三步：定义调度协议
每次调用子 Agent，需要规定「传什么」。这部分要具体到参数级别。

模板：

## 调度总则

### 子 Agent 启动前

1. 读取对应 prompt 文件完整内容。
2. 将 prompt 正文与本轮输入上下文拼接后，通过 spawn_agent 发给子 Agent。
3. 等待子 Agent 完成；必要时用 send_input 补充信息。

### [Agent 名称] 调度参数

​```
spawn_agent(
  agent_type="[explorer/worker]",
  fork_context=true,
  message=[
    [Agent] prompt 完整内容
    + 用户需求
    + [其他必要上下文]
  ]
)
​```
agent_type 选哪个？

类型	适合场景
explorer	需要大量读文件、搜索代码库（分析 Agent）
worker	需要写代码、执行命令（实现 Agent、验证 Agent）
3.5 第四步：写禁止行为清单
这是防止 AI「越权」的最后一道防线。禁止清单要能覆盖所有可能的「走捷径」行为。

思路：逐一列举每个可能的偷懒路径

## 禁止行为

| # | 禁止 |
|---|------|
| 1 | 跳过 [分析阶段] 直接进入 [实现阶段] |
| 2 | [实现阶段] 完成后不调 [验证阶段] |
| 3 | 在工作流里由主 Agent 直接亲自写测试代码 |
| 4 | 在工作流里由主 Agent 直接亲自跑测试 |
| 5 | 在 [实现→验证→判断] 循环中因非 [指定原因] 向用户确认 |
| 6 | 测试失败超过 [N] 次后继续自动重试 |
| 7 | 跨 Agent 只口头传递信息，不写入 artifact |
3.6 完整总控模板
把以上四步组合，就得到一个可直接复用的总控模板：

# [项目名] UI 自动化测试 - 多 Agent Skill

> [一句话描述：这个 Skill 在什么情况下被调用]

---

## 你的角色

你是流程总控。在这个工作流里，你的职责只有三件事：
1. 调度三个子 Agent 按正确顺序执行
2. 判断每个 Agent 的输出，决定下一步
3. 保证不跳步、不遗漏、不突破重试上限

默认不要在这个工作流里自己做需求分析、直接改测试代码、或自己跑验证命令。

---

## 三个子 Agent

| 阶段 | 文件 | 推荐 agent_type | 职责 | 产物 |
|------|------|----------------|------|------|
| 分析 | `docs/.../analyzer-agent.md` | `explorer` | 解析需求、扫描代码、产出复用计划 | `_analysis.md` |
| 实现 | `docs/.../implementer-agent.md` | `worker` | 根据分析结果生成或修复代码 | 源码变更 |
| 验证 | `docs/.../verifier-agent.md` | `worker` | 审查架构、运行测试、输出验证报告 | `_verification.md` |

---

## 状态机

​```text
START -> ANALYZE -> IMPLEMENT -> VERIFY -> JUDGE
                                       |
                                       +-> DONE
                                       |
                                       +-> IMPLEMENT(architecture_fix) -> VERIFY -> JUDGE
                                       |
                                       +-> IMPLEMENT(retry_fix) -> VERIFY -> JUDGE
​```

### 重试计数

- retry 初始值为 0
- ARCHITECTURE_VIOLATION 不计入重试
- 仅当验证报告状态为 ❌ 失败时，retry += 1
- 最多自动重试 2 次
- 超过 2 次仍失败，结束并向用户报告

---

## 调度总则

[调度参数细节]

---

## 完整执行流程

### 阶段 1：分析（ANALYZE）
[步骤描述]

### 阶段 2：实现（IMPLEMENT）
[步骤描述]

### 阶段 3：验证（VERIFY）
[步骤描述]

### 阶段 4：判断（JUDGE）
[各状态处理逻辑]

---

## 禁止行为

[禁止清单]
第 4 章：手把手写三个 Agent Prompt
总控写好了，下面分别设计三个子 Agent 的 prompt。每个 prompt 都有固定的结构。

4.1 通用 Prompt 结构
每个子 Agent 的 prompt 文件都应包含：

1. 角色定义     → 告诉 Agent 它是谁、它的唯一职责是什么
2. 输入         → 它接收什么（文件路径、参数等）
3. 工作流程     → 步骤编号的执行顺序
4. 输出格式     → 产物文件的精确格式（用 Markdown 代码块给出模板）
5. 约束         → 绝对不能做的事
4.2 分析 Agent（Analyzer）的写法
核心任务：把用户的自然语言需求，变成实现 Agent 可以直接使用的结构化文档。

关键设计原则：让下游 Agent 不需要再读源码

分析 Agent 产出的 _analysis.md 必须足够完整，使得实现 Agent 在「首次实现」模式下，不需要自己去翻项目源码。这是最重要的一条原则，它：

加快速度：实现 Agent 不用重复扫描代码库
减少错误：信息经过分析 Agent 过滤，更精准
便于审查：用户在确认节点能看到清晰的复用计划
分析 Agent prompt 的核心步骤：

## 工作流程

### 第一步：解析需求
将用户描述转成有序步骤。每步标注：
- 所属 Page 类或 Service 类
- 操作类型：输入、点击、导航、验证、提取

### 第二步：匹配最佳实践文档
先读 [你的最佳实践目录]/README.md。
根据需求关键词，选择 1-2 份文档：
[关键词 → 文档 的映射表]

### 第三步：确定测试目录并读取相邻 case
[你的测试目录映射表]
读 1-3 个最相关的现有测试文件，提取：
- Service 的实例化方式
- import 路径模式
- 测试数据生成方式
- 步骤组合模式

### 第四步：扫描代码库
扫描 components/、pages/、services/ 下的文件，提取类名和公共方法。

### 第五步：复用分析
对每个步骤标记：复用 / 扩展 / 修改 / 新建

> 「修改」需要标出来供用户审批，「扩展」和「新建」不需要

### 第六步：输出 _analysis.md
复用分析的四个标记，为什么这样设计？

标记	含义	是否需要用户确认
复用	直接用，不改任何代码	否
扩展	在现有文件里新增方法	否（不改旧代码）
新建	创建新文件	否
修改	改动已有方法	是（破坏性变更）
这个设计的核心思路是：「加法」不需要审批，「改法」需要审批。新增代码不会影响现有功能，修改已有代码可能破坏已有测试。

_analysis.md 的输出格式模板（关键部分）：

# 需求分析结果

## 原始需求
[用户原文]

## 参考的最佳实践
- 模块：[模块名]
- 关键参考：[推荐的方法调用模式]

## 参考的相邻 Case
- 目录：[目录路径]
- 参考文件：[文件名及简述]

## 操作步骤
1. [PageClass] 操作描述
2. [PageClass] 操作描述

## 代码复用分析

### 可复用
| 步骤 | 现有代码 | 覆盖内容 |

### 需扩展
| 文件 | 新增内容 | 对应步骤 |

### 需新建
| 文件 | 用途 | 对应步骤 |

## 测试文件
- 目标文件：src/tests/xxx.test.ts

## 代码上下文（Agent 2 直接使用，无需重新读取源码）

### 需扩展文件的现有代码结构
[文件路径、类名、已有方法签名、插入位置建议]

### 相邻 Case 代码模式
[完整代码或关键片段]

### 测试文件模板
[基于相邻 case 推导出的模板]
最后一个约束（非常重要）：

## 约束

- 不执行任何测试
- 不启动浏览器
- 不写实现代码
- 必须让「代码上下文」章节足够完整，使 implementer 在 first_run 下无需再次读项目源码
4.3 实现 Agent（Implementer）的写法
核心任务：读取 _analysis.md，严格按照架构约束写出可运行的测试代码。

最重要的两个设计：运行模式 + 已有函数保护

设计一：四种运行模式
实现 Agent 不是每次都做同样的事，它有四种模式：

模式	触发时机	核心任务
first_run	首次实现	读 _analysis.md，按复用计划写代码
review_fix	AI 定位规范违规	修复 Page 方法里的定位方式
architecture_fix	架构分层违规	把定位逻辑移到正确的层
retry_fix	测试运行失败	读日志和截图分析，修复具体错误
在 first_run 模式下，实现 Agent 禁止读取项目源码文件。它只能使用 _analysis.md 里的「代码上下文」章节。这个约束的好处：

强制分析 Agent 把上下文准备好
防止实现 Agent 边分析边实现导致决策漂移
## first_run 的强约束

当运行模式为 first_run 时：
- 禁止读取 src/pages/*.ts、src/services/*.ts、src/tests/**/*.ts
- 需要的实现上下文全部来自 _analysis.md 的「代码上下文」章节
- 所有新增 Page 方法默认使用 AI-Only 模式
- 不写真实 CSS 定位逻辑
设计二：已有函数保护机制
这是整个 Skill 里最精妙的设计之一，专门用来防止 AI「偷偷改旧代码」。

问题背景：AI 在修复失败的测试时，有时会「顺手」修改已有的 Page 方法来解决问题。这很危险——那个方法可能被其他 10 个测试用例依赖，你改了之后其他测试全挂。

解决方案：approved_modifications + rejected_modifications 双清单

## 已有函数修改保护（最高优先级）

### 核心原则
任何对已存在函数的修改，必须经过用户明确确认。未经确认，禁止修改。

### 判断规则
1. 修改任何已存在的函数前，检查该函数是否在 approved_modifications 清单中
2. 若在 approved_modifications 中 → 允许修改
3. 若在 rejected_modifications 中 → 禁止，使用替代策略
4. 若两个清单都没有 → 禁止，在返回消息中报告，等待主 Agent 向用户确认

### 未预审批函数的报告格式

⚠️ 需要修改未预审批的已有函数：

| 文件 | 函数名 | 修改原因 | 修改内容摘要 |
|------|--------|---------|-------------|
| src/pages/XxxPage.ts | clickXxx() | 需要增加参数 | 添加 optional 参数 |

请用户确认后重新调度。

### 被拒绝时的替代策略

| 场景 | 替代方案 |
|------|---------|
| 需要给已有 Page 方法加参数 | 新增 clickXxxWithOptions()，保持原方法不变 |
| 需要修改已有 Service 编排逻辑 | 新增专用 Service 方法，不改原方法 |
withFallback + AI-Only 模式的代码模板：

这是本项目 Page 层的标准写法模板，需要在实现 Agent 的 prompt 里给出完整示例：

/**
 * [功能描述]
 * AI-Only（首次实现）
 */
async clickXxx() {
  await this.withFallback({
    label: "clickXxx()",
    cssAction: async () => false,   // 固定写 false，强制走 AI
    aiFallback: async () => {
      await this.getAgent().aiTap("[容器上下文]中的[文案][元素类型]");
    },
    aiOnly: true,                   // 固定写 true
  });
  await this.wait(500);
}
Service 层模板：

async doSomething(param: string) {
  await this.step(`操作描述: "${param}"`, async () => {
    await this.xxxPage.clickXxx();  // 只调 Page 方法
  });
}
// 禁止：this.page.locator(...)、this.getAgent().aiTap(...) 等
Test 层模板：

describe("功能描述", () => {
  const ctx = usePlaywrightWithAuth();

  test("测试用例名称", async () => {
    const svc = new XxxService(ctx.page);  // 只 new Service
    await svc.doSomething("参数");
    expect(result).toBe(expected);         // expect 只在 Test 层
  }, 180_000);
});
4.4 验证 Agent（Verifier）的写法
核心任务：做质量守门员——先审查代码合规性，再运行测试，最后写出能被实现 Agent 直接使用的失败分析报告。

关键设计：两层审查 + 截图分析

两层审查的顺序
## 工作流程

Step 1: 架构合规审查（不通过 → 立即输出 ARCHITECTURE_VIOLATION，不跑测试）
Step 2: AI-Only 合规审查（仅首轮，不通过 → 输出 AI_ONLY_VIOLATION，不跑测试）
Step 3: 运行测试
Step 4: 分类错误
Step 5: 分析截图（如有）
Step 6: 输出 _verification.md
为什么审查要在运行之前？

跑测试要花几分钟。如果代码里有明显的架构违规，先检查出来，避免浪费时间等测试跑完。

架构违规检查的实现
验证 Agent 需要对以下模式做静态检查（在测试层和服务层中查找禁止出现的代码）：

## Step 1：架构合规审查

只检查本轮新增或修改的文件。

### 测试层（src/tests/）禁止出现的代码模式
- page.evaluate(
- page.locator(
- page.click(
- .aiTap(
- .aiQuery(

### 服务层（src/services/）禁止出现的代码模式
- this.page.evaluate(
- this.page.locator(
- this.page.click(
- .aiTap(
- .aiAction(

若违规，立即输出 ARCHITECTURE_VIOLATION，停止，不运行测试。
截图分析的重要性
当测试失败且有截图时，截图往往比日志更直接地说明问题。验证 Agent 应该：

从日志里提取截图路径
读取截图
结合日志分析：页面处于什么状态、失败在第几步、根因是什么
这些信息写进 _verification.md 的「截图分析」章节，让实现 Agent 在修复时有更准确的方向。

_verification.md 的输出格式
验证 Agent 必须输出严格格式化的报告，因为总控要读取其中的状态字段来做判断：

# 验证报告

## 状态
[ARCHITECTURE_VIOLATION / AI_ONLY_VIOLATION / ✅ 通过 / ❌ 失败]

## 审查结果
- 架构合规：✅ 通过 / ❌ 违规

## 测试结果（仅通过审查时填写）
- 状态：✅ 通过 / ❌ 失败
- 测试文件：<文件路径>
- 通过/失败用例数：N

## 完整测试日志
```text
[完整 stdout + stderr，禁止截断]
错误详情（仅失败时填写）
错误 1
类型：[selector_not_found / timeout / logic_error / type_error / import_error / assertion_failed]
失败用例：
错误信息：...
截图分析（仅失败时填写）
截图路径：<路径或"截图不可用">
页面状态：<描述>
失败定位：<失败在第几步>
根因推断：<描述>
修复方向：<描述>
修复建议
[建议 1]
[建议 2]
**约束（非常重要）：**

```markdown
## 约束

- 不修改任何源码
- 不跳过架构审查直接跑测试
- 测试日志不要截断（完整日志是修复的依据）
- 报告中的错误分类、截图分析、修复建议要能直接被 implementer 使用
4.5 三个 Agent Prompt 设计总结
设计三个 Agent prompt 时，有一个核心原则贯穿始终：

每个 Agent 只做一件事，做完就输出产物文件，把决策权交回总控。

对照检查表：

检查项	Analyzer	Implementer	Verifier
角色定义清晰，只有一个职责	✅	✅	✅
输入来源明确（文件路径）	✅	✅	✅
工作步骤有编号	✅	✅	✅
输出格式有严格模板	✅	✅	✅
有「禁止」约束防止越权	✅	✅	✅
产物写入 artifact 文件	_analysis.md	源码	_verification.md
第 5 章：实操：让 AI 帮你写第一个测试
架构设计好了，现在学怎么用它。

5.1 你需要准备什么
在开始之前，确认以下文件都已存在：

docs/codex/ui-automation/
├── SKILL.md                      ← 总控
├── agents/
│   ├── analyzer-agent.md         ← 分析 Agent prompt
│   ├── implementer-agent.md      ← 实现 Agent prompt
│   └── verifier-agent.md         ← 验证 Agent prompt
└── artifacts/                    ← 空目录，AI 会自动写入
另外，.codebuddy/skills/adp-test/best-practices/ 目录下需要有对应的最佳实践文档，分析 Agent 会用到它们。

5.2 如何触发这套 Skill
在你的 AI 编码助手（如 CodeBuddy）中，触发这套 Skill 有两种方式：

方式一：自然语言描述测试步骤

请帮我写一个 UI 自动化测试，步骤如下：
1. 进入应用列表页面
2. 搜索名称包含 "test" 的应用
3. 验证搜索结果中出现了至少一条记录
方式二：参考已有测试，补充覆盖

参考 src/tests/app_dev/app-list/delete-app.test.ts，
帮我写一个类似的测试：验证复制应用功能。
AI 识别到 UI 测试需求后，会自动读取 SKILL.md 开始执行三阶段流程。

5.3 完整流程演示
以「搜索应用」测试为例，演示完整流程。

步骤 1：描述需求
你对 AI 说：

帮我写一个测试：进入应用列表，在搜索框输入 "autotest"，
验证结果列表中显示了包含该关键词的应用。
步骤 2：分析阶段（自动）
AI 调度分析 Agent，你会看到类似这样的输出：

[Analyzer] 正在扫描代码库...
[Analyzer] 读取最佳实践文档: app-list.md
[Analyzer] 读取相邻 case: search-app.test.ts, copy-app.test.ts
[Analyzer] 分析完成，写入 _analysis.md
然后，AI 展示摘要让你确认：

分析完成，复用计划如下：

步骤 1: [AppListPage] 导航到应用列表    → [复用] navigateToAppList()
步骤 2: [AppListPage] 输入搜索关键词    → [扩展] 需新增 searchByKeyword()
步骤 3: [AppListPage] 验证搜索结果      → [扩展] 需新增 verifySearchResult()

需新建文件：无
需扩展文件：src/pages/AppListPage.ts（新增 2 个方法）

请确认是否继续？
这个确认节点非常重要。 你看到的是：哪些功能已有、哪些需要新写、测试文件会在哪里。确认后才进入实现阶段。

步骤 3：实现阶段（自动）
AI 调度实现 Agent，自动在 AppListPage.ts 里新增两个 AI-Only 方法，并创建测试文件：

新增的 Page 方法（src/pages/AppListPage.ts）：

/**
 * 在搜索框中输入关键词
 * AI-Only（首次实现）
 */
async searchByKeyword(keyword: string) {
  await this.withFallback({
    label: "searchByKeyword()",
    cssAction: async () => false,
    aiFallback: async () => {
      await this.getAgent().aiInput(
        "应用列表页面顶部的「搜索应用」输入框",
        { value: keyword }
      );
      await this.getAgent().aiKeyboardPress(
        "应用列表页面顶部的「搜索应用」输入框",
        { keyName: "Enter" }
      );
    },
    aiOnly: true,
  });
  await this.wait(1000);
}

/**
 * 验证搜索结果中是否包含关键词
 * AI-Only（首次实现）
 */
async verifySearchResult(keyword: string): Promise<boolean> {
  let result = false;
  await this.withFallback({
    label: "verifySearchResult()",
    cssAction: async () => false,
    aiFallback: async () => {
      result = await this.getAgent().aiBoolean(
        `应用列表中是否存在名称包含「${keyword}」的应用条目`
      );
    },
    aiOnly: true,
  });
  return result;
}
对应的 Service 层：

// src/services/AppListService.ts（新增方法）
async searchApp(keyword: string): Promise<boolean> {
  await this.step(`搜索应用: "${keyword}"`, async () => {
    await this.appListPage.searchByKeyword(keyword);
  });

  let exists = false;
  await this.step("验证搜索结果", async () => {
    exists = await this.appListPage.verifySearchResult(keyword);
  });
  return exists;
}
生成的测试文件（src/tests/app_dev/app-list/search-app.test.ts）：

import "../../../setup/env";
import { describe, test, expect } from "vitest";
import { usePlaywrightWithAuth } from "../../../fixtures/playwright.fixture";
import { AppListService } from "../../../services";

describe("应用开发 - 应用列表操作", () => {
  const ctx = usePlaywrightWithAuth();

  /**
   * 测试步骤：
   * 1. 导航到应用列表
   * 2. 搜索 "autotest"
   * 3. 验证结果列表出现包含该关键词的应用
   *
   * 预期结果：搜索结果非空，且包含 "autotest" 关键词的应用
   */
  test("搜索应用 - 关键词匹配成功", async () => {
    const svc = new AppListService(ctx.page);
    const keyword = "autotest";

    await svc.navigateToAppList();
    const found = await svc.searchApp(keyword);

    expect(found, `搜索「${keyword}」应有匹配结果`).toBe(true);
  }, 180_000);
});
步骤 4：验证阶段（自动）
AI 调度验证 Agent：

先静态审查架构合规性——确认测试层没有直接操作 DOM，Service 层没有 AI 调用
检查 AI-Only 合规性——确认 Page 方法用了 cssAction: async () => false 和 aiOnly: true
运行测试：node scripts/run-test.js --maxWorkers=1 src/tests/app_dev/app-list/search-app.test.ts
步骤 5：判断结果
如果通过：

✅ 测试通过

- 测试文件：src/tests/app_dev/app-list/search-app.test.ts
- 通过用例数：1
- 执行时间：45s
- 重试次数：0
如果失败：

AI 自动分析失败原因，例如：

❌ 第 1 次失败

- 错误类型：timeout
- 根因：AI 定位描述「搜索应用」过于模糊，搜索框未找到
- 修复方向：增加容器上下文描述，改为「应用列表页面右上角的搜索输入框」
然后自动修复、重跑，最多两次。

5.4 测试数据命名规范
在测试里创建的数据（应用名、模板名等）必须遵守命名规范，防止测试数据污染生产数据：

// 推荐模板：名称以 _qta 结尾，总长度不超过 15 字符
const suffix = String(Date.now()).slice(-6);

const appName = `a_${suffix}_qta`;        // 例：a_628193_qta
const templateTitle = `t_${suffix}_qta`;  // 例：t_628193_qta
const nickname = `u_qta_${suffix}`;       // 例：u_qta_628193
原因：

_qta 后缀让测试数据在界面上一眼可识别，方便清理
时间戳后缀避免测试并发时命名冲突
总长度限制避免触发后端的字段长度校验
第 6 章：常见问题与进阶技巧
6.1 错误类型速查表
当测试失败时，根据错误类型选择对应的修复方向：

错误类型	典型日志特征	常见根因	修复方向
selector_not_found	element not found、locator resolved to 0	AI 描述太模糊或容器不对	在 AI 描述里加容器上下文、文案、元素类型
timeout	timeout exceeded	页面加载慢、弹窗未出现	增加 aiWaitFor() 等待特定状态
logic_error	运行时异常，但非定位问题	步骤顺序错误、依赖状态未就绪	调整步骤顺序或补充前置步骤
assertion_failed	expect 断言失败	实际值与预期不符	检查断言逻辑或等待时机
type_error	TypeScript 编译错误	类型不匹配、方法签名错误	直接修正类型定义
import_error	模块导入失败	路径错误或未从 index.ts 导出	修正导入路径，检查 index.ts 导出
6.2 AI 定位描述的好与坏
AI 定位描述的质量直接决定测试稳定性。一个好的描述要包含四个要素：

[容器上下文] + [视觉位置] + [文案] + [元素类型]
对照示例：

// ❌ 太模糊
await this.getAgent().aiTap("确定按钮");

// ✅ 包含四要素
await this.getAgent().aiTap("在「添加用户」弹窗底部右侧的「确定」按钮");
//                           └─容器上下文─┘  └─位置─┘   └─文案─┘  └─类型─┘

// ❌ 缺少容器（页面上有多个搜索框）
await this.getAgent().aiInput("搜索框", { value: keyword });

// ✅ 加上容器
await this.getAgent().aiInput("应用列表页面顶部的「搜索应用」输入框", { value: keyword });
6.3 AI 方法选择优先级
每次写 Page 方法时，先按这个顺序选方法：

输入文本    → aiInput()
点击元素    → aiTap()
滚动页面    → aiScroll()
按键盘      → aiKeyboardPress()
悬停        → aiHover()
双击        → aiDoubleClick()
读取数据    → aiQuery() / aiBoolean() / aiString() / aiNumber()
等待状态    → aiWaitFor()
验证        → aiAssert()
复杂复合操作 → aiAction()（最后手段）
绝对不要用 aiAction() 做单步操作，例如：

// ❌ 可以用 aiTap，不要用 aiAction
await this.getAgent().aiAction("点击确定按钮");

// ✅ 正确用法
await this.getAgent().aiTap("弹窗底部的「确定」按钮");
6.4 如何把这套架构迁移到你自己的项目
这套多 Agent Skill 不只适用于本项目。迁移到你自己的项目，需要修改以下几处：

第一步：定义你的代码分层架构

在架构参考文件（architecture-reference.md）里写清楚你的项目分层规则：每层允许做什么、禁止做什么。Verifier Agent 会用这个文件做静态审查。

第二步：建立最佳实践文档库

在 .codebuddy/skills/your-project/best-practices/ 里，按功能模块写文档：

best-practices/
├── README.md          ← 关键词 → 文档 的映射表
├── login.md           ← 登录相关测试的最佳实践
├── user-management.md ← 用户管理相关
└── ...
Analyzer Agent 会根据需求关键词选择读哪份文档。

第三步：更新测试目录映射

在 analyzer-agent.md 里，把「需求类型 → 推荐目录」的映射表改成你项目的目录结构。

第四步：更新测试命令

在 verifier-agent.md 里，把测试运行命令改成你项目的命令，例如：

# 本项目
node scripts/run-test.js --maxWorkers=1 <测试文件路径>

# 你的项目（示例）
npx playwright test <测试文件路径> --workers=1
第五步：调整 AI 方法 API

如果你的项目用的不是 Midscene，把 midscene-api-reference.md 里的 API 换成你实际使用的 AI 定位库的 API。

6.5 常见设计陷阱
陷阱一：总控文件写得太复杂

总控只需要「调度 + 判断」，不要在 SKILL.md 里写实现细节。如果某个 Agent 的工作流程很复杂，写在那个 Agent 自己的 prompt 文件里。

陷阱二：分析 Agent 没有输出完整上下文

分析 Agent 最容易犯的错误：_analysis.md 里的「代码上下文」章节写得太简略，实现 Agent 拿到后还要自己去读源码。正确做法：把方法签名、import 路径、代码片段都写进去。

陷阱三：验证 Agent 截断了测试日志

验证报告里的测试日志必须完整保留。实现 Agent 修复失败时，往往需要看日志的某个特定行，被截断就找不到了。

陷阱四：重试计数设置太大

如果允许重试 5 次、10 次，一个有问题的测试会让整个 Skill 运行很长时间。2 次是比较合适的上限：如果 3 轮（首次 + 2 次重试）还过不了，说明问题不是简单修一修能解决的，需要人工介入。

陷阱五：用户交互节点太多

总控里理想情况只有一个用户交互节点（分析完成后确认）。如果在每个步骤都停下来问用户，自动化的价值就大打折扣了。

总结
说一点点感想吧，最近社区有些冷清，我不太清楚大家在AI测试这条路上到底探索成了什么样子。但我周围的感受是，同事们很焦虑， 老板也很焦虑。 AI出来后大家都怕使用不好AI而淘汰。 这个AI来淘汰人类的趋势是很难违抗的，未来将会是特种兵+AI的协作模式。 这一点我深有感受，我现在干的活，在以前需要4,5个人才能完成。但现在只有我一个。而大家同样都是在用AI，我和少数的同事，负责的工作量又是其他人的两到三倍。特种兵+AI的格局已经形成，如果想不被淘汰，只能继续在这条路上走到黑了。 嗯， 不贩卖焦虑了， 大家加油吧。
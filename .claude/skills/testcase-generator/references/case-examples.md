# 示例用例集（few-shot）

生成用例时的表述基准。好例照此风格；坏例展示三类高频错误，生成时自查对照。

示例背景：接口维来自「用户管理 API」（`POST /api/users` 创建用户，`GET /api/users/{id}` 查询用户）；UI 维来自「登录页」PRD（控件：用户名输入框、密码输入框、登录按钮，文案：「账号或密码错误」「登录成功」）。

## 好例：接口维

```json
{
  "id": "TC_USER_001", "module": "用户管理", "title": "创建用户成功",
  "preconditions": "管理员已获取有效 token",
  "steps": "POST /api/users→请求体传入 username=alice、password=A1b2c3d4→发送请求",
  "expected": "返回 200，响应体包含 id 与 username=alice",
  "priority": "P0", "case_type": "正向", "dimension": "接口"
}
```

```json
{
  "id": "TC_USER_002", "module": "用户管理", "title": "创建用户时 username 为空",
  "preconditions": "管理员已获取有效 token",
  "steps": "POST /api/users→请求体 username 传空字符串、password=A1b2c3d4→发送请求",
  "expected": "返回 400，错误信息提示 username 不能为空",
  "priority": "P1", "case_type": "反向", "dimension": "接口"
}
```

```json
{
  "id": "TC_USER_003", "module": "用户管理", "title": "创建用户时 username 超过最大长度 32",
  "preconditions": "管理员已获取有效 token",
  "steps": "POST /api/users→请求体传入 33 位字符串作为 username→发送请求",
  "expected": "返回 400，错误信息提示 username 长度不能超过 32",
  "priority": "P1", "case_type": "边界", "dimension": "接口"
}
```

## 好例：UI 维

```json
{
  "id": "TC_LOGIN_001", "module": "登录", "title": "正确账号密码登录成功",
  "preconditions": "用户已注册且账号状态正常",
  "steps": "打开登录页→用户名输入框输入已注册账号→密码输入框输入正确密码→点击登录按钮",
  "expected": "页面跳转至首页，提示「登录成功」",
  "priority": "P0", "case_type": "正向", "dimension": "UI"
}
```

```json
{
  "id": "TC_LOGIN_002", "module": "登录", "title": "密码错误登录失败",
  "preconditions": "用户已注册且账号状态正常",
  "steps": "打开登录页→用户名输入框输入已注册账号→密码输入框输入错误密码→点击登录按钮",
  "expected": "页面停留登录页，提示「账号或密码错误」",
  "priority": "P1", "case_type": "反向", "dimension": "UI"
}
```

```json
{
  "id": "TC_LOGIN_003", "module": "登录", "title": "密码输入框边界长度 64 位密码",
  "preconditions": "用户已注册且账号状态正常",
  "steps": "打开登录页→密码输入框输入 64 位密码→用户名输入框输入已注册账号→点击登录按钮",
  "expected": "密码可完整输入且输入框内容以圆点显示，登录结果与密码正确性一致",
  "priority": "P2", "case_type": "边界", "dimension": "UI"
}
```

## 坏例对照（禁止模仿）

**坏例 1（编造控件）**

```json
{ "id": "TC_LOGIN_901", "module": "登录", "title": "人脸识别登录成功",
  "steps": "打开登录页→点击人脸识别登录按钮→完成刷脸", "expected": "登录成功",
  "priority": "P0", "case_type": "正向", "dimension": "UI" }
```

错在哪：PRD 与设计稿都没有「人脸识别登录按钮」，控件名是编造的。应改成：删除该用例，或在 G1/G2 提问清单中列出「PRD 未提及人脸识别登录，是否在范围内」，用户确认后才可生成。

**坏例 2（空泛预期）**

```json
{ "id": "TC_USER_902", "module": "用户管理", "title": "创建用户成功",
  "steps": "POST /api/users→传入合法参数→发送请求", "expected": "系统正常",
  "priority": "P0", "case_type": "正向", "dimension": "接口" }
```

错在哪：预期结果「系统正常」不可验证，属于质量红线。应改成：写明可观察结果，如「返回 200，响应体包含 id 与 username=alice」。

**坏例 3（一步多操作）**

```json
{ "id": "TC_LOGIN_903", "module": "登录", "title": "正确账号密码登录成功",
  "steps": "打开登录页并输入账号密码后点击登录按钮", "expected": "跳转首页",
  "priority": "P0", "case_type": "正向", "dimension": "UI" }
```

错在哪：一个步骤里塞了打开页面、输入、点击三个操作，无法定位失败环节。应改成：按 `→` 拆分，一步一个操作（见好例 TC_LOGIN_001）。

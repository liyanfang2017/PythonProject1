---
title: FastAPI Layered API
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
code_clipboard: true
highlight_theme: darkula
headingLevel: 2
generator: "@tarslib/widdershins v4.0.30"

---

# FastAPI Layered API

FastAPI 分层架构学习示例（9 接口版）：健康检查 / CRUD / 鉴权闭环 / 文件 I/O / 实时推送 / 复杂业务 / 聚合 / 回调集成。

Base URLs:

# Authentication

- HTTP Authentication, scheme: bearer

# auth

<a id="opIdauth_register_api_v1_auth_register_post"></a>

## POST 注册

POST /api/v1/auth/register

> Body 请求参数

```json
{
  "username": "string",
  "password": "stringst"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|body|body|[RegisterIn](#schemaregisterin)| 是 | RegisterIn|none|

> 返回示例

> 201 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|201|[Created](https://tools.ietf.org/html/rfc7231#section-6.3.2)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdauth_login_api_v1_auth_login_post"></a>

## POST 登录（签发双令牌）

POST /api/v1/auth/login

> Body 请求参数

```json
{
  "username": "string",
  "password": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|body|body|[LoginIn](#schemaloginin)| 是 | LoginIn|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdauth_refresh_api_v1_auth_refresh_post"></a>

## POST 刷新令牌（轮换）

POST /api/v1/auth/refresh

> Body 请求参数

```json
{
  "refresh_token": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|body|body|[RefreshIn](#schemarefreshin)| 是 | RefreshIn|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdauth_logout_api_v1_auth_logout_post"></a>

## POST 登出（撤销 refresh token）

POST /api/v1/auth/logout

> Body 请求参数

```json
{
  "refresh_token": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|body|body|[RefreshIn](#schemarefreshin)| 是 | RefreshIn|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdauth_me_api_v1_auth_me_get"></a>

## GET 当前用户信息

GET /api/v1/auth/me

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

# orders

<a id="opIdorders_create_api_v1_orders_post"></a>

## POST 创建订单（复杂业务）

POST /api/v1/orders

> Body 请求参数

```json
{
  "items": [
    {
      "product_id": 0,
      "quantity": 1
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|Idempotency-Key|header|any| 否 | Idempotency-Key|none|
|body|body|[OrderCreate](#schemaordercreate)| 是 | OrderCreate|none|

> 返回示例

> 201 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|201|[Created](https://tools.ietf.org/html/rfc7231#section-6.3.2)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdorders_statistics_api_v1_orders_statistics_get"></a>

## GET 订单统计报表（聚合 + 缓存）

GET /api/v1/orders/statistics

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|from|query|string(date)| 是 | From|none|
|to|query|string(date)| 是 | To|none|

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

### 返回数据结构

状态码 **422**

*HTTPValidationError*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|
|»» ValidationError|[ValidationError](#schemavalidationerror)|false|none|ValidationError|none|
|»»» loc|[anyOf]|true|none|Location|none|

*anyOf*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|string|false|none||none|

*or*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»»» *anonymous*|integer|false|none||none|

*continued*

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|»»» msg|string|true|none|Message|none|
|»»» type|string|true|none|Error Type|none|
|»»» input|any|false|none|Input|none|
|»»» ctx|object|false|none|Context|none|

<a id="opIdorders_stream_api_v1_orders_stream_get"></a>

## GET 订单状态实时推送（SSE）

GET /api/v1/orders/stream

SSE 长连接：注册订阅 → 循环取事件/心跳 → 断开清理。

> 返回示例

> 200 Response

```json
null
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

### 返回数据结构

# 数据模型

<h2 id="tocS_HTTPValidationError">HTTPValidationError</h2>

<a id="schemahttpvalidationerror"></a>
<a id="schema_HTTPValidationError"></a>
<a id="tocShttpvalidationerror"></a>
<a id="tocshttpvalidationerror"></a>

```json
{
  "detail": [
    {
      "loc": [
        "string"
      ],
      "msg": "string",
      "type": "string",
      "input": null,
      "ctx": {}
    }
  ]
}

```

HTTPValidationError

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|detail|[[ValidationError](#schemavalidationerror)]|false|none|Detail|none|

<h2 id="tocS_LoginIn">LoginIn</h2>

<a id="schemaloginin"></a>
<a id="schema_LoginIn"></a>
<a id="tocSloginin"></a>
<a id="tocsloginin"></a>

```json
{
  "username": "string",
  "password": "string"
}

```

LoginIn

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|username|string|true|none|Username|none|
|password|string|true|none|Password|none|

<h2 id="tocS_OrderCreate">OrderCreate</h2>

<a id="schemaordercreate"></a>
<a id="schema_OrderCreate"></a>
<a id="tocSordercreate"></a>
<a id="tocsordercreate"></a>

```json
{
  "items": [
    {
      "product_id": 0,
      "quantity": 1
    }
  ]
}

```

OrderCreate

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|items|[[OrderItemIn](#schemaorderitemin)]|true|none|Items|none|

<h2 id="tocS_OrderItemIn">OrderItemIn</h2>

<a id="schemaorderitemin"></a>
<a id="schema_OrderItemIn"></a>
<a id="tocSorderitemin"></a>
<a id="tocsorderitemin"></a>

```json
{
  "product_id": 0,
  "quantity": 1
}

```

OrderItemIn

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|product_id|integer|true|none|Product Id|none|
|quantity|integer|true|none|Quantity|none|

<h2 id="tocS_RefreshIn">RefreshIn</h2>

<a id="schemarefreshin"></a>
<a id="schema_RefreshIn"></a>
<a id="tocSrefreshin"></a>
<a id="tocsrefreshin"></a>

```json
{
  "refresh_token": "string"
}

```

RefreshIn

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|refresh_token|string|true|none|Refresh Token|none|

<h2 id="tocS_RegisterIn">RegisterIn</h2>

<a id="schemaregisterin"></a>
<a id="schema_RegisterIn"></a>
<a id="tocSregisterin"></a>
<a id="tocsregisterin"></a>

```json
{
  "username": "string",
  "password": "stringst"
}

```

RegisterIn

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|username|string|true|none|Username|用户名，3-64 字符|
|password|string|true|none|Password|密码，至少 8 位且含字母与数字|

<h2 id="tocS_ValidationError">ValidationError</h2>

<a id="schemavalidationerror"></a>
<a id="schema_ValidationError"></a>
<a id="tocSvalidationerror"></a>
<a id="tocsvalidationerror"></a>

```json
{
  "loc": [
    "string"
  ],
  "msg": "string",
  "type": "string",
  "input": null,
  "ctx": {}
}

```

ValidationError

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|loc|[anyOf]|true|none|Location|none|

anyOf

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|string|false|none||none|

or

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» *anonymous*|integer|false|none||none|

continued

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|msg|string|true|none|Message|none|
|type|string|true|none|Error Type|none|
|input|any|false|none|Input|none|
|ctx|object|false|none|Context|none|


"""FastAPI Layered API 接口自动化测试（由 api-test-pipeline 依据 FastAPI需求文档.md + swagger.json 生成）

覆盖：健康检查 / 鉴权闭环(注册-登录-刷新轮换-登出撤销) / 待办 CRUD / 订单(幂等键+统计) /
文件(multipart 上传 + CSV 导出) / 支付回调(签名校验) / SSE 实时推送 / 未认证访问控制

运行: pytest test_fastapi_layered_api.py -v
配置: 环境变量 API_BASE_URL 覆盖目标地址，默认 http://localhost:8000
"""
import os
import uuid
from datetime import date, timedelta

import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api/v1"
UNAUTH_ALLOWED = (401, 403)


def unique_username() -> str:
    return f"t{uuid.uuid4().hex[:12]}"


def strong_password() -> str:
    return "Passw0rd!23"


def today_str(offset_days: int = 0) -> str:
    return (date.today() + timedelta(days=offset_days)).isoformat()


def unwrap(resp: requests.Response) -> dict:
    """兼容裸 JSON 与 {code, message, data} 包装响应，返回业务数据部分。"""
    try:
        body = resp.json()
    except ValueError:
        return {}
    if isinstance(body, dict) and isinstance(body.get("data"), dict) and (
        "code" in body or "message" in body
    ):
        return body["data"]
    return body if isinstance(body, dict) else {}


def extract_id(resp: requests.Response):
    """从响应中尽力提取资源 id（响应 schema 未在 Swagger 中定义，做兼容提取）。"""
    data = unwrap(resp)
    for key in ("id", "todo_id", "order_id"):
        if key in data:
            return data[key]
    return None


def create_todo(client, headers, **fields):
    payload = {"title": f"auto_{uuid.uuid4().hex[:8]}"}
    payload.update(fields)
    return client.post(f"{API}/todos/create", json=payload, headers=headers, timeout=10)


def create_id_or_skip(resp):
    todo_id = extract_id(resp)
    if todo_id is None:
        pytest.skip("创建响应未返回 id，无法定位资源")
    return todo_id


@pytest.fixture(scope="session")
def client():
    with requests.Session() as s:
        yield s


@pytest.fixture(scope="session")
def user_creds(client):
    """注册一个会话级用户，供鉴权相关用例使用。"""
    creds = {"username": unique_username(), "password": strong_password()}
    resp = client.post(f"{API}/auth/register", json=creds, timeout=10)
    assert resp.status_code == 201, f"前置注册失败: {resp.status_code} {resp.text}"
    return creds


@pytest.fixture(scope="session")
def tokens(client, user_creds):
    """登录获取双令牌。"""
    resp = client.post(f"{API}/auth/login", json=user_creds, timeout=10)
    assert resp.status_code == 200, f"前置登录失败: {resp.status_code} {resp.text}"
    data = unwrap(resp)
    access = data.get("access_token") or data.get("token")
    refresh = data.get("refresh_token")
    assert access and refresh, f"登录响应缺少双令牌: {data}"
    return {"access_token": access, "refresh_token": refresh}


@pytest.fixture(scope="session")
def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestHealth:
    """健康检查（无需认证）"""

    def test_health_check(self, client):
        resp = client.get(f"{API}/health", timeout=10)
        assert resp.status_code == 200

    def test_healthtest(self, client):
        resp = client.get(f"{API}/health/healthtest", timeout=10)
        assert resp.status_code == 200


class TestRegister:
    """注册：正常 / 重复 / 字段边界（3-64 用户名，8+ 位含字母数字密码）"""

    def test_register_success(self, client):
        creds = {"username": unique_username(), "password": strong_password()}
        resp = client.post(f"{API}/auth/register", json=creds, timeout=10)
        assert resp.status_code == 201

    def test_register_duplicate_rejected(self, client, user_creds):
        resp = client.post(f"{API}/auth/register", json=user_creds, timeout=10)
        assert resp.status_code >= 400

    @pytest.mark.parametrize(
        "username",
        ["ab", "a" * 65, ""],
        ids=["用户名过短2字符", "用户名超长65字符", "用户名为空"],
    )
    def test_register_invalid_username_422(self, client, username):
        resp = client.post(
            f"{API}/auth/register",
            json={"username": username, "password": strong_password()},
            timeout=10,
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize(
        "password",
        ["Aa1", "a" * 7, "a" * 8, "12345678", "A" * 8],
        ids=["密码过短", "仅7位", "纯小写字母", "纯数字", "纯大写无数字"],
    )
    def test_register_weak_password_rejected(self, client, password):
        resp = client.post(
            f"{API}/auth/register",
            json={"username": unique_username(), "password": password},
            timeout=10,
        )
        assert resp.status_code in (400, 422)

    def test_register_missing_password_422(self, client):
        resp = client.post(f"{API}/auth/register", json={"username": unique_username()}, timeout=10)
        assert resp.status_code == 422


class TestLogin:
    """登录：双令牌签发 / 错误凭证 / 缺参"""

    def test_login_success_issues_dual_tokens(self, tokens):
        assert tokens["access_token"] and tokens["refresh_token"]

    def test_login_wrong_password(self, client, user_creds):
        resp = client.post(
            f"{API}/auth/login",
            json={"username": user_creds["username"], "password": "WrongPass123"},
            timeout=10,
        )
        assert resp.status_code in (400, 401)

    def test_login_unknown_user(self, client):
        resp = client.post(
            f"{API}/auth/login",
            json={"username": f"no_such_{uuid.uuid4().hex[:6]}", "password": strong_password()},
            timeout=10,
        )
        assert resp.status_code in (400, 401, 404)

    def test_login_missing_password_422(self, client):
        resp = client.post(f"{API}/auth/login", json={"username": "x"}, timeout=10)
        assert resp.status_code == 422


class TestAuthLifecycle:
    """鉴权闭环：me → 刷新轮换 → 旧 refresh 重放失效 → 登出撤销 → 登出后刷新失效。
    每条用例独立登录，互不依赖执行顺序。"""

    state: dict = {}

    def _login(self, client, creds) -> dict:
        resp = client.post(f"{API}/auth/login", json=creds, timeout=10)
        assert resp.status_code == 200
        return unwrap(resp)

    def test_01_me_with_valid_token(self, client, user_creds):
        data = self._login(client, user_creds)
        access = data.get("access_token") or data.get("token")
        assert access
        TestAuthLifecycle.state["access"] = access
        resp = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
            timeout=10,
        )
        assert resp.status_code == 200
        me = unwrap(resp)
        if "username" in me:
            assert me["username"] == user_creds["username"]

    def test_02_refresh_rotates_tokens(self, client, user_creds):
        data = self._login(client, user_creds)
        old_refresh = data.get("refresh_token")
        assert old_refresh
        resp = client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh}, timeout=10)
        assert resp.status_code == 200
        new = unwrap(resp)
        access = new.get("access_token") or new.get("token")
        refresh = new.get("refresh_token")
        assert access and refresh, f"刷新响应缺少双令牌: {new}"
        assert refresh != old_refresh, "refresh token 应轮换，不应返回旧值"
        TestAuthLifecycle.state["old_refresh"] = old_refresh

    def test_03_old_refresh_token_replay_rejected(self, client):
        old = TestAuthLifecycle.state.get("old_refresh")
        if old is None:
            pytest.skip("依赖 test_02 记录的轮换前 refresh token")
        resp = client.post(f"{API}/auth/refresh", json={"refresh_token": old}, timeout=10)
        assert resp.status_code in (400, 401, 403)

    def test_04_logout_revokes_refresh_token(self, client, user_creds):
        data = self._login(client, user_creds)
        access = data.get("access_token") or data.get("token")
        refresh = data.get("refresh_token")
        assert access and refresh
        # 实际实现要求携带 Bearer 访问令牌
        resp = client.post(
            f"{API}/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
            timeout=10,
        )
        assert resp.status_code == 200
        TestAuthLifecycle.state["logged_out_refresh"] = refresh

    def test_05_refresh_after_logout_rejected(self, client):
        refresh = TestAuthLifecycle.state.get("logged_out_refresh")
        if refresh is None:
            pytest.skip("依赖 test_04 记录的已撤销 refresh token")
        resp = client.post(f"{API}/auth/refresh", json={"refresh_token": refresh}, timeout=10)
        assert resp.status_code in (400, 401, 403)


class TestAuthSecurity:
    """未认证 / 非法令牌访问受保护接口"""

    def test_me_without_token(self, client):
        resp = client.get(f"{API}/auth/me", timeout=10)
        assert resp.status_code in UNAUTH_ALLOWED

    def test_me_with_garbage_token(self, client):
        resp = client.get(
            f"{API}/auth/me",
            headers={"Authorization": "Bearer not.a.real.jwt"},
            timeout=10,
        )
        assert resp.status_code in UNAUTH_ALLOWED

    def test_me_with_tampered_token(self, client, tokens):
        tampered = tokens["access_token"][:-2] + "xx"
        resp = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {tampered}"},
            timeout=10,
        )
        assert resp.status_code in UNAUTH_ALLOWED

    def test_todos_list_without_token(self, client):
        resp = client.get(f"{API}/todos/list", timeout=10)
        assert resp.status_code in UNAUTH_ALLOWED


class TestTodos:
    """待办 CRUD：创建/列表(分页+筛选+搜索)/详情/更新/删除 + 参数边界"""

    def test_01_create_full(self, client, auth_headers):
        resp = create_todo(
            client, auth_headers,
            description="自动化测试-完整字段",
            due_at="2026-12-31T23:59:59",
        )
        assert resp.status_code == 201

    def test_02_create_minimal_only_title(self, client, auth_headers):
        resp = create_todo(client, auth_headers)
        assert resp.status_code == 201

    def test_03_create_empty_title_422(self, client, auth_headers):
        resp = client.post(
            f"{API}/todos/create", json={"title": ""}, headers=auth_headers, timeout=10
        )
        assert resp.status_code == 422

    def test_04_create_title_over_128_422(self, client, auth_headers):
        resp = create_todo(client, auth_headers, title="a" * 129)
        assert resp.status_code == 422

    def test_05_create_title_min_length_1_ok(self, client, auth_headers):
        resp = create_todo(client, auth_headers, title="a")
        assert resp.status_code == 201

    def test_10_list_default(self, client, auth_headers):
        resp = client.get(f"{API}/todos/list", headers=auth_headers, timeout=10)
        assert resp.status_code == 200

    def test_11_list_pagination(self, client, auth_headers):
        resp = client.get(
            f"{API}/todos/list",
            params={"page": 1, "page_size": 1},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200

    def test_12_list_status_filter_done(self, client, auth_headers):
        resp = client.get(
            f"{API}/todos/list", params={"status": "done"}, headers=auth_headers, timeout=10
        )
        assert resp.status_code == 200

    def test_13_list_keyword_search(self, client, auth_headers):
        keyword = f"kw{uuid.uuid4().hex[:6]}"
        create_todo(client, auth_headers, title=f"{keyword} 特殊任务")
        resp = client.get(
            f"{API}/todos/list", params={"q": keyword}, headers=auth_headers, timeout=10
        )
        assert resp.status_code == 200
        assert keyword in resp.text, "搜索结果应命中刚创建的关键词"

    def test_20_detail_matches_created(self, client, auth_headers):
        todo_id = create_id_or_skip(create_todo(client, auth_headers))
        resp = client.get(f"{API}/todos/{todo_id}", headers=auth_headers, timeout=10)
        assert resp.status_code == 200
        assert extract_id(resp) == todo_id

    def test_21_detail_not_found(self, client, auth_headers):
        resp = client.get(f"{API}/todos/99999999", headers=auth_headers, timeout=10)
        assert resp.status_code in (400, 404)

    def test_22_detail_invalid_id_422(self, client, auth_headers):
        resp = client.get(f"{API}/todos/not-an-int", headers=auth_headers, timeout=10)
        assert resp.status_code == 422

    def test_30_update_status_to_done(self, client, auth_headers):
        todo_id = create_id_or_skip(create_todo(client, auth_headers))
        resp = client.put(
            f"{API}/todos/{todo_id}",
            json={"status": "done"},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200
        detail = client.get(f"{API}/todos/{todo_id}", headers=auth_headers, timeout=10)
        assert detail.status_code == 200
        body = unwrap(detail)
        if "status" in body:
            assert body["status"] == "done"

    def test_31_update_invalid_status_422(self, client, auth_headers):
        todo_id = create_id_or_skip(create_todo(client, auth_headers))
        resp = client.put(
            f"{API}/todos/{todo_id}",
            json={"status": "archived"},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 422

    def test_32_update_empty_title_422(self, client, auth_headers):
        todo_id = create_id_or_skip(create_todo(client, auth_headers))
        resp = client.put(
            f"{API}/todos/{todo_id}", json={"title": ""}, headers=auth_headers, timeout=10
        )
        assert resp.status_code == 422

    def test_40_delete_then_not_found(self, client, auth_headers):
        todo_id = create_id_or_skip(create_todo(client, auth_headers))
        resp = client.delete(f"{API}/todos/{todo_id}", headers=auth_headers, timeout=10)
        assert resp.status_code in (200, 202, 204)
        detail = client.get(f"{API}/todos/{todo_id}", headers=auth_headers, timeout=10)
        assert detail.status_code in (400, 404)


class TestOrders:
    """订单：幂等键 / 数量边界(1-999) / 统计报表必填校验"""

    first_order_id = None
    idem_key = None

    def test_01_create_with_idempotency_key(self, client, auth_headers):
        TestOrders.idem_key = uuid.uuid4().hex
        resp = client.post(
            f"{API}/orders",
            json={"items": [{"product_id": 1, "quantity": 2}]},
            headers={**auth_headers, "Idempotency-Key": TestOrders.idem_key},
            timeout=10,
        )
        assert resp.status_code == 201
        TestOrders.first_order_id = extract_id(resp)

    def test_02_same_key_returns_same_order(self, client, auth_headers):
        if TestOrders.idem_key is None:
            pytest.skip("依赖 test_01 的 Idempotency-Key")
        resp = client.post(
            f"{API}/orders",
            json={"items": [{"product_id": 1, "quantity": 2}]},
            headers={**auth_headers, "Idempotency-Key": TestOrders.idem_key},
            timeout=10,
        )
        assert resp.status_code in (200, 201)
        if TestOrders.first_order_id is not None:
            assert extract_id(resp) == TestOrders.first_order_id, \
                "相同 Idempotency-Key 应返回同一订单"

    def test_03_empty_items_422(self, client, auth_headers):
        resp = client.post(
            f"{API}/orders", json={"items": []}, headers=auth_headers, timeout=10
        )
        assert resp.status_code == 422

    def test_04_missing_items_422(self, client, auth_headers):
        resp = client.post(f"{API}/orders", json={}, headers=auth_headers, timeout=10)
        assert resp.status_code == 422

    @pytest.mark.parametrize(
        "quantity", [0, 1000, -1], ids=["低于下界0", "高于上界1000", "负数"]
    )
    def test_05_quantity_out_of_range_422(self, client, auth_headers, quantity):
        resp = client.post(
            f"{API}/orders",
            json={"items": [{"product_id": 1, "quantity": quantity}]},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 422

    def test_06_quantity_upper_bound_999(self, client, auth_headers):
        """quantity=999 通过 schema 校验；若商品库存不足则业务返回 409。"""
        resp = client.post(
            f"{API}/orders",
            json={"items": [{"product_id": 1, "quantity": 999}]},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code in (201, 409)

    def test_07_create_without_auth(self, client):
        resp = client.post(
            f"{API}/orders",
            json={"items": [{"product_id": 1, "quantity": 1}]},
            timeout=10,
        )
        assert resp.status_code in UNAUTH_ALLOWED

    def test_10_statistics_range_ok(self, client, auth_headers):
        resp = client.get(
            f"{API}/orders/statistics",
            params={"from": today_str(-7), "to": today_str(1)},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200

    def test_11_statistics_missing_from_422(self, client, auth_headers):
        resp = client.get(
            f"{API}/orders/statistics",
            params={"to": today_str(1)},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 422

    def test_12_statistics_missing_to_422(self, client, auth_headers):
        resp = client.get(
            f"{API}/orders/statistics",
            params={"from": today_str(-7)},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 422


class TestFiles:
    """文件：multipart 上传 / CSV 流式导出"""

    def test_01_upload_multipart(self, client, auth_headers):
        files = {"file": ("api_test.txt", b"hello from api test", "text/plain")}
        resp = client.post(
            f"{API}/files/upload", files=files, headers=auth_headers, timeout=10
        )
        assert resp.status_code == 201

    def test_02_upload_missing_file_422(self, client, auth_headers):
        resp = client.post(f"{API}/files/upload", headers=auth_headers, timeout=10)
        assert resp.status_code == 422

    def test_03_upload_without_auth(self, client):
        files = {"file": ("x.txt", b"x", "text/plain")}
        resp = client.post(f"{API}/files/upload", files=files, timeout=10)
        assert resp.status_code in UNAUTH_ALLOWED

    def test_10_export_orders_csv(self, client, auth_headers):
        resp = client.get(
            f"{API}/files/export/orders.csv",
            params={"from": today_str(-7), "to": today_str(1)},
            headers=auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200
        assert "csv" in resp.headers.get("content-type", "").lower()

    def test_11_export_missing_params_422(self, client, auth_headers):
        resp = client.get(
            f"{API}/files/export/orders.csv", headers=auth_headers, timeout=10
        )
        assert resp.status_code == 422


class TestPaymentsWebhook:
    """支付回调：无 Bearer 认证，依赖签名校验 + 幂等"""

    def test_01_missing_signature_rejected(self, client):
        resp = client.post(
            f"{API}/payments/webhook",
            json={"event": "payment.succeeded"},
            timeout=10,
        )
        assert resp.status_code in (400, 401, 403, 422)

    def test_02_invalid_signature_rejected(self, client):
        resp = client.post(
            f"{API}/payments/webhook",
            json={"event": "payment.succeeded"},
            headers={"X-Signature": "invalid_signature_value"},
            timeout=10,
        )
        assert resp.status_code in (400, 401, 403, 422)


class TestOrderStream:
    """SSE 实时推送：验证连接建立与 content-type，立即关闭避免阻塞"""

    def test_01_stream_established(self, client, auth_headers):
        with client.get(
            f"{API}/orders/stream", headers=auth_headers, stream=True, timeout=(5, 5)
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "").lower()
            resp.close()

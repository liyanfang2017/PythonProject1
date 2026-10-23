import pytest
import yaml
from pathlib import Path

# 读取外部yaml数据文件
def load_yaml_test_data(file_path):
    with open(file_path, "r", encoding="utf‑8") as f:
        return yaml.safe_load(f)

# 获取yaml路径
yaml_file = Path(__file__).parent / "test_data" / "login_data.yaml"
login_test_data = load_yaml_test_data(yaml_file)

# 将yaml数据解包用于 parametrize
test_cases = [
    (item["username"], item["password"], item["expect_success"], item["expect_msg"])
    for item in login_test_data
]

@pytest.mark.parametrize("username,password,expect_success,expect_msg", test_cases)
def test_login_with_yaml(page, username, password, expect_success, expect_msg):
    """
    page fixture来自 pytest‑playwright插件，自动管理浏览器
    测试逻辑只写1遍，多组yaml数据自动循环执行
    """
    # 打开登录页面
    page.goto("https://demo.playwright.dev/login")

    # 执行操作
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in").click()

    # 业务断言逻辑
    if expect_success:
        page.wait_for_selector(f"text={expect_msg}")
        assert expect_msg in page.content()
    else:
        page.wait_for_selector(f"text={expect_msg}")
        assert expect_msg in page.content()

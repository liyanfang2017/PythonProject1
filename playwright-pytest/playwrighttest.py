# test_demo.py
from playwright.sync_api import Page

def test_baidu_search(page: Page):
    # 打开网页
    page.goto("https://www.baidu.com")
    # 输入
    page.locator("#kw").fill("playwright自动化")
    # 点击
    page.locator("#su").click()
    # 断言
    assert "playwright" in page.title()

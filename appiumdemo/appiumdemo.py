from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

if __name__ == '__main__':
    # 配置参数，这里改成你自己APP的包名和activity
    options = UiAutomator2Options()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "Android")  # 随便写，adb识别为准
    options.set_capability("appPackage", "com.sdu.didi.psnger")
    options.set_capability("appActivity", "com.didi.sdk.app.MainActivity")
    options.set_capability("noReset", True)       # 不重置app，保留登录状态，调试推荐True
    options.set_capability("newCommandTimeout", 300)
    options.set_capability("automationName", "UiAutomator2")

    try:
        # 连接appium server
        driver = webdriver.Remote(command_executor="http://127.0.0.1:4723", options=options)
        print("✅ APP启动成功！")
        time.sleep(5)   # 停留5秒看效果
    except Exception as e:
        print("❌ 启动失败：", e)
    finally:
        # 关闭，不想关闭APP可以注释这一行
        driver.quit()
        print("🔚 脚本执行结束")

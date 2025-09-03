from DrissionPage import ChromiumPage
import time


def boss_login_with_captcha():
    """
    BOSS直聘验证码登录模块
    """
    # 实例化浏览器对象
    dp = ChromiumPage()

    try:
        print("开始BOSS直聘登录流程...")

        # 访问登录页面
        dp.get('https://www.zhipin.com/web/user/?ka=header-login')

        # 等待页面加载完成
        time.sleep(3)

        # 选择短信登录方式（如果默认不是的话）
        try:
            sms_login_tab = dp.ele('xpath://*[@class="tab-wrap"]/a[contains(text(), "我要找工作")]')
            if sms_login_tab:
                sms_login_tab.click()
                time.sleep(1)
        except:
            pass

        # 输入手机号
        phone_input = dp.ele('css:#phone')
        phone_number = input("请输入您的手机号: ")
        phone_input.input(phone_number)

        # 点击获取验证码按钮
        get_code_button = dp.ele('css:.btn-send-code')
        if get_code_button:
            get_code_button.click()
            print("已发送验证码到您的手机，请查收...")
        else:
            print("未找到获取验证码按钮，请检查页面元素")
            return None

        # 等待用户输入验证码
        captcha_code = input("请输入您收到的验证码: ")

        # 输入验证码
        code_input = dp.ele('css:#code')
        code_input.input(captcha_code)

        # 点击登录按钮
        login_button = dp.ele('css:.btn-login')
        login_button.click()

        # 等待登录完成
        time.sleep(5)

        # 验证是否登录成功
        # 检查是否存在用户相关的元素来判断登录状态
        user_element = None
        try:
            # 尝试查找用户头像或用户名元素
            user_element = dp.ele('css:.user-avatar', timeout=3)
        except:
            try:
                user_element = dp.ele('css:.user-name', timeout=3)
            except:
                pass

        if user_element:
            print("登录成功！")
            return dp
        else:
            print("登录可能失败，请检查验证码是否正确")
            return None

    except Exception as e:
        print(f"登录过程中出现错误: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    page = boss_login_with_captcha()
    if page:
        print("您可以继续进行数据采集操作...")
        # 在这里可以继续执行其他操作
        # page.get('https://www.zhipin.com/...')
    else:
        print("登录失败")

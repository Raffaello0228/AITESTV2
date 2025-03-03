from selenium import webdriver
import json
import os


def update_token():
    # 初始化浏览器驱动
    driver = webdriver.Chrome()
    # 打开网页
    driver.get("http://sino-adshub-front.background:8080/chat")
    # 获取浏览器Cookies
    feedback = input("请在登录后输入回车：")
    token = driver.execute_script("return window.localStorage.getItem('X-SINO-JWT');")
    driver.quit()

    # 将token保存到配置文件
    config = {"token": token}

    config_dir = os.path.join(os.path.dirname(__file__), "../config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    with open(os.path.join(config_dir, "token.json"), "w") as f:
        json.dump(config, f, indent=2)

    return token


if __name__ == "__main__":
    update_token()

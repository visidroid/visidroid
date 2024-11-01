from appium import webdriver
from appium.options.android import UiAutomator2Options
import os
class Device():
    def __init__(self, platform="Android", platformVersion=None, deviceName=None, appPackage=None, appActivity=None, appium_server_url="http://localhost:4723/wd/hub"):
        # Desired capabilities
        self.platform = platform
        self.platformVersion = platformVersion
        self.deviceName = deviceName
        self.appPackage = appPackage
        self.appActivity = appActivity
        self.appium_server_url = appium_server_url
        self.appPath = None
        for item in os.listdir(os.path.join('..','..','target_apps')):
            if item.startswith(self.appPackage):
                self.appPath = os.path.join(os.path.dirname(__file__),'..','..','target_apps', item)
                break
        if self.appPath is not None and os.path.exists(self.appPath):
            self.desired_caps = {
                'platformName': self.platform,
                'platformVersion': self.platformVersion,
                'deviceName': self.deviceName,
                'appPackage': self.appPackage,
                'appActivity': self.appActivity,
                'app': self.appPath,
                'automationName': 'UiAutomator2',
                'appium:deviceConnectionString': self.appium_server_url,
                'noReset': False,
                'fullReset': False,
                'autoGrantPermissions': True
            }
        else:
            self.desired_caps = {
                'platformName': self.platform,
                'platformVersion': self.platformVersion,
                'deviceName': self.deviceName,
                'appPackage': self.appPackage,
                'appActivity': self.appActivity,
                'automationName': 'UiAutomator2',
                'appium:deviceConnectionString': self.appium_server_url,
                'noReset': False,
                'fullReset': False,
                'autoGrantPermissions': True
            }
        # Initialize Appium driver

    def connect(self):
        capabilities_options = UiAutomator2Options().load_capabilities(self.desired_caps)
        try:
            self.driver = webdriver.Remote(
                command_executor=self.appium_server_url, options=capabilities_options)
        except Exception as e:
            print("Device connect failed")
            print(e)

            exit()

    def disconnect(self):
        self.driver.quit()

    def wait_until_finish(self):
        self.driver.implicitly_wait(3)

    
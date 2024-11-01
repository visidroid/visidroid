from dotenv import load_dotenv
import os


class AppConfig:
    def __init__(self):
        # Default configuration values
        self.platform = 'Android'
        self.platformVersion = "14"
        self.deviceName = "sdk_gphone64_x86_64"
        self.appPackage = "com.simplemobiletools.filemanager.pro"
        self.appActivity = "com.simplemobiletools.filemanager.pro.activities.MainActivity"

    def load_from_env(self):
        # Load environment variables from .env file
        try:
            load_dotenv()

            # Read from environment variables and update configuration
            self.platform = os.getenv('APP_HOST', self.platform)
            self.platformVersion = os.getenv(
                'APP_PLATFORM_VERSION', self.platformVersion)
            self.deviceName = os.getenv('APP_DEVICE_NAME', self.deviceName)
            self.appPackage = os.getenv('APP_APP_PACKAGE', self.appPackage)
            self.appActivity = os.getenv('APP_APP_ACTIVITY', self.appActivity)

            return True  # Configuration loaded successfully
        except Exception as e:
            return str(e)  # Return the error message

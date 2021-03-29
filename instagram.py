import pathlib  
	
from selenium import webdriver  
	
import config
from bot import AutoLikeBot
from strategy import RunForeverWithBreaks 

def configure_chrome_driver():  
	options = webdriver.ChromeOptions()  
	options.add_argument(f"user-data-dir={pathlib.Path(__file__).parent.absolute().joinpath('chrome-profile')}")  
	
	# disable image loading for better performance  
	# options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})  
	
	the_driver = webdriver.Chrome(executable_path=config.DRIVER_EXECUTABLE_PATH, options=options)  
	
	# page loading time and wait time for page reload  
	the_driver.set_page_load_timeout(5)  
	the_driver.implicitly_wait(2)  

	#the_driver = webdriver.Chrome('/mnt/c/Python/chromedriver.exe') # hardcode path

	return the_driver

if __name__ == '__main__':
		from datetime import datetime

		start=datetime.now()

		with AutoLikeBot(configure_chrome_driver(),
			) as bot:
			bot.engage_with_active_users_from_target(target_account=config.TARGET_ACCOUNT,
													temp_like_limit=20)

		print(f"stop time: {datetime.now()}")
		print(f"Runtime: {datetime.now()-start}")										

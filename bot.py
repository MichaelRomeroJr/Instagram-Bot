from selenium.webdriver.remote.webdriver import WebDriver

import logging
import random

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

import config
from strategy import RunForeverStrategy
from tracker import post_tracker
import utils

from selenium.webdriver.common.keys import Keys
import sys

from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(handlers=[logging.StreamHandler()],
					level=logging.INFO,
					format='%(asctime)s [%(levelname).4s] %(message)s',
					datefmt='%a %d %H:%M:%S')

logger = logging.getLogger()

class AutoLikeBot:
	def __init__(self, driver: WebDriver):
		self.driver = driver
		self.like_count = 0
		self.stop_count=0

	def __enter__(self):
		if not config.SKIP_LOGIN:
			self.log_in()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.driver.quit()
		logger.info(post_tracker.stats)
		return None


	def iterate_through_active_users(self, active_account_list):
		"""
			iterate through list of active users			 
			filters: 
				active user has more than follower_lower_bound limit, 
				post has more than post_lower_bound limit (set in like_post function),
			call like_post() function
			track number of posts liked
		"""

		follower_lower_bound = 50 # Change back to 200
		for account_url in active_account_list:
			username = account_url[len("https://www.instagram.com/"):].rstrip('/')

			self.driver.get(account_url)  
			utils.rand_wait_sec(30,45)

			try:
				# Wait until username is loaded on page
				name_loaded = False
				x_path_string = f"//*[contains(text(), {username})]"			
				while not name_loaded:	
					utils.wait_until(self.driver, ec.presence_of_element_located((By.XPATH , x_path_string))) 

					webpage_text = self.driver.find_element_by_xpath(x_path_string).text

					if len(webpage_text)>0:
						name_loaded = True
			except:
				print(f"Error on {username}: ")
				print(f"Couldn't find username. \n" + f"Most likely user has no text in profile. \n" +
						f"Press Enter to try to continue: ")
			
			# Check if account is private
			is_private = self.driver.find_elements_by_xpath("//*[contains(text(), 'This Account is Private')]")
			no_pics_posted = self.driver.find_elements_by_xpath("//*[contains(text(), 'No Posts Yet')]")

			if (len(is_private)==0) and (len(no_pics_posted)==0):
				print(f"{username} is public")
				post_and_descriptions={} # dictionary: key=post urls and value= instagram's image description

				web_elems = self.driver.find_elements_by_class_name('FFVAD')
				descriptions=[]
				for web_elem in web_elems:
					try: 
						text_alt = web_elem.get_attribute("alt")
						descriptions.append(text_alt)
					except:
						print("couldn't get text")
				descriptions=descriptions[:3]

				main_elements = self.driver.find_element_by_tag_name('main') # Get Links
				hyperlink_elems = main_elements.find_elements_by_tag_name('a')

				media1=None
				if media1 is None: #All kmedia types
					media1 = ['', 'Post', 'Video']
				elif media1 == 'Photo': #Posts w/ multiple pics
					media1 = ['', 'Post']
				else: #Make it a list
					media1 = [media]
				
				try:
					if hyperlink_elems:						
						active_user_posts_all = [link_elem.get_attribute('href') for link_elem in hyperlink_elems if link_elem and link_elem.text in media1] 
						active_user_recent_posts=[]
						active_user_recent_posts = active_user_posts_all[:3]

						# Create dictionary of post urls with instagram description tags 
						post_and_descriptions[active_user_recent_posts[0]] = descriptions[0]
						post_and_descriptions[active_user_recent_posts[1]] = descriptions[1]
						post_and_descriptions[active_user_recent_posts[2]] = descriptions[2]

						follower_count = self.number_of_followers(self.driver)											
						# Like 3 most recent posts
						if follower_count > follower_lower_bound: 
							# Only start opening photos if account has more than 200 followers

							for key in post_and_descriptions:								
								post_url = key
								post_description = post_and_descriptions[key]
								print(f"Post link: {post_url}")
								print(f"Post Description: {post_description}")

								post_passed_filter = utils.post_description_filter(post_description)
								successful_like = self.like_post(post_url)

								if successful_like:
									self.like_count += 1
									post_tracker.liked_count+=1
									print(f"Liked {self.like_count} photos")

								if self.like_count >= self.stop_count:
									return

				except :					
					#error = sys.exc_info()[0] # <class 'IndexError'>
					#print(f"{error}")
					print(f"didn't have at least 3 posts")

			else:				
				print(f"{username} is private")

			print()


	def engage_with_active_users_from_target(self, target_account, temp_like_limit):
		"""
			go to target_account's page 
			open recent post
			Click "likes" to view who has liked recent post
			Scroll down likes window and collect active users
			Visit each active_user and like last 3 posts based on filters 
		"""
		self.stop_count = temp_like_limit

		# Land on target_account page
		self.driver.get('https://instagram.com/' + target_account)
		utils.rand_wait_sec()

		# Open target_account most recent post # input('Open recent post: ')
		self.target_open_recent_post()
		
		# View most recent likes of recent post 
		likes_window_visible = False
		while not likes_window_visible:
			#m82CD class name of "Likes" header of the "Likes" pop up window
			try:
				# Click number of likes likes"
				#self.driver.find_element_by_partial_link_text('likes').click() 
				self.driver.find_element_by_class_name("zV_Nj").click()
				#rand_wait_sec()
				utils.rand_wait_sec()

				# Wait and see if "Likes" header is visible 
				utils.wait_until(self.driver, ec.presence_of_element_located((By.CLASS_NAME, 'm82CD'))) 
				likes_window_visible = True

			except (NoSuchElementException, TimeoutException):
				print(f"Re-opening \"Likes\" pop up window because Instagram auto closed it. ")
				
		# Note, instagram doesn't display all accounts at the same time
		# so you have to scroll down, scrape the page, scroll down again scrape the page 
		active_users_list_of_sets=[]
		scroll_count = 4
		print(f"Manually scroll down \"Likes\" pop up window {scroll_count} times")		
		for i in range(scroll_count): # Increase range to increase number of Active Users			
			input(f"manual scroll down {i+1} (press Enter to continue): ") 

			# Method 1: (doesn't grab scroll bar)
			#input(f"method 1: auto scroll down {i+1}: ")			
			#self.driver.find_element_by_css_selector('body').send_keys(Keys.PAGE_DOWN)
			#actions.drag_and_drop_by_offset(element, 50, 50)
			#actions.perform()			

			# Method 2:
			#input(f"method 2: auto scroll down {i+1}: ")
			# likes_window_elems = self.driver.find_elements_by_class_name('_1XyCr')
			# likes_window_elems[0].send_keys(Keys.PAGE_DOWN)
			
			# Scrape all hyperlinks
			href_elems = self.driver.find_elements_by_xpath("//a[@href]")
			hrefs=[]
			for elem in href_elems:
				if elem.get_attribute("href").startswith("https://www.instagram.com/"):
					hrefs.append(elem.get_attribute("href")) 		
			# Return only instagram account usernames from list of all hyperlinks    
			active_users_list_of_sets.append(utils.get_active_users_in_href_elem(hrefs,target_account))

		active_users = utils.active_users_to_set(active_users_list_of_sets,target_account)

		print(f"Number of Active Users: {len(active_users)}")
		print(f"Active Users: ")
		for account in active_users:
			print(account)

		#input(f"Press Enter to close: ")			
		# Go to active user pages and like recent posts
		self.iterate_through_active_users(active_users)


	def target_open_recent_post(self, ):
		"""
			Open recent post of the target_account
			added Added WebDriverWait
		"""

		try:
			utils.wait_until(self.driver, ec.presence_of_element_located((By.TAG_NAME, 'main')))

			# main elements are their so open recent post
			main_elements = self.driver.find_element_by_tag_name('main') # Get Links
			hyperlink_elems = main_elements.find_elements_by_tag_name('a')
			media=None
			if media is None: #All kmedia types
				media = ['', 'Post', 'Video']
			elif media == 'Photo': #Posts w/ multiple pics
				media = ['', 'Post']
			else: #Make it a list
				media = [media]

			try:
				if hyperlink_elems:
					recent_links = [link_elem.get_attribute('href') for link_elem in hyperlink_elems if link_elem and link_elem.text in media] 
			except BaseException as e:
				print("hyperlink_elems error \n", str(e))  
			
			# Got the most recent link so wait to open
			utils.rand_wait_sec()

			# Open link of most recent post
			self.driver.get(recent_links[0])
			return True

		# Couldn't find most recent post but you can still click it to continue 
		except (NoSuchElementException, TimeoutException):
			input("Failed to open most recent post. \n" + 
					"Click the most recent post and press Enter to continue: ")			
			return False


	def like_post(self, post_url):
		"""
			Open post in new tab
			Count tabs to confirm Instagram hasn't auto closed it
			Count likes and click "like" if it has more than post_lower_bound
			Added WebDriverWait
		"""

		post_lower_bound = 20
		utils.open_and_switch_to_tab(self.driver, post_url) 
		utils.rand_wait_sec()

		# Make sure Instagram doesn't auto close the new window of the photo we're about to like
		number_of_tabs = len(self.driver.window_handles)
		while (number_of_tabs == 1):
			print(f"auto closed new window. Will re-open.")			
			#open_and_switch_to_tab(self.driver, post_url)
			util.open_and_switch_to_tab(self.driver, post_url) 
			utils.rand_wait_sec()
			number_of_tabs = len(self.driver.window_handles)
		
		try:
			post_like_count = self.number_of_likes(self.driver) # number of likes of post 
			
			if post_like_count > post_lower_bound: 
				# Wait for heart element to load
				utils.wait_until(self.driver, ec.presence_of_element_located((By.CLASS_NAME, 'fr66n'))) 	

				# Click like
				self.driver.find_element_by_class_name('fr66n').click()
				utils.rand_wait_sec(75,90)

				return True
	
		except (NoSuchElementException, TimeoutException):
			return False
		finally:			
			utils.close_and_open_tab(self.driver) 
	

	def number_of_likes(self, driver): 
		"""
			Count number of likes from current window open
			common class names for number of likes text: Nm9Fw, zV_Nj 
		"""
		
		try: 
			utils.wait_until(self.driver, ec.presence_of_element_located((By.CLASS_NAME, 'Nm9Fw'))) 
			web_text = self.driver.find_element_by_class_name('Nm9Fw').text
			return True

		except (NoSuchElementException, TimeoutException):
			return False
		finally:
			likes_string = web_text.replace(" likes","")
			likes_count = int(likes_string)
			
			return	likes_count	


	def number_of_followers(self, driver): 
		"""
			Count number of likes from current window open
			common class names for number of followers text: -nal3, g47SY  
		"""		

		try: 
			utils.wait_until(self.driver, ec.presence_of_element_located((By.CLASS_NAME, 'g47SY'))) 

			web_elems = self.driver.find_elements_by_class_name('g47SY')

			title = web_elems[1].get_attribute("title").replace(",","")
			follower_count = int(title)

		except (NoSuchElementException, TimeoutException):
			print(f"Couldn't get follower count")

		return follower_count


	def log_in(self):
		"""
			Log in using WebDriverWait
		"""

		self.driver.get("https://www.instagram.com/")

		try:
			utils.wait_until(self.driver, ec.presence_of_element_located((By.NAME, 'username'))) 

			self.driver.find_element_by_name('username').send_keys(config.USERNAME) 
			self.driver.find_element_by_name('password').send_keys(config.PASSWORD)

			utils.rand_wait_sec()

			self.driver.find_element_by_name('password').send_keys(Keys.RETURN)
			utils.rand_wait_sec()
			return True

		except (NoSuchElementException, TimeoutException):
			return False


	def verify_liked_image(self):
		"""
			Not complete
		"""

		self.driver.refresh()
		#unlike_xpath = read_xpath(like_image.__name__, "unlike")
		#aria-label = unlike
		# TODO: Use find element by xpath and find aria-label 'unlike'
		like_elem = self.driver.find_elements_by_partial_link_text('unlike')

		if len(like_elem) == 1:
			return True
		else:
			logger.warning("--> Image was NOT liked! You have a BLOCK on likes!")
			return False
		
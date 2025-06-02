from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Set up options to make Selenium less detectable
options = Options()
options.add_argument("--headless")  # Optional: run without opening browser window
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")

# Load Chrome with options
driver = webdriver.Chrome(options=options)

# Go to Daraz
driver.get("https://www.daraz.com.bd/")
time.sleep(5)  # Wait for page to load (adjust as needed)

# Get page source and parse
soup = BeautifulSoup(driver.page_source, "html.parser")
print("Title:", soup.title.text)

driver.quit()

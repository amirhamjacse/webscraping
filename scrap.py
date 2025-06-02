import requests
from bs4 import BeautifulSoup

# Step 1: Send a GET request to the website
url = "https://quotes.toscrape.com/page/2/"
response = requests.get(url)

# Step 2: Parse the content
soup = BeautifulSoup(response.content, 'lxml')

# Step 3: Extract data
quotes = soup.find_all('div', class_='quote')

for quote in quotes:
    text = quote.find('span', class_='text').get_text()
    author = quote.find('small', class_='author').get_text()
    print(f"{text} — {author}")

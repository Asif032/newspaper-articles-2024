import requests
from bs4 import BeautifulSoup

response = requests.get('https://www.banglatribune.com/873729')

soup = BeautifulSoup(response.content, 'lxml')
with open("sample_page.html", "w", encoding="utf-8") as file:
  file.write(soup.prettify())
  
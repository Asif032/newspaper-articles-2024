from bs4 import BeautifulSoup
import requests
import json
import sys
import time
import unicodedata
# from db import create_connection, init, insert_article, insert_status
from datetime_converter import convert_to_english
from concurrent.futures import ThreadPoolExecutor
 

# connection = create_connection("localhost", "user", "password", "ittefaq_news_article")
# init(connection)

base_url = 'https://mzamin.com/news.php?news='

processed_urls = set()
with open('mzamin_news_articles.jsonl', 'r', encoding='utf-8') as file:
  for line in file:
    data = json.loads(line)
    if 'url' in data:
      processed_urls.add(data['url'])

def save_progress(next_url_number):
  with open('starting_url.json', 'w') as file:
    file.write(str(next_url_number))

def countdown(seconds, next_url_number):
  print("Press 'Ctrl+C' to exit the program.")
  try:
    for i in range(seconds, 0, -1):
      sys.stdout.write(f"\r{i} seconds remaining...")
      sys.stdout.flush()
      time.sleep(1)
  except KeyboardInterrupt:
    save_progress(next_url_number)
    print("\nExiting program...")
    sys.exit(0)
    
  print("\nExit window closed, resuming.")

def scrape_article(request_id):
  url = base_url + str(i)
  response = None
  # print(f"Processing {url} ...", end='')
  if url in processed_urls:
    # print("already done, skipping.")
    return
  
  try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
  except requests.exceptions.ConnectionError as e:
    print("Connection error occurred:", e)
    print(f"Last url: {request_id}")
    return -1
  except requests.exceptions.HTTPError as e:
    print("HTTP error occurred:", e)
    print("HTTP Status Code:", response.status_code)
    return 0
  except requests.exceptions.Timeout as e:
    print("Timeout error occurred:", e)
    return -1
  except requests.exceptions.RequestException as e:
    print("Request exception occurred:", e)
    return -1
  finally:
    status_code = -1
    if response:
      status_code = response.status_code
    status_report = {
      "id": request_id,
      "status_code": status_code
    }
    # insert_status(connection, status_report)
    if response and response.status_code != 200:
      return 0
 
  # print("outside finally")
  soup = BeautifulSoup(response.content, 'lxml')
  # with open("article.html", "w", encoding="utf-8") as file:
  #   file.write(soup.prettify())


  date_published = None
  date_published_container = soup.find('div', class_='col-sm-8')
  h5_tag = None
  if date_published_container:
    h5_tag = date_published_container.find('h5')
  if h5_tag:
  # Get the next sibling or the following <p> tag
    next_sibling = h5_tag.next_sibling
    while next_sibling:
      if next_sibling.name == 'p':  # Handle <p> tag case
        date_published = next_sibling.text.strip()
        break
      elif next_sibling.string and next_sibling.string.strip():  # Handle plain text case
        date_published = next_sibling.string.strip()
        break
      next_sibling = next_sibling.next_sibling

  # print(date_published)
  
  #date_modified
  date_modified = date_published
  # date_modified = convert_to_english(date_modified[8:])
  # if date_published and len(date_published) >= 9:
  #   date_modified = date_modified[8:]
  
  #author
  author = soup.find('h5', class_=None).text.strip() if soup.find('h5', class_=None) else None
  
  #category
  category = soup.find('h4', class_='sectitle').text.strip() if soup.find('h4', class_='sectitle') else None

  #tag
  tag = []
    
  #title
  title = soup.find('h1', class_='lh-base fs-1').text.strip() \
    if soup.find('h1', class_ = 'lh-base fs-1') else None
  
  #url
  
      
  #content
  content = soup.find('div', class_='col-sm-10 offset-sm-1 fs-5 lh-base mt-4 mb-5').get_text().strip() \
    if soup.find('div', class_='col-sm-10 offset-sm-1 fs-5 lh-base mt-4 mb-5') else None
  if content:
    content = content.replace('\n', ' ')
    content = unicodedata.normalize("NFKC", content)
  
  article = {
    "date_published": date_published,
    "date_modified": date_modified,
    "author": author,
    "category": category,
    "tag": tag,
    "title": title,
    "url": url,
    "content": content
  }
  # print(article)
  with open('mzamin_news_articles.jsonl', 'a', encoding='utf-8') as file:
    if not url in processed_urls:
      file.write(json.dumps(article, ensure_ascii=False) + '\n')
      processed_urls.add(article["url"])
  # insert_article(connection, article)
  # print("done")
  return 1
  

with open("starting_url.json", "r") as file:
  starting_url = json.load(file)

# 672352 initial staring url
# 704500 ending url
ending_url = 134020
workers = 20
batch = []
for i in range(starting_url, ending_url + 1, workers):
  try:
    with ThreadPoolExecutor(max_workers=workers) as article_pool:
      futures = [article_pool.submit(scrape_article, j) for j in range(i, min(ending_url, i + workers))]
      print(f"{i/ending_url}")
  except KeyboardInterrupt:
    countdown(10, i)
  save_progress(i + 1)
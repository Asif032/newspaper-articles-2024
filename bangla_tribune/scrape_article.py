from bs4 import BeautifulSoup
import requests
import json
import sys
import time
import unicodedata
# from db import create_connection, init, insert_article, insert_status
from datetime_converter import convert_to_english
from concurrent.futures import ThreadPoolExecutor
import math
 

# connection = create_connection("localhost", "user", "password", "ittefaq_news_article")
# init(connection)

base_url = 'https://www.banglatribune.com/'

processed_urls = set()
with open('bangla_tribune_news_articles.jsonl', 'r', encoding='utf-8') as file:
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

def get_elapsed_time(total_time):
  # seconds = total_time % 60
  # total_time //= 60
  # minutes = total_time % 60
  # hours = total_time // 60

  # time_string = ""
  # if hours:
  #   time_string += f"{hours} hour(s) "
  # if minutes:
  #   time_string += f"{minutes} minute(s) "

  # time_string += f"{seconds} second(s)"
  
  return f"{total_time}s"

def get_eta(t0, t1, completed, total):
  incompleted = total - completed
  time_per_task = (t1 - t0) / completed
  eta = int(time_per_task * incompleted)
  return get_elapsed_time(eta)

def print_progress_bar(t0, t1, completed, total):
  progress = math.ceil(completed / total * 50)
  completed_percentage = completed / total * 100
  progress_bar = f"[{'=' * progress}{'.' * (50 - progress)}] {completed_percentage:.2f}%"
  eta_string = f"ETA: {get_eta(t0, t1, completed, total)} | Elapsed: {get_elapsed_time(int(t1 - t0))}"
  sys.stdout.write("\033[F\033[K")
  sys.stdout.write("\033[F\033[K")
  print(progress_bar)
  print(eta_string)

articles = []

def scrape_article(request_id):
  url = base_url + str(i)
  response = None
  if url in processed_urls:
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
  time.sleep(1)
  soup = BeautifulSoup(response.content, 'lxml')
  # print(soup.prettify())
  # with open("sample_page.html", "w", encoding="utf-8") as file:
  #   file.write(soup.prettify())
  #   return


  date_published = None
  date_modified = None
    
  json_ld_scripts = soup.find_all("script", type="application/ld+json")
  for script in json_ld_scripts:
    try:
      data = json.loads(script.string)
      if 'datePublished' in data:
        date_published = datetime.strptime(data['datePublished'][:19], "%Y-%m-%dT%H:%M:%S")
      if 'dateModified' in data:
        date_modified = datetime.strptime(data['dateModified'][:19], "%Y-%m-%dT%H:%M:%S")
    except json.JSONDecodeError:
      continue
  
  #author
  author = soup.find('div', class_='author no_propic').text.strip() \
    if soup.find('div', class_='author no_propic') else None
  
  #category
  category = None
  category_container = soup.find('div', class_='container pb16 mt10 breadcrumb_wrap')
  if category_container:
    li = soup.find_all('a')
    if li and len(li) >= 2:
      category = li[1].get_text().strip()
  #tag
  tag = []
  tag_container = soup.find('div', class_='topic_list') \
    if soup.find('div', class_='topic_list') else None
  if tag_container:
    tag_list = tag_container.find_all('a')
    if tag_list:
      for tag_ in tag_list:
        tag.append(tag_.get_text().strip())
    
  #title
  title = soup.find('h1', class_='title mb10').text.strip() \
    if soup.find('h1', class_ = 'title mb10') else None
  
  #url
  
      
  #content
  paragraphs_container = soup.find('article', class_='jw_detail_content_holder content mb16') \
    if soup.find('article', class_='jw_detail_content_holder content mb16') else None

  paragraphs = None
  if paragraphs_container:
    paragraphs = paragraphs_container.find_all('p')

  content = ""
  if paragraphs:
    for paragraph in paragraphs:
      text = paragraph.get_text().strip()
      if text and not text.endswith(" "):
        text += " "
      content += text

  content = content.strip()
  
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
  if not url in processed_urls:
    articles.append(article)
  # insert_article(connection, article)
  # print("done")
  return 1
  

with open("starting_url.json", "r") as file:
  starting_url = json.load(file)

print(starting_url)
ending_url = 873730
total_urls = ending_url - starting_url + 1
# 90903 initial staring url
# 136353 ending url
workers = 1
t0 = time.time()

for i in range(starting_url, ending_url + 1, workers):
  try:
    with ThreadPoolExecutor(max_workers=workers) as article_pool:
      futures = [article_pool.submit(scrape_article, j) for j in range(i, min(ending_url + 1, i + workers))]
  except KeyboardInterrupt:
    countdown(10, i)
  with open('bangla_tribune_news_articles.jsonl', 'a', encoding='utf-8') as file:
    for article in articles:
      file.write(json.dumps(article, ensure_ascii=False) + '\n')
      processed_urls.add(article["url"])
  
  completed = min(ending_url, i + workers - 1) - starting_url + 1
  t1 = time.time()
  print_progress_bar(t0, t1, completed, total_urls)
  articles.clear()
  
  
t1 = time.time()
time_spent = int(t1 - t0)
seconds = time_spent % 60
time_spent //= 60
minutes = time_spent % 60
hours = time_spent // 60
print(f"\n{ending_url - starting_url + 1} urls processed in {hours} hour(s) {minutes} minute(s) {seconds} second(s).")
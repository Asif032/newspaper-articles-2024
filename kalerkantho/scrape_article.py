from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import json
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from datetime import datetime, timedelta
# from db import init, insert_article, insert_article_status, insert_date_status
import sys
import time
import keyboard
import traceback
import cloudscraper


# init()
scraper = cloudscraper.create_scraper()

processed_urls = set()
with open('samakal_news_articles.jsonl', 'r', encoding='utf-8') as file:
  for line in file:
    data = json.loads(line)
    if 'url' in data:
      processed_urls.add(data['url'])


def close_connection(connection):
  if connection:
    connection.close()
    print("Connection closed.")
    
def save_progress(start_date, start_idx):
  start_info = {}
  start_info["start_date"] = start_date.strftime("%Y-%m-%d")
  start_info["start_idx"] = start_idx
  
  with open('info/start_info.json', 'w') as file:
    json.dump(start_info, file, indent=2)
    
    
def load_progress():
  start_date = datetime.now()
  with open('info/start_info.json', 'r') as file:
    start_info = json.load(file)
    start_date = datetime.strptime(start_info["start_date"], "%Y-%m-%d")
    start_idx = int(start_info["start_idx"])
    return start_date, start_idx
  
  
def load_end_date():
  with open('info/end_info.json', 'r') as file:
    end_info = json.load(file)
    end_date = datetime.strptime(end_info["end_date"], "%Y-%m-%d")
    return end_date
  

def countdown(seconds, start_date, start_idx):
  print("Press 'Ctrl+C' to exit the program.")
  try:
    for i in range(seconds, 0, -1):
      sys.stdout.write(f"\r{i} seconds remaining...")
      sys.stdout.flush()
      time.sleep(1)
  except KeyboardInterrupt:
    save_progress(start_date, start_idx)
    print("\nExiting program...")
    sys.exit(0)
    
  print("\nExit window closed, resuming.")
  
    
  
def handle_article_error(status, url, default_date, date_modified, start_idx):
  if status == "KEYBOARD_INTERRUPT":
    return handle_connection_article_error(status, url, default_date, date_modified, start_idx, interrupted=True)
  if status == "CONNECTION_ERROR":
    return handle_connection_article_error(status, url, default_date, date_modified, start_idx)
  else:
    return handle_other_article_error(status, url, default_date, date_modified, start_idx)
  
  
def handle_connection_article_error(status, url, default_date, date_modified, start_idx, from_error=False, interrupted=False):
  retries = 1
  
  if interrupted:
    countdown(10, start_date, start_idx)
  
  while True:
    for k in range(8):
      print(f"retrying...({retries})")
      retries += 1
      article, status, status_code = scrape_article(url, default_date, date_modified)
      if status == "OK":
        return article, status, status_code
      if status != "CONNECTION_ERROR" and not from_error:
        return handle_other_article_error(status, url, default_date, date_modified, start_idx)
      
      countdown(1 << k, default_date, start_idx)
      
  return {}, status, status_code
  
  
def handle_other_article_error(status, url, default_date, date_modified, start_idx):
  for i in range(3):
    print(f"retrying...({i + 1})")
    article, status, status_code = scrape_article(url, default_date, date_modified)
    if status_code == 404:
      return article, status, status_code
    if status == "OK":
      return article, status, status_code
    if status == "CONNECTION_ERROR":
      return handle_connection_article_error(status, url, default_date, date_modified, start_idx, from_error=True)
    if status == "TIMEOUT":
      try:
        time.sleep(5)
      except KeyboardInterrupt:
        countdown(10, default_date, start_idx)
      
  return {}, status, status_code


articles = []

# Scrape URLs with multithreading, workers = 12,16 is optimal
def scrape_urls(default_date, start_idx = 0, workers=16):
  date = default_date.strftime("%Y-%m-%d")
  print(f"Processing articles of date: {date}")
  sitemap_url = f"https://www.samakal.com/sitemap/sitemap-daily-{date}.xml"
  status_code = -6
  response = None
  try:
    response = scraper.get(sitemap_url, timeout=10)
    response.raise_for_status()
  except HTTPError as e:
    print(f"{response.status_code} HTTP error occured.")
    return "HTTP_ERROR", start_idx
  except ConnectionError as e:
    status_code = -1
    print(f"Connection error occured.")
    return "CONNECTION_ERROR", start_idx
  except Timeout as e:
    status_code = -2
    print(f"Timeout occured.")
    return "TIMEOUT", start_idx
  except RequestException as e:
    status_code = -3
    print(f"Request exception occured.")
    return "REQUEST_EXCEPTION", start_idx
  except KeyboardInterrupt as e:
    status_code = -4
    print(f"Interrupted.")
    return "KEYBOARD_INTERRUPT"
  except Exception as e:
    status_code = -5
    print(f"Error fetching date. {e}")
    return "ERROR", start_idx
  finally:
    if response:
      status_code = response.status_code
    date_status = {
      "publication_date": date,
      "status_code": status_code
    }
    # insert_date_status(date_status)
  if not response or not response.content:
    print(f"Date has no urls.")
    return "NO_CONTENT", start_idx
  
  # Parse the sitemap and collect all article URLs
  soup = BeautifulSoup(response.content, 'xml')
  article_tags = soup.find_all('url')
  print(f"Total: {len(article_tags)} articles.")

  default_date = datetime.strptime(date, "%Y-%m-%d")
  # Collect URLs to be processed
  completed = start_idx
  errors = []
  batch = []
  for i, element in enumerate(article_tags[start_idx:], start=start_idx):
    url = element.find('loc').get_text().strip()
    last_slash_url = url.rfind('/')
    url = url[:last_slash_url]
    
    date_modified = element.find('lastmod').get_text().strip()
    date_modified = datetime.strptime(date_modified[:19], "%Y-%m-%dT%H:%M:%S") if date_modified else None
    batch.append((url, date_modified))
    if len(batch) == 0 or (len(batch) < workers and i != len(article_tags) - 1):
      continue
    try:
      print(f"Batch size: {len(batch)}, index: {i - len(batch) + 1}")
      with ThreadPoolExecutor(max_workers=workers) as article_pool:
        futures = {
          article_pool.submit(scrape_article, url, default_date, date_modified): (url, date_modified)
          for url, date_modified in batch
        }
        for future in as_completed(futures):
          url, date_modified = futures[future]
          article, status, status_code = future.result()
          if status in ("OK", "INVALID_URL") or status_code == 404:
            completed += 1
            print(url)
            print(f"{status}...{completed}/{len(article_tags)}")
          else:
            errors.append((url, date_modified, status))
    except KeyboardInterrupt as e:
          print("Interrupted.")
          return "KEYBOARD_INTERRUPT", start_idx
    except Exception as e:
      print(f"Thread interrupted: {e}")
      print(f"{traceback.format_exc()}")
      save_progress(default_date, start_idx)
      # return "ERROR", start_idx
      sys.exit(0)
      
    print(f"Multithreading completed, handling errors.")
    for url, date_modified, status in errors:
      article, status, status_code = handle_article_error(status, url, default_date, date_modified, start_idx)
      completed += 1
      print(url)
      print(f"{status}...{completed}/{len(article_tags)}")

    with open('samakal_news_articles.jsonl', 'a', encoding='utf-8') as file:
      for article in articles:
        file.write(json.dumps(article, ensure_ascii=False) + '\n')
        processed_urls.add(article["url"])
    
    start_idx = i + 1
    articles.clear()
    batch.clear()
    errors.clear()
  # with open('sample_article.json', 'w', encoding='utf-8') as file:
  #   json.dump(articles, file, indent=2, ensure_ascii=False)
  print(f"All articles processed for date: {date}")
  return "OK", 0
  
  
  
# Scrape article details from a single URL
def scrape_article(url, default_date, default_date_modified):
  # print(f"Processing article: {url}")
  response = None
  status_code = -5
  try:
    response = scraper.get(url, timeout=20)
    response.raise_for_status()
  except HTTPError as e:
    status_code = response.status_code
    print(f"{response.status_code} HTTP error occured. {url}")
    return {}, "HTTP_ERROR", response.status_code
  except ConnectionError as e:
    status_code = -1
    print(f"Connection error occured.")
    return {}, "CONNECTION_ERROR", -1
  except Timeout as e:
    status_code = -2
    print(f"Timeout occured.")
    return {}, "TIMEOUT", -2
  except RequestException as e:
    status_code = -3
    print(f"Request exception occured.")
    return {}, "REQUEST_EXCEPTION", -3
  except Exception as e:
    status_code = -4
    print(f"Error fetching article")
    return {}, "ERROR", -4
  finally:
    if not response or response.status_code != 200:
      if response:
        status_code = response.status_code
      article_status = {
        "url": url,
        "status_code": status_code,
        "publication_date": default_date.date()
      }
      # insert_article_status(article_status)
  if response and not response.content:
    print(f"Article has no content.")
    return {}, "NO_CONTENT", -5

  soup = BeautifulSoup(response.content, 'lxml')
  # Extract various fields from the article page
  
  date_published = default_date
  date_modified = default_date
  if default_date_modified:
    date_modified = default_date_modified
    
  json_ld_scripts = soup.find_all("script", type="application/ld+json")
  for script in json_ld_scripts:
    try:
      data = json.loads(script.string)
      if 'datePublished' in data:
        date_published = datetime.strptime(data['datePublished'], "%Y-%m-%d %H:%M:%S")
      if 'dateModified' in data:
        date_modified_str = data['dateModified']
        if len(date_modified_str) == 19:
          date_modified = datetime.strptime(date_modified_str, "%Y-%m-%d %H:%M:%S")
    except json.JSONDecodeError:
      continue
    
  author_ = soup.find('div', class_='writter')
  author = author_.get_text().strip() if author_ else None
  # print(f"author: {author}")

  # category
  category_container = soup.find_all('li', class_='breadcrumb-item')
  category = None
  if len(category_container) >= 2:
    category = category_container[1].get_text().strip()
  # print(f"category: {category}")

  # tag
  tag = []
  tag_container = soup.find('div', class_="tagArea") if soup.find('div', class_="tagArea") else None
  if tag_container: 
    tag_list = tag_container.find_all('a') if tag_container.find('a') else None
    if tag_list:
      for tag_ in tag_list:
        tag.append(tag_.get_text().strip())

  # title
  title = soup.find('h1').get_text().strip() if soup.find('h1') else None
  # print(f"title: {title}")

  # content
  paragraphs_container = soup.find('div', class_='dNewsDesc') if soup.find('div', class_='dNewsDesc') else None
  # if paragraphs_container == None:
  #   print(f"No content: {url}")

  paragraphs = None
  if paragraphs_container:
    paragraphs = paragraphs_container.find_all('p')

  content = ""
  if paragraphs:
    for paragraph in paragraphs:
      content += paragraph.get_text().strip() + " "

  content = content.strip()
  content = content.replace("\r\n", " ")
  # print("done")

  article = {
    "date_published": date_published.isoformat(),
    "date_modified": date_modified.isoformat(),
    "author": author,
    "category": category,
    "tag": tag,
    "title": title,
    "url": url,
    "content": content
  }
  if url not in processed_urls:
    articles.append(article)
  # with open('sample_article.json', 'w', encoding='utf-8') as file:
  #   json.dump(article, file, indent=2, ensure_ascii=False)
  # articles.append(article)
  return article, "OK", response.status_code
  

# if __name__ == "__main__":
  # scrape_article('https://samakal.com/economics/article/264110', datetime.now(), datetime.now().date())
  # scrape_urls(datetime.now().date())
    
    
    
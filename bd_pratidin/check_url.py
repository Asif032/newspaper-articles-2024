import requests
from bs4 import BeautifulSoup
import json
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from datetime import datetime, timedelta
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from db import article_exists, article_status_exists, insert_article_status



def save_progress(start_date):
  start_info = {}
  start_info["start_date"] = start_date.strftime("%Y-%m-%d")
  
  with open('metadata/start_info.json', 'w') as file:
    json.dump(start_info, file, indent=2)
    
    
def load_progress():
  start_date = datetime.now()
  with open('metadata/start_info.json', 'r') as file:
    start_info = json.load(file)
    start_date = datetime.strptime(start_info["start_date"], "%Y-%m-%d")
    return start_date
  
  
def load_end_date():
  with open('metadata/end_info.json', 'r') as file:
    end_info = json.load(file)
    end_date = datetime.strptime(end_info["end_date"], "%Y-%m-%d")
    return end_date

def valid_url(url):
  return not any([
    url[12:22] != 'samakal',
    url[27:32] == 'photo',
    url[27:32] == 'video',
    url[27:37] == 'ampstories'
  ])
  
  
  
def get_urls_for_date(current_date):
  date = current_date.strftime("%Y-%m-%d")
  sitemap_url = f"https://www.samakal.com/sitemap/sitemap-daily-{date}.xml"
  response = requests.get(sitemap_url)
  soup = BeautifulSoup(response.content, 'xml')
  article_tags = soup.find_all('url')
  urls = []
  for element in article_tags:
    url = element.find('loc').get_text().strip()
    urls.append(url)
  return urls



def check_url(url):
  if not article_exists(url) and not article_status_exists(url):
    article_status = {
      "url": url,
      "status_code": -20,
      "publication_date": current_date.date()
    }
    insert_article_status(article_status)
    return True
  
  return False
  
def check_urls_for_date(date):
  urls = get_urls_for_date(date)
  print(f"Checking urls for date: {date.strftime('%Y-%m-%d')}, Total: {len(urls)}")
  batch = []
  incompleted_urls = 0
  for i, url in enumerate(urls):
    batch.append(url)
    if len(batch) == 24 or i == len(urls) - 1:
      try:
        with ThreadPoolExecutor(max_workers=24) as url_pool:
          futures = {
            url_pool.submit(check_url, url): (url)
            for url in batch
          }
          for future in as_completed(futures):
            res = future.result()
            if res:
              incompleted_urls += 1
      except Exception as e:
        print(e)
      except KeyboardInterrupt:
        sys.exit(0)
      print(f"\r{i + 1}/{len(urls)}", end='') 
      batch.clear()
  print(f"\nIncompleted urls: {incompleted_urls}")
  
  
if __name__ == "__main__":
  start_date = load_progress()
  end_date = load_end_date()
  print(start_date.date(), end_date.date())
  t0 = time.time()
  dates_processed = 0
  current_date = start_date
  while current_date <= end_date:
    check_urls_for_date(current_date)
    current_date += timedelta(days=1)
    dates_processed += 1
    save_progress(current_date)
  
  t1 = time.time()
  time_spent = int(t1 - t0)
  seconds = time_spent % 60
  time_spent //= 60
  minutes = time_spent % 60
  hours = time_spent // 60
  print(f"{dates_processed} dates processed in {hours} hour(s) {minutes} minute(s) {seconds} second(s).")
  print(f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

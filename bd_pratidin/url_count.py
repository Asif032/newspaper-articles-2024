import requests
from bs4 import BeautifulSoup
import json
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from datetime import datetime, timedelta
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


unique_urls = set()

def valid_url(url):
  return not any([
    url[12:22] != 'prothomalo',
    url[27:32] == 'photo',
    url[27:32] == 'video',
    url[27:37] == 'ampstories'
  ])

def get_valid_invalid_url_count_for_date(current_date):
  urls = set()
  date = date = current_date.strftime("%Y-%m-%d")
  sitemap_url = f"https://www.prothomalo.com/sitemap/sitemap-daily-{date}.xml"
  response = requests.get(sitemap_url)
  soup = BeautifulSoup(response.content, 'xml')
  article_tags = soup.find_all('url')
  valid_urls = 0
  invalid_urls = 0
  for element in article_tags:
    url = element.find('loc').get_text().strip()
    if url in urls:
      print(f"Duplicate: {url}")
    if valid_url(url):
      valid_urls += 1
    else:
      invalid_urls += 1
      print(f"{date}: {url}")
  # print(f"{date}: Total: {len(article_tags)}, Valid: {valid_urls}, invalid: {invalid_urls}")
  return valid_urls, invalid_urls

def get_url_count_for_date(current_date):
  date = date = current_date.strftime("%Y-%m-%d")
  sitemap_url = f"https://www.prothomalo.com/sitemap/sitemap-daily-{date}.xml"
  response = requests.get(sitemap_url)
  soup = BeautifulSoup(response.content, 'xml')
  article_tags = soup.find_all('url')
  return len(article_tags)

def get_url_count(dates):
  total_url_count = 0
  batch = []
  for i, date in enumerate(dates):
    batch.append(date)
    if len(batch) == 16 or i == len(dates) - 1:
      with ThreadPoolExecutor(max_workers=16) as date_pool:
        futures = [
          date_pool.submit(get_url_count_for_date, date)
          for date in batch
        ]
        for future in as_completed(futures):
          url_count = future.result()
          total_url_count += url_count
          
      print(f"\r{date.date()}: {total_url_count}", end='')
      batch.clear()
  return total_url_count
  
if __name__ == "__main__":
  start_date = datetime(2009, 8, 28)
  end_date = datetime(2014, 12, 31)
    
  t0 = time.time()
  current_date = start_date
  dates = []
  while current_date <= end_date:
    dates.append(current_date)
    current_date += timedelta(days=1)
  
  total_urls = get_url_count(dates)  
  t1 = time.time()
  time_spent = int(t1 - t0)
  seconds = time_spent % 60
  time_spent //= 60
  minutes = time_spent % 60
  hours = time_spent // 60
  print(f"{len(dates)} dates processed in {hours} hour(s) {minutes} minute(s) {seconds} second(s).")
  
  print(f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:\
    Total urls: {total_urls}")
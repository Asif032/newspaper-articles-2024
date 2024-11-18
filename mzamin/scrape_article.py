from bs4 import BeautifulSoup
import requests
import json
import sys
import time
from db import create_connection, init, insert_article, insert_status
from datetime_converter import convert_to_english
 

# connection = create_connection("localhost", "user", "password", "ittefaq_news_article")
# init(connection)


def scrape_article(request_id):
  url = base_url + str(i)
  response = None
  print(f"Processing {url}...")
  
  try:
    response = requests.get(url)
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
    insert_status(connection, status_report)
    if response and response.status_code != 200:
      return 0
 
  # print("outside finally")
  soup = BeautifulSoup(response.content, 'lxml')
  # with open("article.html", "w", encoding="utf-8") as file:
  #   file.write(soup.prettify())
  
  #date_published
  date_published = soup.find(itemprop='datePublished').get_text(strip=True) if soup.find(itemprop='datePublished') else None
  # date_published = convert_to_english(date_published[9:])
  # if date_published and len(date_published) >= 10:
  #   date_published = date_published[9:]
  
  #date_modified
  date_modified = soup.find(itemprop='dateModified').get_text(strip=True) if soup.find(itemprop='dateModified') else None
  # date_modified = convert_to_english(date_modified[8:])
  # if date_published and len(date_published) >= 9:
  #   date_modified = date_modified[8:]
  
  #author
  author = soup.find(itemprop='author').get_text(strip=True) if soup.find(itemprop='author') else None
  author = [a.strip() for a in author.split(',')] if author else []
  
  #category
  category = soup.find(class_='secondary_logo').get_text(strip=True) if soup.find(class_='secondary_logo') else None
  
  #tag
  topic_list = soup.find(class_ = 'topic_list')
  tag = []
  if topic_list:
    tag_ = topic_list.find_all('strong')
    for t in tag_:
      tag.append(t.get_text(strip=True))
  else:
    tag = None
    
  #title
  title = soup.find('h1', itemprop='headline').get_text(strip=True) if soup.find('h1', itemprop='headline') else None
  
  #url
  main_entity = soup.find(attrs={"itemprop": "mainEntityOfPage"})
  
  if main_entity:
    content_value = main_entity.get("content")
    
    full_url = content_value
    # Find the position of the second slash after the domain
    first_slash = full_url.find('/', 8)  # The 8 skips the 'https://'
    second_slash = full_url.find('/', first_slash + 1)

    if second_slash != -1:
      url = full_url[:second_slash]
    else:
      url = full_url
      
  #content
  content = soup.find(itemprop='articleBody').get_text(strip=True) if soup.find(itemprop='articleBody') else None
  
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
  
  # inserting the article into mysql database
  insert_article(connection, article)
  return 1
  
  
  
base_url = 'https://www.ittefaq.com.bd/'

with open("starting_url.json", "r") as file:
  staring_url = json.load(file)

# 672352 initial staring url
# 704500 ending url

ending_url = 706874
for i in range(staring_url, ending_url + 1):
  f = scrape_article(i)
  next_start = i + 1
  if (f == -1):
    next_start = i
  with open("starting_url.json", "w") as file:
    json.dump(next_start, file)
  if (f == -1):
    sys.exit(-1)
  
connection.close()
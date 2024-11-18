import requests
from datetime import datetime, timedelta
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
import keyboard
import sys

def scrape_urls(date):
  sitemap_url = f"https://www.prothomalo.com/sitemap/sitemap-daily-{date}.xml"
  response = None
  try:
    response = requests.get(sitemap_url,timeout=5)
    response.raise_for_status()
  except HTTPError as http_err:
    print(f"{response.status_code} HTTP error occurred.")
    status_code = response.status_code
    return "HTTP_ERROR"
  except ConnectionError as conn_err:
    print(f"Connection error occurred.")
    status_code = -2
    return "CONNECTION_ERROR"
  except Timeout as timeout_err:
    print(f"Timeout error occurred.")
    status_code = -3
    return "TIMEOUT_ERROR"
  except RequestException as err:
    status_code = -4
    print(f"An error occurred.")
    return "CONNECTION_ERROR"
  except KeyboardInterrupt:
    print(f"Interrupted.")
    sys.exit(0)
    status_code = -7
    return "KEYBOARD_INTERRUPT"
  except Exception as err:
    status_code = -5
    print(f"An error occurred.")
    return "ERROR"
  finally:
    if response and not response.content:
      return "NO_CONTENT"
  
  return "OK"


def binary_search(l, r):
  res = r
  while (l <= r):
    mid = l + (r - l) / 2
    mid.replace(hour=0, minute=0, second=0, microsecond=0)
    mid_date_str = mid.strftime("%Y-%m-%d")
    response = scrape_urls(mid_date_str)
    print(f"{response} {mid_date_str}")
    if response == "OK":
      res = mid
      r = mid - timedelta(days=1)
    else:
      l = mid + timedelta(days=1)
    
  return res.strftime("%Y-%m-%d")


def linear_search(l, r):
  res = r
  while (l <= r):
    current_date = l
    current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    current_date_str = current_date.strftime("%Y-%m-%d")
    response = scrape_urls(current_date_str)
    if response == "OK":
      print(f"OK {current_date_str}")
      res = current_date
  return res.strftime("%Y-%m-%d")  
      
if __name__ == "__main__":
  l = datetime(2005, 1, 1)
  r = datetime(2024, 10, 31)
  res = binary_search(l, r)
  print(f"The earliest available articles are of {res}")
  # res = linear_search(datetime(2009, 7, 1), datetime(2009, 8, 28))
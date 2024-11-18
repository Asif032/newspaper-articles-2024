from datetime import datetime, timedelta
from scrape_article import scrape_urls
import json
import time
import sys
import keyboard


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


def handle_date_error(status, start_date, start_idx):
  if status == "KEYBOARD_INTERRUPT":
    return handle_date_connection_error(status, start_date, start_idx, interrupted=True)
  if status == "CONNECTION_ERROR":
    return handle_date_connection_error(status, start_date, start_idx)
  else:
    return handle_other_date_error(status, start_date, start_idx)
  
  
def handle_date_connection_error(status, start_date, start_idx, from_error=False, interrupted=False):
  if interrupted:
    countdown(10, start_date, start_idx)
  retries = 1
  while True:
    for k in range(8):
      print(f"retrying...({retries})")
      retries += 1
      status, start_idx = scrape_urls(start_date, start_idx)
      if status == "OK":
        return status, start_idx
      if status != "CONNECTION_ERROR" and not from_error:
        return handle_other_date_error(status, start_date, start_idx)
      
      countdown(1 << k, start_date, start_idx)
      
  return status, start_idx
  
  
def handle_other_date_error(status, start_date, start_idx):
  for i in range(3):
    print(f"retrying...({i + 1})")
    status, start_idx = scrape_urls(start_date, start_idx)
    if status == "OK":
      return status, start_idx
    if status == "CONNECTION_ERROR":
      return handle_date_connection_error(status, start_date, start_idx, True)
    try:
      if status == "TIMEOUT_ERROR":
        time.sleep(5)
      else:
        time.sleep(3)
    except KeyboardInterrupt:
      countdown(10, start_date, start_idx)
      
  return status, start_idx


def scrape_new_articles():
  start_date, start_idx = load_progress()
  end_date = load_end_date()
  current_date = start_date
  t0 = time.time()
  dates_processed = 0
  while current_date <= end_date:
    status, start_idx = scrape_urls(current_date, start_idx)
    
    if status != "OK":
      status, start_idx = handle_date_error(status, current_date, start_idx)
    if status == "CONNECTION_ERROR":
      save_progress(current_date, start_idx)
      sys.exit(0)
      
    current_date += timedelta(days=1)
    save_progress(current_date, 0)
    dates_processed += 1
    
    t1 = time.time()
    time_spent = int(t1 - t0)
    seconds = time_spent % 60
    time_spent //= 60
    minutes = time_spent % 60
    hours = time_spent // 60
    print(f"{dates_processed} dates processed in {hours} hour(s) {minutes} minute(s) {seconds} second(s).")
    
    # if dates_processed % 5 == 0:
    #   countdown(15, current_date.strftime("%Y-%-m-%d"), start_idx)
      
if __name__ == "__main__":
    scrape_new_articles()
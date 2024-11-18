import pandas as pd
df = pd.read_csv('ittefaq_news_articles.csv')

start = 695800 - 400
base_url = 'https://www.ittefaq.com.bd/'

for i in range(start, start + 200):
  url = base_url + str(start)
  start += 1
  print(url, df[df['url'] == url]['date_published'].values)
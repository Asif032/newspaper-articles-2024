# from MySQLdb import Connection
import mysql.connector
from mysql.connector import Error

def create_connection(hostname, username, password, db_name):
  connection = None
  try:
    connection = mysql.connector.connect(
      host = hostname,
      user = username,
      password = password,
      database = db_name
    )
  except Error as e:
    print(e)
  
  return connection



def init(connection):
  create_article_table_query = """
    CREATE TABLE IF NOT EXISTS article (
    date_published VARCHAR(255),
    date_modified VARCHAR(255),
    author JSON,
    category VARCHAR(255),
    tag JSON,
    title VARCHAR(255),
    url VARCHAR(255),
    content TEXT
  );
  """
  
  create_status_table_query = """
    CREATE TABLE IF NOT EXISTS status (
    id INT PRIMARY KEY,
    status_code INT
  );
  """
  
  cursor = connection.cursor()
  try:
    cursor.execute(create_article_table_query)
    cursor.execute(create_status_table_query)
    # commit the changes
    connection.commit()
  except Error as e:
    print(e)
  finally:
    cursor.close()


import json

import json

def insert_article(connection, article):
  # Convert the 'tag' list to a JSON string
  if isinstance(article.get('tag'), list):
    article['tag'] = json.dumps(article['tag'], ensure_ascii=False)
    
  # Convert the 'author' list to a JSON string
  if isinstance(article.get('author'), list):
    article['author'] = json.dumps(article['author'], ensure_ascii=False)
  
  query = """
    INSERT INTO article (date_published, date_modified, author, category, tag, title, url, content)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
  """
  
  # Pass the article values as a tuple
  cursor = connection.cursor()
  try:
    cursor.execute(query, tuple(article.values()))
    connection.commit()
    print(f"done")
  except mysql.connector.Error as e:
    print(f"Error inserting article: {e}")
  finally:
    cursor.close()


    

def insert_status(connection, status):
  # columns = ', '.join(status.keys())
  # placeholders = ', '.join(['%s'] * len(status))
  # query = f"INSERT INTO statuss ({columns}) VALUES ({placeholders})"
  
  query = """
    INSERT INTO status (id, status_code)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE status_code = VALUES(status_code);
  """
  
  cursor = connection.cursor()
  try:
    cursor.execute(query, tuple(status.values()))
    connection.commit()
  except Error as e:
    print(f"The error '{e}' occurred")
  finally:
    cursor.close()
  
  
  
# def find_status(connection, request_id)
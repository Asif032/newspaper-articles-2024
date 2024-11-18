from concurrent.futures import ThreadPoolExecutor
import mysql.connector
from mysql.connector import Error
import json

from mysql.connector import pooling

connection_pool = pooling.MySQLConnectionPool(
  pool_name="my_pool",
  pool_size=20,
  host="localhost",
  user="user",
  password="password",
  database="samakal_2024"
)

def init():
  connection, cursor = get_connection()
  create_article_table_query = """
    CREATE TABLE IF NOT EXISTS article (
      date_published DATETIME,
      date_modified DATETIME,
      author VARCHAR(255),
      category VARCHAR(255),
      tag JSON,
      title VARCHAR(255),
      url VARCHAR(255),
      content TEXT,
      PRIMARY KEY(url, date_published)
    );
  """
  
  create_date_status_table_query = """
    CREATE TABLE IF NOT EXISTS date_status (
      publication_date DATE PRIMARY KEY,
      status_code INT
    );
  """
  
  create_article_status_table_query = """
    CREATE TABLE IF NOT EXISTS article_status (
      url VARCHAR(255),
      status_code INT,
      publication_date DATE,
      PRIMARY KEY(url, publication_date),
      FOREIGN KEY (publication_date) REFERENCES date_status(publication_date)
    );
  """
  
  try:
    cursor.execute(create_article_table_query)
    cursor.execute(create_date_status_table_query)
    cursor.execute(create_article_status_table_query)
    # commit the changes
    connection.commit()
  except Error as e:
    print(e)



def get_connection():
  connection = connection_pool.get_connection()
  return connection, connection.cursor()


def release_connection(connection):
  connection.commit()
  connection.close()
  connection_pool.release(connection)


def insert_article(article):
  connection, cursor = get_connection()
  if isinstance(article.get('tag'), list):
    article['tag'] = json.dumps(article.get('tag'), ensure_ascii=False)

  query = """
    INSERT IGNORE INTO article (date_published, date_modified, author, category, tag, title, url, content)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
  """
  try:
    # Pass the article values as a tuple
    cursor.execute(query, tuple(article.values()))
    connection.commit()
  except Error as e:
    print(f"Error inserting article: {e}")
  finally:
    cursor.close()
    connection.close()


def insert_date_status(status):
  connection, cursor = get_connection()
  query = """
    INSERT INTO date_status (publication_date, status_code)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE status_code = VALUES(status_code);
  """
  
  try:
    cursor.execute(query, tuple(status.values()))
    connection.commit()
  except Error as e:
    print(f"The error '{e}' occurred")
  finally:
    cursor.close()
    connection.close()
  

def insert_article_status(status):
  connection, cursor = get_connection()
  query = """
    INSERT INTO article_status (url, status_code, publication_date)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE status_code = VALUES(status_code);
  """
  
  try:
    cursor.execute(query, tuple(status.values()))
    connection.commit()
  except Error as e:
    print(f"The error '{e}' occurred")
  finally:
    cursor.close()
    connection.close()
    
    
def article_exists(url):
  connection, cursor = get_connection()
  query = "SELECT EXISTS(SELECT 1 FROM article WHERE url = %s)"
  try:
    cursor.execute(query, (url,))
    exists = cursor.fetchone()[0]
    return bool(exists)
  except Error as e:
    print(f"The error '{e}' occurred")
  finally:
    cursor.close()
    connection.close()
    
    

    
def article_status_exists(url):
  connection, cursor = get_connection()
  query = "SELECT EXISTS(SELECT 1 FROM article_status WHERE url = %s)"
  try:
    cursor.execute(query, (url,))
    exists = cursor.fetchone()[0]
    return bool(exists)
  except Error as e:
    print(f"The error '{e}' occurred")
  finally:
    cursor.close()
    connection.close()
    
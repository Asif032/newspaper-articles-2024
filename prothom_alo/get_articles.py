import pandas as pd
import mysql.connector

# Database connection configuration
config = {
    'user': 'user',
    'password': 'password',
    'host': 'localhost',
    'database': 'prothom_alo_2024'
}

# Connect to the database
connection = mysql.connector.connect(**config)

# Read the table into a DataFrame
query = f"SELECT * FROM article"
df = pd.read_sql(query, connection)

# Close the connection
connection.close()

# Save as CSV
df.to_csv('output.csv', index=False, encoding='utf-8')

# Save as JSONL (JSON Lines format)
df.to_json('output.jsonl', orient='records', lines=True, force_ascii=False)

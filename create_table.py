import sqlite3

# Create a database connection
conn = sqlite3.connect('test.db')

# Create a cursor
cursor = conn.cursor()

# Create table
cursor.execute('''
   CREATE TABLE IF NOT EXISTS tree_items (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT NOT NULL,
       data TEXT,
       parent_id INTEGER,
       FOREIGN KEY(parent_id) REFERENCES tree_items(id)
   );
''')

# Save (commit) the changes
conn.commit()

# Close the connection
conn.close()
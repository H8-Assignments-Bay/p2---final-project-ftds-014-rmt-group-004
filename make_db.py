
import sqlite3

conn = sqlite3.connect('./data/data_sepatu.db')
cur = conn.cursor()

# Do some setup
cur.executescript('''
DROP TABLE IF EXISTS shoes;
DROP TABLE IF EXISTS product_stock;

CREATE TABLE shoes (
    product_id     INTEGER NOT NULL PRIMARY KEY UNIQUE,
    name   TEXT UNIQUE,
    brand  TEXT ,
    color  TEXT,
    price  TEXT,
    gender VARCHAR(7),
    image TEXT
);

CREATE TABLE product_stock (
    product_id      INTEGER,
    size            tinyint,
    stock           tinyint
)
''')

# fname = 'roster_data.json'
# # [
# #   [ "Charley", "si110", 1 ],
# #   [ "Mea", "si110", 0 ],

# str_data = open(fname).read()
# json_data = json.loads(str_data)

# for entry in json_data:

#     name = entry[0]
#     title = entry[1]
#     role = entry[2]

#     # print((name, title,role))

#     cur.execute('''INSERT OR IGNORE INTO User (name)
#         VALUES ( ? )''', ( name, ) )
#     cur.execute('SELECT id FROM User WHERE name = ? ', (name, ))
#     user_id = cur.fetchone()[0]
    
#     cur.execute('''INSERT OR IGNORE INTO Course (title)
#         VALUES ( ? )''', ( title, ) )
#     cur.execute('SELECT id FROM Course WHERE title = ? ', (title, ))
#     course_id = cur.fetchone()[0]

#     cur.execute('''INSERT OR REPLACE INTO Member
#         (user_id, course_id, role) VALUES ( ?, ?, ? )''',
#         ( user_id, course_id,role ) )




conn.commit()


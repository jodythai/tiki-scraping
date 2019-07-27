# Import libraries

import pandas as pd
import requests
from bs4 import BeautifulSoup
import psycopg2

tbl_prefix = "tiki_"

conn = psycopg2.connect("dbname=fansipan_week2 user=duong password=P@ssw0rd")
cur = conn.cursor()

sql = "DELETE FROM " + tbl_prefix + "products"

cur.execute(sql)
conn.commit() 

cur.close()
conn.close()
# Import libraries
import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup
import psycopg2
import logging

# Define constants and table prefix
tbl_prefix = "tiki_"
SCRAPING_URL = "https://tiki.vn"


def print_exception(err):
	"""
	This function is used to render the Exception error
	"""
	logging.exception(err)

def connect_to_db():
	""" This function returns a database connection
	"""
	try:
		connection = psycopg2.connect(user = "duong",
										password = 'P@ssw0rd',
										host = "127.0.0.1",
										port = "5432",
										database = "fansipan_week2_test1")
		return connection

	except (Exception, psycopg2.Error) as err:
		print_exception(err)

# Parser function to retrieve and parse the HTML code of a website 
def parser(url):
	"""Get a parsed version of an URL"""

	try:
		# Retrieve plain HTML code
		plain = requests.get(url).text

		# Parse the plain content into structured one
		soup = BeautifulSoup(plain, features="lxml")

		return soup

	except Exception as err:
		print_exception(err)

def scrape_products(cat_id, cat_name, url):
	"""Scrape product information of all products on one page"""

	try:
		# Initialize empty 'results' list
		results = []

		# Get the parsed html code
		soup = parser(url)

		# Find all products on this page
		product_items = soup.find_all('div', class_='product-item')

		# If there is no products, return an empty list.
		if len(product_items) == 0:
			return []
		
		# If the page has products
		else: 
      		
			# Set default values for some variables
			rating = -1
			tiki_now = ''
			product_url = ''
			review_total = 0

			# Iterate through all product_items and store the product information in the 'row' list
			for product in product_items:
				
        		# Extract the rating value
				if len(product.select('.rating-content > span')) > 0:
					rating = product.select_one('.rating-content > span')["style"]
					rating = rating.replace('width:', '').replace('%', '')
				
        		# Extract the number of reviews value
				if len(product.select('.review-wrap .review')) > 0:
					review_total = product.select_one('.review-wrap .review').string
					review_total = review_total[review_total.find('(')+1:review_total.find(' ')]

				# Extract the regular price
				price_regular = product.find('span', class_="price-regular").text
				if price_regular != '':
					price_regular = price_regular[0:-2].replace('.', '')
				else:
					price_regular = -1

				# Extract the final price
				price_final = product.get('data-price')
				if price_final == '' or price_final == None:
						price_final = -1

				# Extract the Tiki Now value
				tiki_now = True if len(product.select('i.icon-tikinow')) > 0 else False

				# Extract the product url
				product_url = product.select_one('a')['href']

				# Add the insert to db date
				insert_date = datetime.datetime.now()

				row = 	{	'product_id' : product.get('data-id'), 
							'seller_id' : product.get('data-seller-product-id'),
							'cat_id' : cat_id,
							'title' : product.get('data-title'),
							'image_url' : product.img['src'],
							'price_regular' : price_regular,
							'price_final' : price_final,
							'rating' : rating,
							'tiki_now' : tiki_now,
							'product_url' : product_url,
							'review_total' : review_total,
							'insert_date' : insert_date
						}

				# Add the product information of each product into the 'results' list
				results.append(row)

		return results
	except Exception as err:
		print_exception(err)

def create_db_table__categories():
	""" This function will create the database table tiki_categories
	"""
	try:
		# Connect to the database and create a cursor
		conn = connect_to_db()
		cursor = conn.cursor()
		
		# Create the SQL query
		sql = 	"CREATE TABLE IF NOT EXISTS " + tbl_prefix + "categories \
				(cat_id SERIAL NOT NULL PRIMARY KEY, \
				cat_name text NOT NULL, \
				cat_url text NOT NULL)"

		# Execute the query
		cursor.execute(sql)

		# Commit the changes made to the database
		conn.commit()

	except (Exception, psycopg2.Error) as err:
		print_exception(err)
		# In case of error, cancel all changes made to our database during the connection
		conn.rollback()

	finally:
		# Close database connection
		cursor.close()
		conn.close()

def create_db_table__products():
	""" This function will create the database table tiki_products
	"""
	try:
		# Connect to the database and create a cursor
		conn = connect_to_db()
		cursor = conn.cursor()
		
		# Create the SQL query
		# Note: because not all products return all prices, so to prevent error in the inserting process,
		# we decide to use varchar as the data type for prices and convert data type for further use
		sql = 	"CREATE TABLE IF NOT EXISTS " + tbl_prefix + "products \
				(product_id integer NOT NULL PRIMARY KEY, \
				seller_id integer NOT NULL, \
				cat_id integer NOT NULL REFERENCES " + tbl_prefix + "categories(cat_id), \
				title text NOT NULL, \
				image_url text, \
				price_regular integer, \
				price_final integer, \
				rating float, \
				tiki_now boolean, \
				product_url text NOT NULL, \
				review_total integer, \
				insert_date timestamp)"

		# Execute the query
		cursor.execute(sql)

		# Commit the changes made to the database
		conn.commit()

	except (Exception, psycopg2.Error) as err:
		print_exception(err)
		# In case of error, cancel all changes made to our database during the connection
		conn.rollback()

	finally:
		# Close database connection
		cursor.close()
		conn.close()


def insert_to_db__categories():
	""" Get the URLs of all categories information on Tiki.vn
		and store the data into our database
	"""
	try:
		# Get the homepage's html in BeautifulSoup format
		soup = parser(SCRAPING_URL)

		# Connect to the database and create a cursor
		conn = connect_to_db()
		cursor = conn.cursor()
		
		# Scrape through the main category navigation bar
		for i in soup.find_all('li', class_="MenuItem-tii3xq-0"):
			
			# Get the category value
			category = i.a.find('span', class_='text').text
			
			# Get the url value
			url = i.a["href"]

			# Build the SQL query with our data
			data = {"cat_name" : category, "cat_url" : url}
			
			# Check for existed category in the database
			sql =  "SELECT 1 FROM " + tbl_prefix + "categories \
					WHERE cat_url = \'" + data['cat_url'] + "\'"
			cursor.execute(sql)

			# If there is no existed category in the databse, then insert 
			if cursor.fetchone() is None:
				# Create our SQL query
				sql = "INSERT INTO " + tbl_prefix + "categories (cat_name, cat_url)\
						VALUES(%(cat_name)s, %(cat_url)s)"

				# Execute the query
				cursor.execute(sql, data)

				# Commit to insert data into the database
				conn.commit()

	except (Exception, psycopg2.Error) as err:
		print_exception(err)
		# In case of error, cancel all changes made to our database during the connection
		conn.rollback()
	
	finally:
		# Close the database connection
		cursor.close()
		conn.close()

def insert_to_db__products():
	""" Get the URLs of all products information on Tiki.vn
		and insert the data into our database on table tiki_products
	"""
	try:
		# Connect to the database and create a cursor
		conn = connect_to_db()
		cursor = conn.cursor()
		
		# Get all category links from tiki_categories table in the database
		queue = select_from_db(tbl_prefix + "categories")

		# Initialize the 'page' variable, which indicates the current product page of the current category
		page = 1

		# While there are links in the queue, we will run through each link and get the products
		while len(queue) > 0:

			# We will proceed from the last link in the queue     
			cat_id = queue[-1][0]
			cat_name = queue[-1][1]
			url = queue[-1][2]

			# Check to keep the original category's url and its category name
			if "page" not in url:
				url_orig = url
				cat_id_orig = cat_id
				cat_name_orig = cat_name
				
			# Remove the last link in queue so that new product url from page 2 will be added at the end of the queue
			queue.pop() 
			
			print('Scraping', cat_name_orig + " page " + str(page))
			print(url)
			
			# Get the list of products of the current page and store it in a temporary variable
			list_current_products = scrape_products(cat_id, cat_name, url)
			
			# If the page has products, we will create the next product page link and add it to the queue
			if len(list_current_products) > 0:

				# Generate next page url and add it to the end of list `queue` so that it will be the next link to be scraped
				page += 1
				url = url_orig + "&page=" + str(page)

				print('Insert to db\n')
				for product in list_current_products:
					
					# Check for existed products in the database
					sql =  "SELECT 1 FROM " + tbl_prefix + "products \
							WHERE product_id = " + product['product_id']
					cursor.execute(sql)
					
					# If there is no existed product in the databse, then insert 
					if cursor.fetchone() is None:

						# Create our SQL query
						sql = "INSERT INTO " + tbl_prefix + "products \
								VALUES (%(product_id)s, %(seller_id)s, %(cat_id)s, %(title)s, \
										%(image_url)s, %(price_regular)s, %(price_final)s, %(rating)s, \
										%(tiki_now)s, %(product_url)s, %(review_total)s, %(insert_date)s)"

						# Execute the query to insert a product to the database
						cursor.execute(sql, product)
						conn.commit()

				# Add the new page url to the end of list `queue`
				queue.append([cat_id_orig, cat_name_orig, url]) 
					
				print('Add next page', page)
			else: 
				# Now the product page link doesn't return any product, which indicates that we have done getting all products...
				# ...of the current category. We will reset the page number to 1 in order to scrape the next category
				page = 1

	except (Exception, psycopg2.Error) as err:
		print_exception(err)

		# In case of error, cancel all changes made to our database during the connection
		conn.rollback()
	
	finally:
		# Close the database connection
		cursor.close()
		conn.close()

def select_from_db(sql):
	"""
	This function will execute the SELECT query and return the list of results
	1. If the input is a table name, it will return a list of all rows from that table
	2. If the input is a SQL query, it will execute that query and return the desire results
	"""
	try:
		
		#Create an empty list
		list_results = []

		# Connect to the database
		conn = connect_to_db()

		# Create a cursor
		cursor = conn.cursor()

		# Get data from the database
		# If the input variable starts with the table prefix, then this is the standard SELECT query
		# Otherwise, we will use the input value as the query
		if sql.startswith(tbl_prefix):
			sql = "SELECT * FROM " + sql
	
		cursor.execute(sql)

		list_results = cursor.fetchall()

		return list_results

	except (Exception, psycopg2.Error) as err:
		print_exception(err)
		conn.rollback()

	finally:
		# Close the database connection
		cursor.close()
		conn.close()

# Create necessary database tables
#create_db_table__categories()
create_db_table__products()

# scrape all categories from tiki.vn and insert into the database
#insert_to_db__categories()

# scrape all products from tiki.vn and insert into the database
insert_to_db__products()

# Get the list of 10 latest products
#sql = "SELECT * FROM " + tbl_prefix + "products ORDER BY insert_date DESC LIMIT 10"

#list_products = select_from_db(sql)
#print(list_products)
### Data restoration
Use the file backup/db/homework_week_2.sql to restore the needed data to Portgres database.

# Project Description
In this project, we create a scraper program that visits the e-commerce website TIKI at https://tiki.vn, reads its categories & products content, extracts the information and insert into our Portgres database.

The main function of our scapper is to collect the product information of products being sold on Tiki, including products on every pages of all categories. The collected information will be saved as arrays, which will in turn be added into a Pandas dataframe.

The product information includes:

* Product ID
* Seller ID
* Category ID
* Product title
* URL of the product image
* Price (Regular and Final)
* Tiki Now service
* Product URL
* Rating
* Number of reviews

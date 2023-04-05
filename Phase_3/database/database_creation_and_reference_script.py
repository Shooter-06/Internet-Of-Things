import pymysql
import pymysql.cursors

#after installing mariadb and setting password to 'root' (we can change this if you want):
#maybe install pymysql as well
# to navigate the db directly from terminal: run in terminal: mariadb -u root -p and enter password (root)

#create the database: just write: CREATE DATABASE IOT;



# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='root',
                             database='IOT',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


# INSERT YOUR CARD INFO
with connection.cursor() as cursor:

   # sql = "INSERT INTO `USER` (`id`, `temp_threshold`, `light_threshold`, `picture`) VALUES ('f37d2813', '23.5', '500.0', 'assets/dory.jpg')"
   sql = "INSERT INTO `USER` (`id`, `temp_threshold`, `light_threshold`, `picture`) VALUES ('33a168d', '17', '500.0', 'assets/stitch.jpg')"
    
   cursor.execute(sql)
   connection.commit()
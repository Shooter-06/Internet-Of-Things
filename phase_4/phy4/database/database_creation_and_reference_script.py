import sqlite3


conn= sqlite3.connect("Readings.db")

# Retrieve the latest temperature and humidity readings from the readings table

cursor = conn.cursor()
cursor.execute('SELECT user_id,name, temp_threshold,humidity_threshold, light_intensity FROM readings ORDER BY id DESC LIMIT 1')
# cursor.execute("INSERT INTO `Reading` (`id`, `temp_threshold`, `light_threshold`) VALUES ('33a168d', '25', '400.0')")
row = cursor.fetchone()
name, temp_threshold, humidity_threshold = row

# Print the readings
print('Latest name:', name)
print('Latest humidity:', temp_threshold)
print('Latest temperature:', humidity_threshold)

# Close the database connection
conn.close()

import sqlite3
import asyncio

db_name = 'archbot'

class Database:
	def __init__(self, dbname):
		self.connection = sqlite3.connect(dbname + ".db") #create connection/database
		self.cursor = self.connection.cursor()

	async def query(self, query, params):
		try:
			return self.cursor.execute(query, params)
		except Exception as e:
			print(e)

	async def exec(self, query, params):
		try:
			self.cursor.execute(query, params)
			self.connection.commit()
		except Exception as e:
			print(e)

	def setup(self):
		#Create `tags` table if it doesn't exist
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS tags (
							user integer,
							tag text,
							content text,
							server integer,
							global integer
							)""")

		#Create blacklisted user table if it doesn't exit
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS blacklist (
							user integer,
							server integer
							)""")

		#Create blacklisted user table if it doesn't exit
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS user_commands (
							user integer,
							server integer,
							cmd text
							)""")

		#Create blacklisted user table if it doesn't exit
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS server_commands (
							server integer,
							cmd text
							)""")

		#Create prefix table if it doesnt exist
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS prefix (
								prefix text,
								server integer
								)""")

		self.connection.commit()
	
	def __del__(self):
		self.connection.close()
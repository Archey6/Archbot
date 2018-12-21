import sqlite3
import asyncio

db_name = 'archbot'

class Database:
	def __init__(self, dbname):
		self.connection = sqlite3.connect(dbname + ".db") #create connection/database
		self.connection.row_factory = sqlite3.Row
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
		"""Creates all tables if they do not exist"""
		self.cursor.executescript("""
			CREATE TABLE IF NOT EXISTS global_tags (user integer, tag text, content text, server integer);
			CREATE TABLE IF NOT EXISTS server_tags (user integer, tag text, content text, server integer);
			CREATE TABLE IF NOT EXISTS blacklist (user integer, server integer);
			CREATE TABLE IF NOT EXISTS user_commands (user integer, server integer, cmd text);
			CREATE TABLE IF NOT EXISTS server_commands (server integer, cmd text);
			CREATE TABLE IF NOT EXISTS prefix (prefix text, server integer);
			""")

		self.connection.commit()
	
	def __del__(self):
		self.connection.close()
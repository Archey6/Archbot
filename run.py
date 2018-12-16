import asyncio
import sqlite3

from archbot import ArchBot
from utils.database import *

def start_db():
	#dbname = 'archbot'
	db = Database(db_name)

	try:
		print('Connecting to database...')
		db.setup()
		print('Connected to: %s' % db_name)
	except sqlite3.Error as e:
		print('Database error: %s' % e)

def run():
	bot = ArchBot()
	bot.run()

if __name__ == '__main__':
	start_db()
	run()
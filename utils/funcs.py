import asyncio
import sqlite3
import discord

from utils.database import *
from discord.ext import commands

class Funcs:

	def __init__(self):
		self.db = Database(db_name)
		 

	async def get_prefix(self, guild):
		result = await self.db.query("SELECT prefix FROM prefix WHERE server=?", (guild.id,))
		result = result.fetchall()

		if not result:
			return ',' #returns default prefix
		else:
			return result[0][0]

	async def blacklist(self, message, guild):
		result = await self.db.query("SELECT * FROM blacklist WHERE user=? AND server=?", (message.author.id, guild.id))
		return result.fetchall()

	async def command(self, ctx, cmd, user):
		"""checks if command is disabled server wide, if not checks for user for disabled commands"""
		result = await self.db.query("SELECT * FROM server_commands WHERE server=? AND cmd=?", (ctx.guild.id, cmd))
		result = result.fetchall()
		
		if not result:
			result = await self.db.query("SELECT * FROM user_commands WHERE user=? AND server=? AND cmd=?", (user, ctx.guild.id, cmd))
			return not result.fetchall()
		return not result
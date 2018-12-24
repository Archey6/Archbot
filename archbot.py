import discord
import asyncio
import os
import sqlite3
import sys, traceback


from discord.ext import commands
from utils.database import *
from utils.funcs import Funcs

extensions = [
'cogs.moderation', 
'cogs.tags', 
'cogs.botcontrol', 
'cogs.fun'
]

async def call_prefix(bot, msg):
	"""function to call prefix for server specific prefixes
		cant directly call func.get_prefxi in __init__ as __init__
		is not async"""
	return await Funcs().get_prefix(msg.guild)

class ArchBot(commands.Bot):
	"""Tags bot"""
	
	def __init__(self):
		self.token = os.getenv('bot_token')
		self.funcs = Funcs()

		super().__init__(command_prefix=call_prefix, description="ArchBot")

		for ext in extensions:
			try:
				self.load_extension(ext)
				print(f'Added cog: {ext}')
			except Exception as e:
				print(f'Failed to load extension: {ext}.', file=sys.stderr)
				traceback.print_exc()


	async def on_ready(self):
		print('Logged in as: {0} -- {0.id}'.format(self.user))
		print('------')

	async def on_message(self, message):
		#Do nothing if PM
		if message.guild is None:
			return

		#checks for blacklisted users
		if await self.funcs.blacklist(message, message.guild):
			return

		#check if author is the bot
		if message.author.id == self.user.id:
			return

		await self.process_commands(message)
		
	async def on_command_error(self, ctx, exc):
		msg = None
		color = discord.Color.default()
		if isinstance(exc, commands.UserInputError):
			pf = await self.funcs.get_prefix(ctx.message.guild)
			msg = f'Usage: `{pf}{ctx.command.signature}`'
		elif isinstance(exc, commands.CheckFailure):
			msg = 'You do not have permission to run this command or it\'s disabled!'
			color = discord.Color.red()
		elif isinstance(exc, commands.BadArgument):
			msg = 'Incorrect parameter passed!'
			color = discord.Color.red()
		elif isinstance(exc, commands.CommandInvokeError):
			msg = str(exc)
			color = discord.Color.orange()
		elif isinstance(exc, commands.CommandNotFound):
			return #Don't care about this error, way too spammy
		elif isinstance(exc, commands.CommandError):
			msg = str(exc)
			color = discord.Color.orange()


		if msg is not None:
			await ctx.send(embed=discord.Embed(description=msg, color=color))

	def run(self):
		try:
			super().run(self.token)
		except Exception as e:
			print(e)


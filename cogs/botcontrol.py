import discord
import asyncio
import sys, traceback

from discord.ext import commands

class BotControl():
	def __init__(self, bot):
		self.bot = bot

	def __local_check(self, ctx):
		return self.bot.is_owner(ctx.author)

	@commands.command(name='reload', aliases=['rl'], hidden=True)
	async def reload_cog(self, ctx, ext):
		"""Reloads a cog"""
		try:
			ext = 'cogs.' + ext
			self.bot.unload_extension(ext)
			self.bot.load_extension(ext)
			print(f'Reloaded cog: {ext}')
		except Exception as e:
			print(f'Failed to reload extension: {ext}.', file=sys.stderr)
			traceback.print_exc()

def setup(bot):
	bot.add_cog(BotControl(bot))
import discord
import asyncio
import aiohttp, io
import sys, traceback, os
import cairosvg
import emoji

from discord.ext import commands

class Fun():
	def __init__(self, bot):
		self.bot = bot
		self.query_error = commands.CommandError('Query failed. Try again later!')
		self.emoji_path = os.path.abspath("./files/emoji/")

	async def convert_emoji(self, ctx, em):
		return await commands.PartialEmojiConverter().convert(ctx, em)

	async def custom_emoji(self, emoji: discord.Emoji):
			try:
				async with aiohttp.ClientSession() as session:
					async with session.get(emoji.url) as resp:
						if resp.status != 200:
							raise self.query_error
						data = io.BytesIO(await resp.read())
						return discord.File(data, 'custom_emoji.png')
			except asyncio.TimeoutError:
				raise self.query_error

	async def png_svg(self, path, size):
		with open(path, 'rb') as f:
			path = f.read()
		s = bytes(str(size), encoding="utf-8")
		b = path.replace(b"<svg ", b"<svg width=\"" + s + b"px\" height=\"" + s + b"px\" ")
		path = io.BytesIO(cairosvg.svg2png(b))
		return path
		
	@commands.command(name='avatar', aliases=['ava'])
	async def avatar(self, ctx, member: discord.Member=None):
		"""Show a users avatar"""
		if member is None:
			member = ctx.author

		async with ctx.channel.typing():
			try:
				async with aiohttp.ClientSession() as session:
					async with session.get(member.avatar_url_as(format='png')) as resp:
						if resp.status != 200:
							raise self.query_error
						data = io.BytesIO(await resp.read())
						await ctx.send(file=discord.File(data, member.avatar+'.png'))
			except asyncio.TimeoutError:
				raise self.query_error

	@commands.command(name='emoji', aliases=['e'])
	async def emoji(self, ctx, em):
		"""Posts a big version of an emoji"""

		async with ctx.channel.typing():
			if em in emoji.UNICODE_EMOJI:
				if len(em) == 2: #for flag emojis
					emj = ''
					for i in em:
						emj += f'{ord(i):x}'
					mp = len(emj)//2
					e = emj[:mp] + '-' + emj[mp:]
				else:
					e = f'{ord(em):x}'

				e = e+'.svg'

				png = await self.png_svg(self.emoji_path+'/'+e, 1024)

				await ctx.send(file=discord.File(png, 'emote.png'))
			else:
				em = await self.convert_emoji(ctx, em)
				await ctx.send(file=await self.custom_emoji(em))
				return
			

def setup(bot):
	bot.add_cog(Fun(bot))
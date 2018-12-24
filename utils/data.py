import discord

from discord.ext import commands

class TagName(commands.Converter):
	_length_limit = 32
	_reserved = ['tag', 'add', 'create', 'edit', 'delete', 'info', 'list', 'top', 'raw', 'get', 'set', 'exec', 'search']

	def make_lower(self, s: str): return s.lower()

	async def convert(self, ctx, tag):
		if len(tag) > self._length_limit:
			raise commands.CommandError(f'Tag name limit is {self._length_limit} characters.')
		if tag in self._reserved:
			raise commands.CommandError('Sorry, that tag name is reserved!')
		return self.make_lower(tag)


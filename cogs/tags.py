import discord
import asyncio

from discord.ext import commands
from utils.database import *
from utils.checks import *
from utils.funcs import Funcs
from utils.data import TagName

class Tags:
	def __init__(self, bot):
		self.bot = bot
		self.db = Database(db_name)
		self.funcs = Funcs()
		self.GLOBAL_TRUE = 1
		self.GLOBAL_FALSE = 0

	async def get_tag(self, tag, glb: int, server=None):
		if server is None:
			sql_q = "SELECT * FROM tags WHERE tag=? AND global=?"
			result = await self.db.query(sql_q, (tag, glb))
		else:
			sql_q = "SELECT * FROM tags WHERE tag=? AND server=? AND global=?"
			result = await self.db.query(sql_q, (tag, server, glb))

		return result.fetchall()

	"""This is an old function leaving in for docs
	async def tag_exists(self, tag, glb: int, server=None):
		if await self.get_tag(tag, glb, server):
			return True
		else:
			return False"""


	async def tag_exists(self, ctx, tag, global_with_server: bool):
		is_server = await self.get_tag(tag, self.GLOBAL_FALSE, ctx.guild.id)

		if global_with_server:
			is_global = await self.get_tag(tag, self.GLOBAL_TRUE, ctx.guild.id)
		else:
			is_global = await self.get_tag(tag, self.GLOBAL_TRUE)

		if not is_global and not is_server:
				await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))
				return False
		return True


	async def tag_add(self, user, tag, content, server, glb: int):
		sql_in = "INSERT INTO tags VALUES (?, ?, ?, ?, ?)"
		await self.db.exec(sql_in, (user, tag, content, server, glb))

	async def get_owner(self, ctx, tag):
		is_global = await self.get_tag(tag, self.GLOBAL_TRUE)
		is_server = await self.get_tag(tag, self.GLOBAL_FALSE, ctx.guild.id)
		if is_server:
			return is_server[0][0] == ctx.author.id
		elif is_global:
			return is_global[0][0] == ctx.author.id
		return False

	async def list_tags(self, ctx, user_input, search_type: str):
		if search_type == 'tag':
			sql_q = "SELECT user, tag FROM tags WHERE server=? AND tag LIKE ?"
		elif search_type == 'content':
			sql_q = "SELECT user, tag FROM tags WHERE server=? AND content LIKE ?"

		lst = ''

		result = await self.db.query(sql_q, (ctx.guild.id, '%'+user_input+'%'))
		result = result.fetchall()

		for i in result:
			usr = str(ctx.guild.get_member(i[0]))
			lst = lst + '**' + i[1] + '**' + ' `(' + usr + ')`\n'

		await ctx.send(embed=discord.Embed(title=str(ctx.guild.name) + '\'s Tags matching: '+user_input, description=lst))

	@commands.group(name='tag', aliases=['t'], invoke_without_command=True)
	async def tag(self, ctx, tag: TagName):
		"""If no server tag exists, display global tag"""
		tag = await TagName().convert(ctx, tag)
		is_global = await self.get_tag(tag, self.GLOBAL_TRUE)
		is_server = await self.get_tag(tag, self.GLOBAL_FALSE, ctx.guild.id)

		if not is_server and not is_global:
			#if no server OR global tag exists
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))
		elif not is_server:
			t = await self.get_tag(tag, self.GLOBAL_TRUE)
			t = t[0][2] #0 = index of first tuple in list; 2 = 'content' in row
			await ctx.send(t)
		elif is_server:
			t = await self.get_tag(tag, self.GLOBAL_FALSE, ctx.guild.id)
			t = t[0][2]
			await ctx.send(t)

	@tag.command(name='add', aliases=['create'])
	async def add_tag(self, ctx, tag: TagName, content: commands.clean_content):
		"""If no tag exists add global tag; If global tag exists add server tag
			0 = false 1 = true"""
		tag = await TagName().convert(ctx, tag)
		is_global = await self.get_tag(tag, self.GLOBAL_TRUE)
		is_server = await self.get_tag(tag, self.GLOBAL_FALSE, ctx.guild.id)

		if not is_global and not is_server:
			#No global or server tag so we add a global tag
			await self.tag_add(ctx.author.id, tag, content, ctx.guild.id, self.GLOBAL_TRUE)
			await ctx.send(":white_check_mark: Added global tag `{}`".format(tag))
		elif is_global and not is_server:
			#Global tag exists but server tag does not so we add server tag
			await self.tag_add(ctx.author.id, tag, content, ctx.guild.id, self.GLOBAL_FALSE)
			await ctx.send(":white_check_mark: Added server tag `{}`".format(tag))
		else:
			await ctx.send(":no_entry: Tag `{}` already exists!".format(tag))

	@tag.command(name='remove', aliases=['del', 'delete'])
	async def del_tag(self, ctx, tag: TagName):
		"""Delete a tag"""
		tag = await TagName().convert(ctx, tag)
		can_edit = await self.get_owner(ctx, tag)
		sql_del = "DELETE FROM tags WHERE user=? AND tag=? AND server=?"

		if not await self.tag_exists(ctx, tag, True):
			return

		if can_edit:
			await self.db.exec(sql_del, (ctx.author.id, tag, ctx.guild.id))
			await ctx.send(":white_check_mark: Tag `{}` has been deleted.".format(tag))
		else:
			raise commands.CommandError("You don\'t own tag `{}`".format(tag))

	@tag.command(name='edit', aliases=['change'])
	async def edit_tag(self, ctx, tag: TagName, content: commands.clean_content):
		"""Edits the content of a tag"""
		tag = await TagName().convert(ctx, tag)
		can_edit = await self.get_owner(ctx, tag)

		if not await self.tag_exists(ctx, tag, True):
			return

		sql_e = "UPDATE tags SET content=? WHERE user=? AND tag=? AND server=?"
		if can_edit:
			await self.db.exec(sql_e, (content, ctx.author.id, tag, ctx.guild.id))
			await ctx.send(":white_check_mark: Edited tag `{}`".format(tag))
		else:
			raise commands.CommandError("You don\'t own tag `{}`".format(tag))			

	@tag.command(name='forceremove', aliases=['fm', 'forcedelete'])
	@is_admin()
	async def forceremove(self, ctx, tag: TagName):
		"""Force removes a tag"""
		tag = await TagName().convert(ctx, tag)

		if not await self.tag_exists(ctx, tag, True):
			return

		sql_del = "DELETE FROM tags WHERE tag=? AND server=?"
		sql_q = "SELECT user FROM tags WHERE tag=? AND server=?"

		#Gets user id of owner of tag 
		usr = await self.db.query(sql_q, (tag, ctx.guild.id))
		usr = usr.fetchall()
		usr = ctx.guild.get_member(usr[0][0])

		await self.db.exec(sql_del, (tag, ctx.guild.id))
		await ctx.send(":cop::skin-tone-1: Force removed `{}\'s` tag `{}`".format(usr, tag))

	@tag.command(name='owner', aliases=['creator'])
	async def owner(self, ctx, tag: TagName):
		tag = await TagName().convert(ctx, tag)

		if not await self.tag_exists(ctx, tag, False):
			return

		sql_q = "SELECT user FROM tags WHERE tag=? AND server=?"
		sql_g = "SELECT user FROM tags WHERE tag=? AND global=?"

		global_result = await self.db.query(sql_g, (tag, self.GLOBAL_TRUE))
		global_result = global_result.fetchall()

		result = await self.db.query(sql_q, (tag, ctx.guild.id))
		result = result.fetchall()

		if global_result and result:
			user = ctx.guild.get_member(result[0][0])
		elif global_result:
			user = ctx.guild.get_member(global_result[0][0])
		else:
			user = ctx.guild.get_member(result[0][0])

		await ctx.send("`{}` owns tag `{}`".format(user, tag))

	@tag.command(name='list')
	async def list(self, ctx, member: discord.Member=None):
		sql_q = "SELECT tag FROM tags WHERE user=? AND server=?"
		lst = ''
		if member is None: 
			mem_id = ctx.author.id 
		else: 
			mem_id = member.id

		result = await self.db.query(sql_q, (mem_id, ctx.guild.id))
		result = result.fetchall()
		for i in result:
			lst = lst + i[0] + '\n'
			
		await ctx.send(embed=discord.Embed(title=str(ctx.author) + '\'s Tags', description=lst))

	@tag.group(name='search', aliases=['find'], invoke_without_command=True)
	async def search(self, ctx, tag: TagName):
		await self.list_tags(ctx, tag, 'tag')

	@search.command(name='content')
	async def content(self, ctx, content: commands.clean_content):
		await self.list_tags(ctx, content, 'content')
		

def setup(bot):
	bot.add_cog(Tags(bot))
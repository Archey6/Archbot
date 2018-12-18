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

		self.reactions = ['⏮', '⏪', '⏩', '⏭', '🆗']

	async def get_tag(self, tag, glb: int, server=None):
		if server is None:
			sql_q = "SELECT * FROM tags WHERE tag=? AND global=?"
			result = await self.db.query(sql_q, (tag, glb))
		else:
			sql_q = "SELECT * FROM tags WHERE tag=? AND server=? AND global=?"
			result = await self.db.query(sql_q, (tag, server, glb))

		return result.fetchall()

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
			sql_q = "SELECT * FROM tags WHERE server=? AND tag LIKE ?"
		elif search_type == 'content':
			sql_q = "SELECT * FROM tags WHERE server=? AND content LIKE ?"

		result = await self.db.query(sql_q, (ctx.guild.id, '%'+user_input+'%'))
		result = result.fetchall()

		if not result:
			await ctx.send(":no_entry: No tags matching `{}` exist!".format(user_input))
			return
		else:
			return result

	async def create_embed(self, ctx, result, *, member=None):
		embed = discord.Embed()

		if member is not None:
			if not result:
				await ctx.send(":no_entry: `{}` has no tags!".format(member))
				return 
			embed.set_author(name=member.name+'\'s Tags', icon_url=member.avatar_url_as(format='jpeg', size=32))

		list_len = 21 #Lists will cap at 20, needs to be 21 for mod division
		item = 0
		page = 0
		total = 0
		tag_list = [None] * ((len(result) // list_len) + 1) #Initializes a list with how many pages were need, as list indices
		lst = []
		for i in result:
			item += 1 
			total += 1 

			#checks if tag is a server tag	
			if i['global'] == 0 and i['server'] == ctx.guild.id:
				server_tag = '  `(Server Tag)`\n'
			else:
				server_tag = '\n'

			#adds each item to a list to be added to an index later	
			lst.append('{}. "{}"{}'.format(str(item), i['tag'], server_tag)) 

			if item % list_len == 0: #If current list/page is full(20 items) create new page and store it in next index
				page += 1
				tag_str = ''
				lst = []

			#Adds list of 20 or less results to a "page"(index)
			tag_str = ' '.join(lst)
			tag_list[page] = tag_str

			#Default page, used to increment later
			display_page = 0

		embed.add_field(name='Tag List', value=tag_list[display_page])
		msg = await ctx.send(embed=embed)
		for e in self.reactions:
			await msg.add_reaction(e)

		def check(reaction, user):
			return user.id == ctx.author.id and str(reaction.emoji) in self.reactions

		while True:
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)

				if reaction.emoji == '🆗':
					break
					return
				elif reaction.emoji == '⏮':
					display_page = 0
					embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					await msg.edit(embed=embed)
				elif reaction.emoji == '⏪':
					if display_page > 0:
						display_page -= 1
						embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					await msg.edit(embed=embed)
				elif reaction.emoji == '⏩':
					if display_page != len(tag_list) - 1:
						display_page += 1
					embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					await msg.edit(embed=embed)
				elif reaction.emoji == '⏭':
					display_page = len(tag_list) - 1
					embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					await msg.edit(embed=embed)
			except asyncio.TimeoutError:
				break
				return

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
		"""Display owner of a tag"""
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
		"""List a users tags"""
		sql_q = "SELECT tag, server, global FROM tags WHERE user=?"
		if member is None: 
			mem = ctx.author 
		else: 
			mem = member

		result = await self.db.query(sql_q, (mem.id,))
		result = result.fetchall()

		await self.create_embed(ctx, result, member=mem)
		

	@tag.group(name='search', aliases=['find'], invoke_without_command=True)
	async def search(self, ctx, tag: TagName):
		"""List a tag with similar name"""
		result = await self.list_tags(ctx, tag, 'tag')

		if result:
			await self.create_embed(ctx, result)

	@search.command(name='content')
	async def content(self, ctx, content: commands.clean_content):
		"""List a tag with similar content"""
		result = await self.list_tags(ctx, content, 'content')

		if result:
			await self.create_embed(ctx, result)
		

def setup(bot):
	bot.add_cog(Tags(bot))
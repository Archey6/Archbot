import discord
import asyncio
import os, io
import magic

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

		self.reactions = ['⏮', '⏪', '⏩', '⏭', '🆗']

	async def get_global_tag(self, tag):
		sql_q = "SELECT * FROM global_tags WHERE tag=?"
		result = await self.db.query(sql_q, (tag,)) 
		return result.fetchall()

	async def get_global_server_tag(self, tag, server):
		sql_q = "SELECT * FROM global_tags WHERE tag=? AND server=?"
		result = await self.db.query(sql_q, (tag, server))
		return result.fetchall()

	async def get_server_tag(self, tag, server):
		sql_q = "SELECT * FROM server_tags WHERE tag=? AND server=?"
		result = await self.db.query(sql_q, (tag, server))
		return result.fetchall()

	async def tag_table(self, tag, guild):
		if await self.get_server_tag(tag, guild):
			return 'server'
		elif await self.get_global_server_tag(tag, guild):
			return 'global'
		elif await self.get_global_tag(tag):
			return 'global'
		else:
			return False	

	async def get_owner(self, author_id, tag, server):
		is_global = await self.get_global_tag(tag)
		is_server = await self.get_server_tag(tag, server)
		if is_server:
			return is_server[0][0] == author_id
		elif is_global:
			return is_global[0][0] == author_id
		return False

	async def list_tags(self, ctx, user_input, search_type: str):
		sql_q = """
				SELECT * FROM server_tags WHERE {} LIKE ?
				UNION
				SELECT * FROM global_tags WHERE {} LIKE ?
				""".format(search_type, search_type)

		result = await self.db.query(sql_q, ('%'+user_input+'%', '%'+user_input+'%'))
		result = result.fetchall()

		if not result:
			await ctx.send(":no_entry: No tags matching `{}` exist!".format(user_input))
			return
		else:
			return result

	async def create_embed(self, ctx, result, *, member=None):
		embed = discord.Embed(color=discord.Color.blue())

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
		old_tag = None
		for i in result:
			item += 1 
			total += 1 
			
			if i['tag'] == old_tag:
				server_tag = '  `(Server Tag)`\n'
			else:
			 	server_tag = '\n'
			old_tag = i['tag']

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
		embed.set_footer(text=str("{}/{} Tags").format(tag_list[display_page].count('\n'),total))
		msg = await ctx.send(embed=embed)
		for e in self.reactions:
			await msg.add_reaction(e)

		def check(reaction, user):
			return user.id == ctx.author.id and str(reaction.emoji) in self.reactions and reaction.message.id == msg.id

		while True:
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)

				#await msg.remove_reaction(reaction.emoji, user)
				
				if reaction.emoji == '🆗':
					await msg.delete()
					break
					return
				elif reaction.emoji == '⏮':
					display_page = 0
					embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					embed.set_footer(text=str("{}/{} Tags").format(tag_list[display_page].count('\n'), total))
					await msg.edit(embed=embed)
				elif reaction.emoji == '⏪':
					if display_page > 0:
						display_page -= 1
						embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
						embed.set_footer(text=str("{}/{} Tags").format(tag_list[display_page].count('\n'), total))
					await msg.edit(embed=embed)
				elif reaction.emoji == '⏩':
					if display_page != len(tag_list) - 1:
						display_page += 1
					embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					embed.set_footer(text=str("{}/{} Tags").format(tag_list[display_page].count('\n')+(display_page*20)+1, total))
					await msg.edit(embed=embed)
				elif reaction.emoji == '⏭':
					display_page = len(tag_list) - 1
					embed.set_field_at(0, name='Tag List', value=tag_list[display_page])
					embed.set_footer(text=str("{}/{} Tags").format(tag_list[display_page].count('\n')+(display_page*20)+1, total))
					await msg.edit(embed=embed)
			except asyncio.TimeoutError:
				break
				return

	async def get_attach(self, attach):
		for i in attach:
			file = i.filename
			size = i.size

			if size > 8000000:
				raise commands.CommandError('File is over 8MB! Bots cannot upload over 8MB!')

			await i.save(file)
			with open(file, 'rb') as img:
				content = sqlite3.Binary(img.read())
				os.remove(file)
				return content
			break

	@commands.group(name='tag', aliases=['t'], invoke_without_command=True)
	async def tag(self, ctx, tag: TagName):
		"""If no server tag exists, display global tag"""
		#tag = await TagName().convert(ctx, tag)
		
		if await self.get_server_tag(tag, ctx.guild.id):
			table_name = 'server'
		elif await self.get_global_tag(tag):
			table_name = 'global'
		else:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))
			return

		sql_q = "SELECT content FROM {}_tags WHERE tag=?".format(table_name)
		result = await self.db.query(sql_q, (tag,))
		result = result.fetchall()[0]
		
		async with ctx.channel.typing():
			if isinstance(result['content'], bytes):
				file = result['content']

				with open("tmp", 'wb') as out:
					out.write(file)

				ext = magic.from_file('tmp', mime=True).split('/')[1]
				os.remove('tmp')
				file = discord.File(file, "tag."+ext)
				await ctx.send(file=file)
			else:
				await ctx.send(result['content'])

	@tag.command(name='add', aliases=['create'])
	async def add_tag(self, ctx, tag: TagName, content: commands.clean_content=None):
		"""adds a tag"""
		#tag = await TagName().convert(ctx, tag)

		if content is None and ctx.message.attachments:
			async with ctx.channel.typing():
				content = await self.get_attach(ctx.message.attachments)
		elif content is None:
			raise commands.UserInputError()

		#Tag already exists in server, return
		if await self.get_global_server_tag(tag, ctx.guild.id) or await self.get_server_tag(tag, ctx.guild.id):
			await ctx.send(":no_entry: Tag `{}` already exists!".format(tag))
			return

		if not await self.get_global_tag(tag) and not await self.get_server_tag(tag, ctx.guild.id):
			#no global or server tag; add global tag
			table_name = 'global'
		elif await self.get_global_tag(tag) and not await self.get_server_tag(tag, ctx.guild.id): 
			#global tag exists server tag doesnt; add server tag
			table_name = 'server'


		sql_in = "INSERT INTO {}_tags VALUES (?, ?, ?, ?)".format(table_name)
		await self.db.exec(sql_in, (ctx.author.id, tag, content, ctx.guild.id))
		await ctx.send(":white_check_mark: Added {} tag `{}`".format(table_name, tag))

	@tag.command(name='remove', aliases=['del', 'delete'])
	async def del_tag(self, ctx, tag: TagName):
		"""Delete a tag"""
		#tag = await TagName().convert(ctx, tag)
		can_edit = await self.get_owner(ctx.author.id, tag, ctx.guild.id)

		table_name = await self.tag_table(tag, ctx.guild.id)

		if not table_name:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))	
			return	

		sql_del = "DELETE FROM {}_tags WHERE user=? AND tag=? AND server=?".format(table_name) #Delete from table where tag exists
		if can_edit:
			await self.db.exec(sql_del, (ctx.author.id, tag, ctx.guild.id))
			await ctx.send(":white_check_mark: Tag `{}` has been deleted.".format(tag))
		else:
			await ctx.send(":no_entry: You don\'t own tag `{}`!".format(tag))

	@tag.command(name='edit', aliases=['change'])
	async def edit_tag(self, ctx, tag: TagName, content: commands.clean_content=None):
		"""Edits the content of a tag"""
		#tag = await TagName().convert(ctx, tag)
		can_edit = await self.get_owner(ctx.author.id, tag, ctx.guild.id)

		if content is None and ctx.message.attachments:
			content = await self.get_attach(ctx.message.attachments)
		elif content is None:
			raise commands.UserInputError()

		table_name = await self.tag_table(tag, ctx.guild.id)

		if not table_name:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))	
			return	

		sql_e = "UPDATE {}_tags SET content=? WHERE user=? AND tag=? AND server=?".format(table_name)
		if can_edit:
			await self.db.exec(sql_e, (content, ctx.author.id, tag, ctx.guild.id))
			await ctx.send(":white_check_mark: Edited tag `{}`".format(tag))
		else:
			await ctx.send(":no_entry: You don\'t own tag `{}`!".format(tag))

	@tag.command(name='forceremove', aliases=['fm', 'forcedelete'])
	@is_admin()
	async def forceremove(self, ctx, tag: TagName):
		"""Force removes a tag"""
		#tag = await TagName().convert(ctx, tag)

		table_name = await self.tag_table(tag, ctx.guild.id)

		if not table_name:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))	
			return	

		if table_name == 'global' and not await self.get_global_server_tag(tag, ctx.guild.id):
			await ctx.send(":no_entry: Only server tags or global tags created in this server can be removed!")
			return

		sql_del = "DELETE FROM {}_tags WHERE tag=? AND server=?".format(table_name)
		sql_q = "SELECT user FROM {}_tags WHERE tag=? AND server=?".format(table_name)

		#Gets user id of owner of tag 
		usr = await self.db.query(sql_q, (tag, ctx.guild.id))
		usr = usr.fetchall()
		usr = ctx.guild.get_member(usr[0][0])

		await self.db.exec(sql_del, (tag, ctx.guild.id))
		await ctx.send(":cop::skin-tone-1: Force removed `{}\'s` tag `{}`".format(usr, tag))

	@tag.command(name='owner', aliases=['creator'])
	async def owner(self, ctx, tag: TagName):
		"""Display owner of a tag"""
		#tag = await TagName().convert(ctx, tag)

		table_name = await self.tag_table(tag, ctx.guild.id)

		if not table_name:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))
			return	

		sql_q = "SELECT user FROM {}_tags WHERE tag=? AND server=?".format(table_name)
		result = await self.db.query(sql_q, (tag, ctx.guild.id))
		result = result.fetchall()

		user = ctx.guild.get_member(result[0]['user'])

		await ctx.send("`{}` owns tag `{}`".format(user, tag))

	@tag.command(name='list')
	async def list(self, ctx, member: discord.Member=None):
		"""List a users tags"""
		sql_q = """
				SELECT * FROM server_tags WHERE user=?
				UNION
				SELECT * FROM global_tags WHERE user=?
				"""
		if member is None: 
			mem = ctx.author 
		else: 
			mem = member

		result = await self.db.query(sql_q, (mem.id, mem.id))
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

	@tag.command(name='gift', aliases=['give'])
	async def gift(self, ctx, tag: TagName, recipient: discord.Member):
		tag = await TagName().convert(ctx, tag)

		table_name = await self.tag_table(tag, ctx.guild.id)
		if not table_name:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))
			return

		if not await self.get_owner(ctx.author.id, tag, ctx.guild.id):
			await ctx.send(":no_entry: You don't own `{}`".format(tag))
			return

		sql_u = "UPDATE {}_tags SET user=? WHERE user=? AND tag=? AND server=?".format(table_name)
		await ctx.send("{}, {} wants to gift you tag `{}`. Type **yes** to accept.".format(recipient.mention, ctx.author.mention, tag))

		def check(msg):
			return msg.content == "yes" and msg.author.id == recipient.id

		while True:
			try:
				msg = await self.bot.wait_for('message', timeout=30, check=check)

				await self.db.exec(sql_u, (recipient.id, ctx.author.id, tag, ctx.guild.id))
				await ctx.send("`{}` now owns tag `{}`".format(recipient, tag))
				break
			except asyncio.TimeoutError:
				break

	@tag.command(name='source', aliases=['raw'])
	async def source(self, ctx, tag: TagName):
		#tag = await TagName().convert(ctx, tag)

		table_name = await self.tag_table(tag, ctx.guild.id)

		if not table_name:
			await ctx.send(":no_entry: Tag `{}` does not exist!".format(tag))	
			return	

		if table_name == 'global':
			sql_q = "SELECT content FROM {}_tags WHERE tag=?".format(table_name)
			result = await self.db.query(sql_q, (tag,))
		else:
			sql_q = "SELECT content FROM {}_tags WHERE tag=? AND server=?".format(table_name)
			result = await self.db.query(sql_q, (tag, ctx.guild.id))

		result = result.fetchall()

		await ctx.send("```{}```".format(result[0]['content']))

	@tag.command(name='global')
	async def global_tag(self, ctx, tag: TagName):
		#tag = await TagName().convert(ctx, tag)

		if not await self.get_global_tag(tag):
			await ctx.send(":no_entry: Global tag `{}` doesn\'t exist!".format(tag))
			return

		sql_q = "SELECT content FROM global_tags WHERE tag=?"

		result = await self.db.query(sql_q, (tag,))
		result = result.fetchall()[0][0]

		await ctx.send(result)


def setup(bot):
	bot.add_cog(Tags(bot))
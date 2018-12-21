import discord
import asyncio

from discord.ext import commands
from utils.database import *
from utils.checks import *
from utils.funcs import Funcs

class Moderation():
	def __init__(self, bot):
		self.bot = bot
		self.db = Database(db_name)
		self.funcs = Funcs()

	async def __global_check(self, ctx):
		#Global check on ALL commands to see for disabled users
		cmd = str(ctx.bot.get_command(ctx.command.name))
		return await self.funcs.command(ctx, cmd, ctx.author.id)

	@commands.command(name='blacklist', aliases=['bl', 'ignore'])
	@is_admin()
	async def blacklist(self, ctx, *, member: discord.Member):
		"""Toggle command, bot will add or remove user from ignore list.
		 params:: user, server"""
		sql_q = "SELECT * FROM blacklist WHERE user=? AND server=?"
		sql_in = "INSERT INTO blacklist VALUES (?, ?)"
		sql_del = "DELETE FROM blacklist WHERE user=? AND server=?"

		query_result = await self.db.query(sql_q, (member.id, ctx.guild.id))
		query_result = query_result.fetchall()

		if not query_result:
			await self.db.exec(sql_in, (member.id, ctx.guild.id)) 
			await ctx.send(":white_check_mark: Okay now ignoring `{}`".format(member))
		else:
			await self.db.exec(sql_del, (member.id, ctx.guild.id))
			await ctx.send(":white_check_mark: Okay now unigorning `{}`".format(member))

	@commands.group(name='prefix', aliases=['pf'], invoke_without_command=True)
	@is_admin()
	async def prefix(self, ctx, prefix):
		"""Changes bot prefix for the server"""
		sql_q = "SELECT * FROM prefix WHERE server=?"
		sql_in = "INSERT INTO prefix VALUES (?, ?)"
		sql_up = "UPDATE prefix SET prefix=? WHERE server=?"

		result = await self.db.query(sql_q, (ctx.guild.id,))
		result = result.fetchall()

		if not result:
			#if no prefix we add one
			await self.db.exec(sql_in, (prefix, ctx.guild.id))
			await ctx.send(":white_check_mark: Bot prefix is now `{}`".format(prefix))
		elif result is not None:
			#if prefix exists we change it
			await self.db.exec(sql_up, (prefix, ctx.guild.id))
			await ctx.send(":white_check_mark: Bot prefix is now `{}`".format(prefix))

	@prefix.command(name='delete', aliases=['remove', 'del'])
	@is_admin()
	async def del_prefix(self, ctx):
		"""Deletes server specific prefix"""
		sql_q = "SELECT * FROM prefix WHERE server=?"
		sql_del = "DELETE FROM prefix WHERE server=?"

		result = await self.db.query(sql_q, (ctx.guild.id,))
		result = result.fetchall()

		if result is not None:
			#if prefix exists delete it
			await self.db.exec(sql_del, (ctx.guild.id,))
			await ctx.send(":white_check_mark: Bot prefix is now `,`")
		else:
			#if no prefix return
			await ctx.send(":no_entry: Server has no custom prefix")

	safe_commands = ['command']
	@commands.group(name='command', aliases=['cmd'], invoke_without_command=True)
	@is_admin()
	async def command(self, ctx, cmd):
		"""Toggle for commands server wide"""
		c = str(self.bot.get_command(cmd))		
		if c in self.safe_commands:
			await ctx.send(":no_entry: Cannot disable command: `{}`!".format(c))
			return

		if c == 'None':
			await ctx.send(":no_entry: `{}` is not a valid command!".format(cmd))
			return

		sql_q = "SELECT * FROM server_commands WHERE server=? AND cmd=?"
		sql_in = "INSERT INTO server_commands VALUES (?, ?)"
		sql_del = "DELETE FROM server_commands WHERE server=? AND cmd=?"

		result = await self.db.query(sql_q, (ctx.guild.id, c))
		result = result.fetchall()

		if not result:
			#Command is on; Toggle off
			await self.db.exec(sql_in, (ctx.guild.id, c))
			await ctx.send(":white_check_mark: Command `{}` is now disabled".format(c))
		elif result is not None:
			#Command is off; Toggle on
			await self.db.exec(sql_del, (ctx.guild.id, c))
			await ctx.send(":white_check_mark: Command `{}` is now enabled".format(c))

	@command.command(name='user')
	@is_admin()
	async def command_user(self, ctx, cmd, *, user: discord.Member):
		"""Toggle command for specific user on specific server"""
		c = str(self.bot.get_command(cmd))

		if c in self.safe_commands:
			await ctx.send(":no_entry: Cannot disable command: `{}`!".format(c))
			return

		if c == 'None':
			await ctx.send(":no_entry: `{}` is not a valid command!".format(cmd))
			return

		if user.permissions_in(ctx.channel).administrator:
			await ctx.send(":no_entry: Cannot disable commands for Admins!")
			return

		sql_q = "SELECT * FROM user_commands WHERE user=? AND server=? AND cmd=?"
		sql_in = "INSERT INTO user_commands VALUES (?, ?, ?)"
		sql_del = "DELETE FROM user_commands WHERE user=? AND server=? AND cmd=?"

		result = await self.db.query(sql_q, (user.id, ctx.guild.id, c))
		result = result.fetchall()
		print(result)
		if not result:
			#Command is on; Toggle off
			await self.db.exec(sql_in, (user.id, ctx.guild.id, c))
			await ctx.send(":white_check_mark: Command `{}` is now disabled for `{}`".format(c, user))
		elif result is not None:
			#Command is off; Toggle on
			await self.db.exec(sql_del, (user.id, ctx.guild.id, c))
			await ctx.send(":white_check_mark: Command `{}` is now enabled for `{}`".format(c, user))

def setup(bot):
	bot.add_cog(Moderation(bot))
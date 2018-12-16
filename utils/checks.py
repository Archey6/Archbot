from discord.ext.commands import check

def is_admin():
	def predicate(ctx):
		return ctx.author.permissions_in(ctx.channel).administrator
	return check(predicate)

def is_mod():
	def predicate(ctx):
		return ctx.author.permissions_in(ctx.channel).manage_roles
	return check(predicate)
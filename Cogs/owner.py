from discord.ext import commands, tasks
import discord, asyncio
import random, time, json

class OwnersCog(commands.Cog, name='Owner'):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(pass_context=True, name='purge', aliases=['purgemessages'], hidden=True)
	@commands.is_owner()
	async def purge(self, ctx, number:int):
		if number > 99 or number < 1:
			await ctx.send("I can only delete messages within a range of 1 - 99", delete_after=4)
		else:
			mgs = []
			channel = ctx.message.channel
			async for x in channel.history(limit = int(number+1)):
				mgs.append(x)
			await channel.delete_messages(mgs)
			await ctx.send('Success!', delete_after=1)

	@commands.command(name='quit', aliases=['shutdown'])
	@commands.is_owner()
	async def quit(self, ctx):
		print(f'{ctx.author.name} quit')
		await ctx.message.delete()
		await ctx.bot.close()
	
def setup(bot):
    bot.add_cog(OwnersCog(bot))

# ----- Bot Imports
import discord, asyncio, os
from discord.ext import commands, tasks
from dotenv import load_dotenv
from itertools import cycle
# ----- Imports
import random, time, os
# ----- Bot Loading Stuff
load_dotenv()
TOKEN = os.getenv('SEKAIDLE_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='>', intents=intents, help_command=None,
                   owner_ids={226854455478452236, 136906809699991552} )
initial_extensions = ['Cogs.sekaidle', 'Cogs.owner']
for extension in initial_extensions:
  bot.load_extension(extension)
# ----- Assigning Variables
startup_time = time.localtime()
tyler = {'id':226854455478452236}

@bot.event
async def on_ready():
  global activities
  global cogs
  global all_cmds
  '''
  ----- More Variables!
   1:Playing 2:Listening 3:Watching 4:Custom (doesn't work?) 5:Competing in
   message = discord.Streaming(name='yeet', url='yeet.org')
  '''
  members_list = [guilds.members for guilds in bot.guilds]
  activities = cycle([
    discord.Activity(name=f'{sum(map(len, members_list))} members', type=3),
    discord.Activity(name=f'{bot.command_prefix}help for help!', type=2)])
  cogs = {'None':dict()}
  for cog_name in bot.cogs:
    cogs[cog_name] = dict()
  for command in bot.commands:
    cogs[str(command.cog_name)][command.name] = command.help
  all_cmds = [command for command in bot.commands]
  '''
  ----- Background Tasks
  '''
  # change_presence.start()
  print('Bot is ready!')

@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send(f'Please pass in all required arguments. \nUse {bot.command_prefix}help {ctx.command} for help on the usage.')
  elif isinstance(error, commands.CommandNotFound):
    await ctx.send(f'{error}.\nUse {bot.command_prefix}help to look for valid commands')
  elif isinstance(error, (commands.MissingPermissions, commands.NotOwner)):
    await ctx.send(f'No permissions to use "{ctx.command}".')
  else:
    await ctx.send(f'Default error message. <@{tyler["id"]}>\nError: {error}')

@tasks.loop(seconds=15)
async def change_presence():
  await bot.change_presence(activity=next(activities))

@bot.command(name='help', help='Sends this message')
async def help(ctx, cmd=None):
  '''
  If there are no arguments: sends a message with all the commands and their description.
  If there are arguments: sends a message with the command description.
  '''
  if cmd == None:
    text = '```'
    for cog in sorted(cogs):
      '''
      Don't print owner commands.
      '''
      if (cog == 'Owner'):
        continue
      elif (cog == 'None'):
        cog = 'General'
      text += f'--- {cog:^10} ---\n'
      for command in sorted(cogs[cog]):
        if cogs[cog][command] != None:
          help_line = cogs[cog][command].split("\n")[0]
        else:
          help_line = ''
        text += f'{command}: {help_line}\n'
    await ctx.send(f'{text}\nFor help with command usage, do {bot.command_prefix}help <command>```')
  else:
    for command in all_cmds:
      if cmd == command.name:
        await ctx.send(f'```{cogs[str(command.cog_name)][command.name]}```')
        return
    await ctx.send('Command not found')

bot.run(TOKEN)

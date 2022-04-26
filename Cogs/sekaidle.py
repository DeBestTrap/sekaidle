from discord.ext import commands, tasks
import discord, asyncio
import random, time, json
# Wordle Imports
import os, random, csv, country

class SekaidleCog(commands.Cog, name='Sekaidle'):
  def __init__(self, bot):
    self.bot = bot
    '''
    Opens the CSV and stores the country code, lat, long, and name into c_list.
    Then sorts it by the country code.
    '''
    global c_list
    c_list = []
    with open('countries.csv', newline='') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
        if row['latitude'] == '':
          continue
        c = country.Country(row['country'], row['name'], row['latitude'], row['longitude'])
        c_list.append(c)
    c_list.sort(key=lambda c:c.code)
    '''
    Remove countries that do not have images (not in the directory).
    '''
    excluded_countries = []
    directory = (os.listdir(os.getcwd() + '/country_imgs'))
    for c in c_list:
      if c.code.lower() not in directory:
        excluded_countries.append(c)
    for c in excluded_countries:
      c_list.remove(c)

  @commands.command(name='cn', help='Sekaidle with a random country')
  async def cn(self, ctx):
    '''
    Generate a random country, send the image into the channel and run the game loop.
    '''
    incorrect_msg = None
    c_correct = c_list[random.randint(0, len(c_list)-1)]
    print(ctx.author.nick, ctx.author.name, c_correct.name)
    await ctx.send(ctx.author.mention, file=discord.File(f'{os.getcwd()}/country_imgs/{c_correct.code.lower()}/1024.png'))
    turn = 1
    while turn < 7:
      guess_msg = await self.bot.wait_for('message', check=lambda message:
                                          message.author == ctx.author and
                                          message.channel == ctx.channel and
                                          not self.bot.command_prefix in message.content)

      '''
      If the user has already guessed incorrectly, delete the previous message.
      '''
      if incorrect_msg:
        await incorrect_msg.delete()
        incorrect_msg = None

      '''
      Stop the game if the user types 'stop'.
      '''
      if guess_msg.content.lower() == 'stop':
        saveTurnData(ctx.author.id, 7)
        saveBestTurnData(ctx.author.id, 7, c_correct.name)
        await guess_msg.delete()
        await ctx.send(f'{ctx.author.mention} gives up. SMH. The country was {c_correct.name}.')
        return

      '''
      If the guess is a country, check if it is a real country name.
      countryExists returns:
        a list with one country name, if the country name exists.
        a list with five similar country names, if the country name does not exist.
      '''
      c_guess_list = countryExists(guess_msg.content.lower())
      if len(c_guess_list) == 1:

        '''
        If the guess is correct, send a message and end the game.
        If not correct, send a message with the distance and direction
        to the correct country and continue the game.
        '''
        c_guess = c_guess_list[0]
        if c_guess == c_correct: 
          saveTurnData(ctx.author.id, turn)
          saveBestTurnData(ctx.author.id, turn, c_correct.name)
          await guess_msg.delete()
          await ctx.send(f'{ctx.author.mention} You win! The country was {c_correct.name}')
          return
        bearing, dist = c_guess.distanceTo(c_correct.returnCoord())
        await guess_msg.delete()
        await ctx.send(f'{ctx.author.mention} {c_guess.name} {round(dist)}km {returnBearingEmoji(bearing)}') 
        turn = turn + 1
        continue
      else:

        '''
        If the guess is not a country, don't increment the turn, 
        send a message with similar country names, and retry the guess.
        '''
        text = f'{ctx.author.mention} {guess_msg.content} is an invalid country!\nDid you mean?\n'
        for i,c in enumerate(c_guess_list):
          if i > 7:
            break
          text += f'  {c[1].name}\n'
        incorrect_msg = await ctx.send(text)
        await guess_msg.delete()

    '''
    If the player runs out of turns, send a message and end the game.
    '''
    saveTurnData(ctx.author.id, 7)
    saveBestTurnData(ctx.author.id, 7, c_correct.name)
    await ctx.send(f'{ctx.author.mention} You lose! The country was {c_correct.name}')

  @commands.command(name='stats', help='Display Stats')
  async def stats(self, ctx):
    '''
    Sends a message with every user's stats.
    Messages are formatted as:
    Page 1)
    <user1>:
      1: 2
      2: 0
      3: 0
      4: 1
      5: 0
      6: 1
      L: 21
    <user2>:
    ...
    '''

    '''
    Get the user's stats.
    Dict is formatted as:
    stats[user_id][turn]
    '''
    pages = []
    page_text = ''
    with open('stats.json', 'r') as f:
      stats = json.load(f)

    '''
    Generate pages of stats.
    3 Users per page.
    '''
    users_DPT = dict()
    page_ctr = 0
    for user_id in stats.keys():
      if page_ctr%4 == 0 and page_text != '':
        pages.append(page_text)
        page_text = ''
      if not int(user_id) in users_DPT.keys():
        users_DPT[int(user_id)] = await self.bot.fetch_user(int(user_id))
      name = users_DPT[int(user_id)]
      page_text += f'{name.display_name}\n'
      for turn in range(1, 8):
        turn_text = turn
        if turn == 7:
          turn_text = 'L'
        page_text += f'  {turn_text}: {stats[user_id][str(turn)]}\n'
      page_ctr += 1
    pages.append(page_text)
    stats_msg = await ctx.send(f'```\nPage 1)\n{pages[0]}```')

    try:
      await asyncio.wait_for(self.pageHandler(ctx, pages, stats_msg), timeout=120.0)
    except asyncio.TimeoutError:
      await stats_msg.clear_reactions()

  @commands.command(name='leaderboard', help='Display Leaderboard')
  async def leaderboard(self, ctx):
    '''
    Displays the leaderboard.
    Msg is formatted as:
    <country1>: <user1> in <turns> turns!
    <country2>: <user2> in <turns> turns!
    ...
    '''

    '''
    Get the leaderboard.
    Dict is formatted as:
    leaderboard[country_name] = {"id": user_id, "turn": turns}
    '''
    pages = []
    page_text = ''
    with open('leaderboard.json', 'r') as f:
      leaderboard = json.load(f)
    page_ctr = 0
    users_DPT = dict()
    for country in sorted(leaderboard.keys()):
      if page_ctr%20 == 0 and page_text != '':
        pages.append(page_text)
        page_text = ''
      id = leaderboard[country]['id']
      if id not in users_DPT.keys():
        users_DPT[id] = await self.bot.fetch_user(id)
      name = users_DPT[id]
      turns = leaderboard[country]['turn']
      page_text += f'{country}: {name.display_name} in {turns} turns!\n'
      page_ctr += 1
    pages.append(page_text)

    leaderboard_msg = await ctx.send(f'```\nPage 1)\n{pages[0]}```')
    try:
      await asyncio.wait_for(self.pageHandler(ctx, pages, leaderboard_msg), timeout=120.0)
    except asyncio.TimeoutError:
      await leaderboard_msg.clear_reactions()

  async def pageHandler(self, ctx, pages, msg):
    page_num = 0
    await msg.add_reaction('⬇️')
    await msg.add_reaction('⬆️')
    await msg.add_reaction('❌')
    page_down, page_up, end = False, False, False
    while not end:
      def check(reaction, user):
        nonlocal page_down; page_down = str(reaction.emoji) == '⬇️'
        nonlocal page_up; page_up = str(reaction.emoji) == '⬆️'
        nonlocal end; end = str(reaction.emoji) == '❌'
        return reaction.message == msg and user == ctx.author and (page_down or page_up or end)
      await self.bot.wait_for('reaction_add', check=check)
      if page_down:
        page_num = page_num - 1
        if page_num < 0:
          page_num = len(pages) - 1
      elif page_up:
        page_num = page_num + 1
        if page_num >= len(pages):
          page_num = 0
      await msg.edit(content= (f'```\nPage {page_num+1})\n{pages[page_num]}```') )
    await msg.clear_reactions()

def setup(bot):
  bot.add_cog(SekaidleCog(bot))

def countryExists(c):
  '''
  Returns the country name if it is in c_list, otherwise returns None.
  '''
  difference_list = []
  for c_ in c_list:
    if c_.name.lower() == c.lower():
      return [c_]
  for c_ in c_list:
    difference_list.append( (findDifferenceScore(c_.name.lower(), c.lower()), c_) )
  return sorted(difference_list, key=lambda x: x[0])

def returnBearingEmoji(bearing):
  '''
  Returns the emoji based on the bearing.
  '''
  bearing = bearing%360
  if bearing <= 15:
    return ':arrow_up:'
  elif bearing <= 75:
    return ':arrow_upper_right:'
  elif bearing <= 105:
    return ':arrow_right:'
  elif bearing <= 165:
    return ':arrow_lower_right:'
  elif bearing <= 195:
    return ':arrow_down:'
  elif bearing <= 255:
    return ':arrow_lower_left:'
  elif bearing <= 285:
    return ':arrow_left:'
  elif bearing <= 345:
    return ':arrow_upper_left:'
  else:
    return ':arrow_up:'

def saveBestTurnData(id, turn, country):
  '''
  Checks to see if the country has a best guess yet.
    If it does, then check to see if the new guess is better than the old one, update if so.
    If it is not, then do nothing.
  If the country does not exist, then add it to the leaderboard.
  '''
  with open('leaderboard.json', 'r') as f:
    leaderboard = json.load(f)
  if country in leaderboard.keys():
    if turn > leaderboard[country]['turn']:
      '''
      The turn is not better than the best guess so far, don't do anything.
      '''
      return
    else:
      '''
      The turn is better than the best guess so far, update it in the leaderboard.
      '''
      leaderboard[country] = {'id': id, 'turn': turn}
  else:
    '''
    The country has not been guessed yet, add it to the leaderboard.
    '''
    leaderboard[country] = {'id': id, 'turn': turn}
  with open('leaderboard.json', 'w') as f:
    json.dump(leaderboard, f)
  
def saveTurnData(id, turn):
  '''
  Saves the player stats to the leaderboard.
  '''
  id_ = str(id)
  with open('stats.json', 'r') as f:
    stats = json.load(f)
  '''
  If the player has not played before, then add them to the leaderboard.
  '''
  if id_ not in stats.keys():
    stats[id_] = {}
    for i in range(1, 8):
     stats[id_][str(i)] = 0
  '''
  Save the turn data for the player to the leaderboard.
  '''
  num = stats[id_][str(turn)]
  stats[id_][str(turn)] = num + 1 
  with open('stats.json', 'w') as f:
    json.dump(stats, f)

def findDifferenceScore(str1, str2):
  '''
  Returns the number of differences between the two strings:
  The higher the score, the more different the strings are.
  '''
  global DPTable
  DPTable = [ [None for i in range(len(str2)+1)] for j in range(len(str1)+1) ]
  return differenceScoreHelper(str1, str2)

def differenceScoreHelper(str1, str2):
  '''
  Returns the number of differences between the two strings.
  Uses dynamic programming to speed up the process.  
  '''

  global DPTable
  if str1 == '' and str2 == '':
    '''
    Base Case 1: Both strings are empty, difference is 0.
    '''
    DPTable[0][0] = 0
    return 0

  elif str1 == '':
    '''
    Base Case 2: str1 is empty, difference is the length of str2.
    '''
    DPTable[0][len(str2)-1] = len(str2)
    return len(str2)

  elif str2 == '':
    '''
    Base Case 3: str2 is empty, difference is the length of str1.
    '''
    DPTable[len(str1)-1][0] = len(str1)
    return len(str1)

  elif str1[0] == str2[0]:
    '''
    The first characters of str1 and str2 are the same, so the difference 
    does not increase and depends on the difference of the rest of the strings.
    '''
    if DPTable[len(str1)-2][len(str2)-2] != None:
      return DPTable[len(str1)-2][len(str2)-2]
    else:
      return differenceScoreHelper(str1[1:], str2[1:])

  else:
    '''
    The first characters of str1 and str2 are different, so find the difference if:
    1) The first character of str1 is deleted.
    2) The first character of str2 is added to str1.
    3) The first character of str2 replaces the first character of str1.
    '''
    if DPTable[len(str1)-1][len(str2)-1] != None:
      return DPTable[len(str1)-1][len(str2)-1]
    else:
      sub_problems_result = [ differenceScoreHelper(str1[1:], str2),
                              differenceScoreHelper(str2[0]+str1, str2),
                              differenceScoreHelper(str2[0]+str1[1:], str2)]
      DPTable[len(str1)-1][len(str2)-1] = min(sub_problems_result)+1
      return DPTable[len(str1)-1][len(str2)-1]
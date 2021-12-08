#COPYRIGHT 2021 Mazilu Flavius

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.

#blablablalalalalalala
	#!./.venv/bin/python

from abc import get_cache_token
import discord      # base discord module
import code         # code.interact
import os           # environment variables
import inspect      # call stack inspection
import random       # dumb random number generator
import argparse
parser =argparse.ArgumentParser()
parser.add_argument("--verbosity", help="increase output verbosity")
args = parser.parse_args()
if args.verbosity:
	print("verbosity turned on")
from discord.ext import commands    # Bot class and utils

################################################################################
############################### HELPER FUNCTIONS ###############################
################################################################################

# log_msg - fancy print
#   @msg   : string to print
#   @level : log level from {'debug', 'info', 'warning', 'error'}
def log_msg(msg: str, level: str):
	# user selectable display config (prompt symbol, color)
	dsp_sel = {
		'debug'   : ('\033[34m', '-'),
		'info'    : ('\033[32m', '*'),
		'warning' : ('\033[33m', '?'),
		'error'   : ('\033[31m', '!'),
	}

	# internal ansi codes
	_extra_ansi = {
		'critical' : '\033[35m',
		'bold'     : '\033[1m',
		'unbold'   : '\033[2m',
		'clear'    : '\033[0m',
	}

	# get information about call site
	caller = inspect.stack()[1]

	# input sanity check
	if level not in dsp_sel:
		print('%s%s[@] %s:%d %sBad log level: "%s"%s' % \
			(_extra_ansi['critical'], _extra_ansi['bold'],
			 caller.function, caller.lineno,
			 _extra_ansi['unbold'], level, _extra_ansi['clear']))
		return

	# print the damn message already
	print('%s%s[%s] %s:%d %s%s%s' % \
		(_extra_ansi['bold'], *dsp_sel[level],
		 caller.function, caller.lineno,
		 _extra_ansi['unbold'], msg, _extra_ansi['clear']))

################################################################################
############################## BOT IMPLEMENTATION ##############################
################################################################################

# bot instantiation
bot = commands.Bot(command_prefix='!')

# on_ready - called after connection to server is established
@bot.event
async def on_ready():
	log_msg('logged on as <%s>' % bot.user, 'info')

# on_message - called when a new message is posted to the server
#   @msg : discord.message.Message
@bot.event
async def on_message(msg):
	# filter out our own messages
	if msg.author == bot.user:
		return

	log_msg('message from <%s>: "%s"' % (msg.author, msg.content), 'debug')

	# overriding the default on_message handler blocks commands from executing
	# manually call the bot's command processor on given message
	await bot.process_commands(msg)
	# code.interact(local=dict(bot = bot, msg = msg))

# roll - rng chat command
#   @ctx     : command invocation context
#   @max_val : upper bound for number generation (must be at least 1)
@bot.command(brief='Generate random number between 1 and <arg>')
async def roll(ctx, max_val: int):
	# argument sanity check
	if max_val < 1:
		raise Exception('argument <max_val> must be at least 1')

	await ctx.send(random.randint(1, max_val))

@bot.command(brief='Bot joins the voice channel')
async def join(ctx):
	# check if the author is in a voice channel
	if ctx.author.voice is None:
		await ctx.send('enter a voice channel')
		raise Exception('author is not in a voice channel')
	
	# save the channel where the author is connected
	voice_channel = ctx.author.voice.channel

	# check whether bot is connected elsewhere or not
	if ctx.voice_client is None:
		await voice_channel.connect()

	await ctx.send('bot ON')

@bot.command(brief='Bot leaves')
async def scram(ctx):
	# check if bot is connected at all
	if ctx.voice_client is None:
		raise Exception('bot is not in a voice channel')

	# make him go away
	await ctx.voice_client.disconnect()
	await ctx.send('quit')

@bot.command(brief='Bot changes voice channels')
async def cmere(ctx):
	# check if bot is connected
	if ctx.voice_client is None:
		raise Exception('bot is not already in a voice channel')
	
	# check if author is connected
	if ctx.author.voice is None:
		raise Exception('author is not already in a voice channel')
	# check if author is not in the same channel as bot
	elif ctx.author.voice.channel is ctx.voice_client.channel:
		await ctx.send('already here, boss')
		raise Exception('bot is already in the same voice channel as author')

	# bot swtiches channels
	voice_channel = ctx.author.voice.channel
	await ctx.voice_client.disconnect()
	await voice_channel.connect()

@bot.command(brief='Bot plays a song')
async def play(ctx, song : str):
	
	if ctx.author.voice is None:
		await ctx.send('connect first')
		raise Exception('author not connected')

	if ("%s.mp3" %song) in os.listdir('./music/'):	
		if ctx.voice_client.is_playin():
			await ctx.send('i am already playing something, adding to queue')
			
			raise Exception('bot is already playing a song')

		if ctx.voice_client is None:
			await ctx.invoke(bot.get_command('join'))
		elif ctx.voice_client.channel is not ctx.author.voice.channel:
			await ctx.invoke(bot.get_command('cmere'))

		ctx.voice_client.play(discord.FFmpegPCMAudio("./music/%s.mp3" %song))
	else:
		await ctx.send('i do not have that song locally')
		


@bot.command(brief='Bot pauses')
async def pause(ctx):
	if ctx.author.voice is None:
		await ctx.send('PAUSED')
		raise Exception('author not connected')

	if ctx.voice_client is None:
		await ctx.send('not here')
		raise Exception('bot is not already in a voice channel')

	if ctx.voice_client.channel is not ctx.author.voice.channel:
		await ctx.send("you are not the boss of me, %s" %ctx.author)
		raise Exception('author is not in the same channel as bot')

	if ctx.voice_client.is_playing():
		ctx.voice_client.pause()
	else:
		await ctx.send('nothing to pause here')
		raise Exception('bot is not playing anything')

@bot.command(brief='Bot resumes playing')
async def resume(ctx):
	if ctx.author.voice is None:
		await ctx.send('RESUMED')
		raise Exception('author not connected')

	if ctx.voice_client is None:
		await ctx.send('not even here')
		raise Exception('bot is not already in a voice channel')

	if ctx.voice_client.channel is not ctx.author.voice.channel:
		await ctx.send("you are not the boss of me, %s" %ctx.author)
		raise Exception('author is not in the same channel as bot')

	if ctx.voice_client.is_paused():
		ctx.voice_client.resume()
	else:
		await ctx.send('nothing to resume here')
		raise Exception('bot is not paused anything')




# roll_error - error handler for the <roll> command
#   @ctx     : command that crashed invocation context
#   @error   : ...
@roll.error
async def roll_error(ctx, error):
	await ctx.send(str(error))

################################################################################
############################# PROGRAM ENTRY POINT ##############################
################################################################################

if __name__ == '__main__':
	# check that token exists in environment
	if 'BOT_TOKEN' not in os.environ:
		log_msg('save your token in the BOT_TOKEN env variable!', 'error')
		exit(-1)

	# launch bot (blocking operation)
	bot.run(os.environ['BOT_TOKEN'])

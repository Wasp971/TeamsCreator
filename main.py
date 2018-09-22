import os
from subprocess import Popen

import aiohttp
import discord
from discord.ext import commands
import numpy
import math
import _thread

TOKEN = "NDU5NjMzMDU0MDU1NjYxNTY4.Dg5COg.vzK3yXnNSxbDzr00t2ZfBoz9mT0"

bot = commands.Bot(command_prefix='/')
names = ""
teams_num = 0
team_dim = 0
channel = ""
teams = None
voice_client = None
server = None
teams_channel = None
voice_channel = None
states = {}
tts_status = True
PATH="/TeamsCreator/"
NUM_EMOJI = ["<:one:459728790160015360>","<:two:459729375408160778>","<:three:459729387068063775>",
			 "<:four:459729399625809923>","<:five:459729411277586442>","<:six:459729423361507329>",
			 "<:seven:459729448175009803>","<:eight:459729484237504525>","<:nine:459729515820613673>",
			 "<:keycap_ten:459729545860218880>"]


@bot.event
async def on_ready():
	global teams_channel
	print('Ready')


@bot.command(pass_context=True, description="st_dim: imposta la dimensione dei team")
async def st_dim(ctx, n_in):
	global team_dim
	global channel
	global voice_client
	global server
	global teams_channel
	global voice_channel
	team_dim = int(n_in)
	server = ctx.message.server
	teams_channel = get_channel_by_name("teams", server)
	voice_channel = ctx.message.author.voice.voice_channel
	await del_last(ctx.message)
	await bot.send_message(teams_channel, "Teams dimension set to: "+n_in+"\n")


@bot.command(pass_context=True, description="ct_by_dim <nome nome>: crea team in base alla dimensione a partire dalla lista (se non presente, utilizza la lista precedente)")
async def ct_by_dim(ctx, *args):
	global names
	global teams_num
	global states
	await del_last(ctx.message)
	tts_msg = ""
	if len(args) != 0:
		names = args
		teams_num = int(numpy.ceil(len(names)/team_dim))
		print("names:", names)
	names = numpy.random.permutation(names)
	split(names, teams_num)
	for i in range(len(teams)):
		tts_msg = tts_msg + "Team" + str(i+1) + str(teams[i]) + "\n"
		states[i] = "Inizio"
		await bot.send_message(teams_channel, NUM_EMOJI[i]+print_team(teams[i]))
	tts_msg = await bot.send_message(teams_channel, content=tts_msg, tts=tts_status)
	await bot.delete_message(tts_msg)
	await bot.send_message(teams_channel, "\n")

# noinspection PyShadowingNames
@bot.command(pass_context=True, description="st_dim: imposta il numero di team da generare")
async def st_num(ctx, n_in):
	global teams_num
	global channel
	global voice_client
	global teams_channel
	global voice_channel
	global server
	await del_last(ctx.message)
	teams_num = int(n_in)
	server = ctx.message.server
	channel = ctx.message.channel
	teams_channel = get_channel_by_name("teams", server)
	voice_channel = ctx.message.author.voice.voice_channel
	await bot.send_message(teams_channel, "Teams number set to: "+n_in+"\n")


@bot.command(pass_context=True, description="ct_by_dim <nome nome>: crea team in base al numero a partire dalla lista (se non presente, utilizza la lista precedente)")
async def ct_by_num(ctx, *args):
	global names
	global team_dim
	global states
	await del_last(ctx.message)
	tts_msg = ""
	if len(args) != 0:
		team_dim = math.ceil(len(args)/teams_num)
		names = args
		print("names:", names)
	names = numpy.random.permutation(names)
	print(names)
	split(names, teams_num)
	for i in range(len(teams)):
		tts_msg = tts_msg+"Team"+str(i+1)+str(teams[i])+"\n"
		states[i] = "Inizio"
		await bot.send_message(teams_channel, NUM_EMOJI[i]+print_team(teams[i]))
	tts_msg = await bot.send_message(teams_channel, content=tts_msg, tts=tts_status)
	await bot.delete_message(tts_msg)
	await bot.send_message(teams_channel, "\n")


# noinspection PyShadowingNames
@bot.command(pass_context=True, description="state <stato>: visualizza lo stato dei team e, se indicato, imposta lo stato del proprio team (NO SPAZI!)")
async def state(ctx, *state):
	global states
	await del_last(ctx.message)
	if len(state) != 0:
		states[search_team(ctx.message.author)] = state[0]
	print(states)
	for i in range(len(teams)):
		await bot.send_message(teams_channel, NUM_EMOJI[i] + " " + states[i]+"\n")


def search_team(author):
	for y in range(len(teams)):
		for i in range(len(teams[y])):
			if teams[y][i].lower() == author.name.lower():
				return y


def print_team(team):
	t = ""
	for i in range(len(team)):
		if team[i] != None:
			t += team[i]+", "
	return t[:-2]


# noinspection PyShadowingNames
def split(names, n):
	global teams
	temp_names = names
	try:
		temp = numpy.split(temp_names, teams_num)
		teams = temp
	except ValueError:
		temp_names = numpy.append(temp_names, None)
		split(temp_names, n)


# noinspection PyShadowingNames
@bot.command(pass_context=True, desciption="move_players: crea abbastanza canali vocali per i team e sposta le persone")
async def move_players(ctx):
	await del_last(ctx.message)
	server = ctx.message.server
	await bot.send_message(teams_channel, content="Moving players\n", tts=tts_status)
	i = 1
	for team in teams:
		channel = get_channel_by_name("Team"+str(i))
		for member in team:
			if member != None:
				await bot.move_member(get_member_by_name(member, server), channel)
		i += 1;


@bot.command(pass_context=True, desciption="end_teams: elimina i canali vocali creati")
async def end_teams(ctx):
	await del_last(ctx.message)
	i = 1
	for team in teams:
		for member in team:
			await bot.move_member(get_member_by_name(member, server), voice_channel)
		i += 1
	await bot.send_message(teams_channel, "All teams ended ended\n")


# noinspection PyShadowingNames
@bot.command(pass_context=True, desciption="end_team: elimina il canale del team indicato")
async def end_team(ctx, n):
	await del_last(ctx.message)
	server = ctx.message.server
	for member in teams[int(n)]:
		await bot.move_member(get_member_by_name(member, server), voice_channel)
	await bot.send_message(teams_channel, "Team"+n+" ended\n")


@bot.command(description="clear: cancella tutti i messaggi")
async def clear():
	async for msg in bot.logs_from(teams_channel):
		await bot.delete_message(msg)


# noinspection PyShadowingNames
def get_channel_by_name(name, server):
	channels = server.channels
	for channel in channels:
		if channel.name == name:
			return channel


# noinspection PyShadowingNames
def get_member_by_name(name, server):
	members = server.members
	for member in members:
		if member.name.lower() == name.lower():
			return member


# noinspection PyShadowingNames
def wait_creation(channel):
	while channel.type != discord.ChannelType.voice:
		print("Here2")
		pass


@bot.command(pass_context=True)
async def enable_debug(ctx):
	global tts_status
	await del_last(ctx.message)
	tts_status = False;


@bot.command(pass_context=True)
async def disable_debug(ctx):
	global tts_status
	await del_last(ctx.message)
	tts_status = True;


async def del_last(msg):
	await bot.delete_message(msg)


def check_connection():
	try:
		teams_channel.server.roles
	except aiohttp.errors.ClientOSError:
		os.system('sudo shutdown -r now')


check_connection_thread = _thread.start_new_thread(check_connection, ())

bot.run(TOKEN)


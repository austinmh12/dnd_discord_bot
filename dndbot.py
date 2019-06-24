import discord
import re
from oauth2client.service_account import ServiceAccountCredentials as SAC
import gspread
import random as rand
import logging
import client_info

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(levelname)s]: %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

CLIENT_ID = client_info.info['CLIENT_ID']
CLIENT_SECRET = client_info.info['CLIENT_SECRET']
TOKEN = client_info.info['TOKEN']


scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
cred = SAC.from_json_keyfile_name('dndbot_scopes.json', scope)
g_sheets = gspread.authorize(cred)
dnd_sheet = g_sheets.open('DnDTest')

client = discord.Client()

@client.event
async def on_ready():
	log.info('We\'ve logged on as {0.user}'.format(client))

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.content.startswith('!'):
		log.debug('Parsing command')
		log.debug(message.author.id)
		resp = parse_command(message)
		if isinstance(resp, str):
			await message.channel.send(resp)
		elif isinstance(resp, list):
			await message.channel.send(str(resp))
		else:
			await message.channel.send(embed=resp)

def parse_command(message):
	msg = message.content.lower()
	command, *args = msg.split(' ')

	if command == '!help':
		log.debug('Showing command list')
		ret = list(help_.keys())
		log.debug(ret)
		return ret

	if command == '!init' or command == '!i':
		log.debug('The initiative command is being used!')
		ret = initiative(message)
		return ret

	if command == '!create':
		log.debug('The create command is being used!')
		ret = create(message)
		return ret

	if not args:
		log.info('No arguments, displaying help')
		return help_.get(command)

	if command == '!roll':
		log.debug('The roll command is being used!')
		ret = roll(args)
		return ret
	if command == '!damage':
		log.debug('The damage command is being used!')
		ret = damage(message)
		return ret

	if command == '!heal':
		log.debug('The heal command is being used!')
		ret = heal(message)
		return ret

	if command == '!stat':
		log.debug('The stat command is being used!')
		ret = stat(message)
		return ret

	

	return 'Unknown command.'


def roll(die):
	ret = []
	for dice in die:
		if dice == 'd4':
			log.info('Rolling D4')
			value = rand.randint(1,4)
			ret.append(value)
		elif dice == 'd6':
			log.info('Rolling D6')
			value = rand.randint(1,6)
			ret.append(value)
		elif dice == 'd8':
			log.info('Rolling D8')
			value = rand.randint(1,8)
			ret.append(value)
		elif dice == 'd10':
			log.info('Rolling D10')
			value = rand.randint(1,10)
			ret.append(value)
		elif dice == 'd12':
			log.info('Rolling D12')
			value = rand.randint(1,12)
			ret.append(value)
		elif dice == 'd20':
			log.info('Rolling D20')
			value = rand.randint(1,20)
			ret.append(value)
		elif dice == 'd100':
			log.info('Rolling D100')
			value = rand.randint(1,10) * 10
			ret.append(value)
		else:
			return help_.get('!roll')
	return ret

def damage(message):
	msg = message.content.lower()
	user = message.mentions[0]
	_, user_id, *args = msg.split(' ')
	if not args:
		return help_.get('!damage')

	if len(args) == 1 and not args[0].startswith('d'):
		ret = deal_damage(user, user_id, args[0])
	else:
		dmg = sum(roll(args))
		ret = deal_damage(user, user_id, dmg)
	return ret

def deal_damage(user, user_id, damage):
	username, _ = str(user).split('#')
	log.debug(user)
	user_sheet = dnd_sheet.worksheet(username)
	hp_cell = user_sheet.find('HP')
	existing_wounds = user_sheet.cell(hp_cell.row, hp_cell.col+2).value
	new_wounds = int(existing_wounds) + int(damage)
	user_sheet.update_cell(hp_cell.row, hp_cell.col+2, new_wounds)
	damage_quip = rand.choice(damage_quips)
	return f'Damaged {user_id} for {damage}. {damage_quip}!'

def heal(message):
	msg = message.content.lower()
	author = message.author.id
	user = message.mentions[0]
	_, user_id, *args = msg.split(' ')
	if not args:
		return help_.get('!heal')

	if len(args) == 1 and not args[0].startswith('d'):
		ret = add_health(author, user, user_id, args[0])
	else:
		health = sum(roll(args))
		ret = add_health(author, user, user_id, health)
	return ret

def add_health(author, user, user_id, health):
	username, _ = str(user).split('#')
	log.debug(user)
	user_sheet = dnd_sheet.worksheet(username)
	hp_cell = user_sheet.find('HP')
	existing_wounds = user_sheet.cell(hp_cell.row, hp_cell.col+2).value
	new_wounds = max((int(existing_wounds) - int(health)), 0)
	user_sheet.update_cell(hp_cell.row, hp_cell.col+2, new_wounds)
	return f'<@{author}> healed {user_id} for {health}.'

def initiative(message):
	author = message.author
	username, _ = str(author).split('#')
	user_sheet = dnd_sheet.worksheet(username)
	dex_cell = user_sheet.find('DEX')
	dex_mod = int(user_sheet.cell(dex_cell.row, dex_cell.col+2).value)
	init_roll = roll(['d20'])[0] + dex_mod
	return f'<@{author.id}> rolled a {init_roll} for initiative.'

def create(message):
	rolls = roll(['d6','d6','d6','d6'])
	rolls.sort()
	filt = rolls[1:]
	return '<@{author}> rolled {rolls} for a total of {tot}'.format(
		author=message.author.id,
		rolls=str(rolls),
		tot=sum(filt)
	)

def stat(message):
	username, _ = str(message.author).split('#')
	_, attr = message.content.upper().split(' ')
	if attr not in ['STR','DEX','CON','INT','WIS','CHA','HP']:
		return 'Not a stat.'
	user_sheet = dnd_sheet.worksheet(username)
	attr_cell = user_sheet.find(attr)
	attr_value = user_sheet.cell(attr_cell.row, attr_cell.col + 1).value
	return f'<@{message.author.id}> has a {attr} of {attr_value}.'











def get_embed(title, desc, usage, examples):
	embed = discord.Embed(
		title=f'**{title}**',
		description=desc,
		colour=discord.Colour.dark_green()
	)

	embed.add_field(name='**> Usage**', value=usage, inline=False)
	embed.add_field(name='**> Examples**', value='\n'.join(examples), inline=False)

	return embed


help_ = {
	'!roll': get_embed('Roll', 'Rolls the specified die.', '`!roll [dice]`', ['`!roll d4`','`!roll d12 d20`']),
	'!damage': get_embed('Damage', 'Damages a specified player with either a dice roll or a determined amount of damage.', '`!damage @<user> <die or damage number>`', ['`!damage @rectrec369 6`','`!damage @rectrec369 d8`']),
	'!heal': get_embed('Heal', 'Heals a specified played with either a determined amount or a dice roll.', '`!heal <@user> <die or damage number>', ['`!heal @rectrec369 3`', '`!heal @rectrec369 d8`']),
	'!init': get_embed('Initiative', 'Rolls for initiative taking into account the user\'s DEX modifier.', '`!init`', ['`!init`','`!i`']),
	'!i': get_embed('Initiative', 'Rolls for initiative taking into account the user\'s DEX modifier.', '`!init`', ['`!init`','`!i`']),
	'!create': get_embed('Create', 'Rolls four D6s and removes the lowest value. Used to create new characters.', '`!create`', ['`!create`']),
	'!stat': get_embed('Stat', 'Returns the value of the user\'s specified stat.', '`!stat <stat>`', ['`!stat dex`','`!stat str`'])

}

damage_quips = [
	'Ouch',
	'That must\'ve hurt',
	'F',
	'Oof',
	'Holy shit',
	'Where\'d they learn to do that',
	'Oh barnacles',
	'Oh fuck',
]


client.run(TOKEN)
import discord
import re
from oauth2client.service_account import ServiceAccountCredentials as SAC
import gspread
import random as rand
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(levelname)s]: %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

CLIENT_ID = '592509064995536909'
CLIENT_SECRET = '5IhlBqsaUDYfeOKmrXs3CijbIseykfgi'
TOKEN = 'NTkyNTA5MDY0OTk1NTM2OTA5.XRAXcA.5Mu6HAuQzUxdTwX4knU46E0y0d0'


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
		resp = parse_command(message)
		if isinstance(resp, str):
			await message.channel.send(resp)
		else:
			await message.channel.send(embed=resp)

def parse_command(message):
	msg = message.content.lower()
	command, *args = msg.split(' ')
	if not args:
		log.info('No arguments, displaying help')
		return help_.get(command)

	if command == '!roll':
		log.debug('The roll command is being used!')
		ret = roll(args)
		return str(ret)

	if command == '!damage':
		log.debug('The damage command is being used!')
		ret = damage(message)
		return ret

	if command == '!heal':
		log.debug('The heal command is being used!')
		ret = heal(message)
		return ret


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
		elif dice == 'd20':
			log.info('Rolling D20')
			value = rand.randint(1,20)
			ret.append(value)
		elif dice == 'd100':
			log.info('Rolling D100')
			value = rand.randint(1,10) * 10
			ret.append(value)
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
	username, tag = str(user).split('#')
	log.debug(user)
	user_sheet = dnd_sheet.worksheet(username)
	hp_cell = user_sheet.find('HP')
	existing_wounds = user_sheet.cell(hp_cell.row, hp_cell.col+2).value
	new_wounds = int(existing_wounds) + int(damage)
	user_sheet.update_cell(hp_cell.row, hp_cell.col+2, new_wounds)
	return f'Damaged {user_id} for {damage}. Ouch!'

def heal(message):
	msg = message.content.lower()
	user = message.mentions[0]
	_, user_id, *args = msg.split(' ')
	if not args:
		return help_.get('!heal')

	if len(args) == 1 and not args[0].startswith('d'):
		ret = add_health(user, user_id, args[0])
	else:
		health = sum(roll(args))
		ret = add_health(user, user_id, health)
	return ret

def add_health(user, user_id, health):
	username, tag = str(user).split('#')
	log.debug(user)
	user_sheet = dnd_sheet.worksheet(username)
	hp_cell = user_sheet.find('HP')
	existing_wounds = user_sheet.cell(hp_cell.row, hp_cell.col+2).value
	new_wounds = max((int(existing_wounds) - int(health)), 0)
	user_sheet.update_cell(hp_cell.row, hp_cell.col+2, new_wounds)
	return f'Healed {user_id} for {health}.'


















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
	'!heal': get_embed('Heal', 'Heals a specified played with either a determined amount or a dice roll.', '`!heal <@user> <die or damage number>', ['`!heal @rectrec369 3`', '`!heal @rectrec369 d8`'])

}


client.run(TOKEN)
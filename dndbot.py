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

# CLIENT_ID = client_info.info['CLIENT_ID']
# CLIENT_SECRET = client_info.info['CLIENT_SECRET']
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
			await message.channel.send(' '.join([str(i) for i in resp]))
		elif not resp:
			await message.channel.send(file=discord.File('resources/idiots.gif'))
		elif isinstance(resp, discord.Embed):
			await message.channel.send(embed=resp)
		elif isinstance(resp, discord.File):
			await message.channel.send(file=resp)
		elif isinstance(resp, tuple):
			await message.channel.send(resp[0], file=resp[1])

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

	if command == '!roll':
		log.debug('The roll command is being used!')
		ret = roll(message)
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
		ret = get_stat(message)
		return ret

	if command == '!skill':
		log.debug('The skill command is being used!')
		ret = get_skill(message)
		return ret

	if command == '!xp':
		log.debug('The get_exp command is being used!')
		ret = get_exp(message)
		return ret

	if command == '!addxp':
		log.debug('The add_exp command is being used!')
		ret = add_exp(message)
		return ret

	if command == '!summary':
		log.debug('The summary command is being used!')
		ret = summary(message)
		return ret

	if command == '!d4':
		log.debug('Running roll command!')
		ret = roll(['d4'])
		return ret

	if command == '!d6':
		log.debug('Running roll command!')
		ret = roll(['d6'])
		return ret

	if command == '!d8':
		log.debug('Running roll command!')
		ret = roll(['d8'])
		return ret

	if command == '!d10':
		log.debug('Running roll command!')
		ret = roll(['d10'])
		return ret

	if command == '!d12':
		log.debug('Running roll command!')
		ret = roll(['d12'])
		return ret

	if command == '!d20':
		log.debug('Running roll command!')
		ret = roll(['d20'])
		return ret

	if command == '!d100':
		log.debug('Running roll command!')
		ret = roll(['d100'])
		return ret


	
	if not args and command in list(help_.keys()):
		log.info('No arguments, displaying help')
		return help_.get(command)

	return None

def roll(message):
	ret = []
	if isinstance(message, list):
		die = message
	else:
		_, *die = message.content.lower().split(' ')

	if not die:
		return help_.get('!roll')

	for dice in die:
		if 'x' in dice:
			amt, dice_val = [int(val) for val in dice.split('xd')]
		else:
			amt = 1
			dice_val = int(dice[1:])
		if dice_val not in [4,6,8,10,12,20,100]:
			return help_.get('!roll')
		log.info(f'Rolling {amt} D{dice_val}')
		ret.extend([rand.randint(1,dice_val) for i in range(amt)])
	if len(ret) == 1 and ret[0] == 20 and dice_val == 20:
		return (20, discord.File('resources/nat20.gif'))
	if len(ret) == 1 and ret[0] == 1 and dice_val == 20:
		return (1, discord.File('resources/nat1.gif'))
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
	init_roll = roll(['d20'])[0]
	return f'<@{author.id}> rolled a {init_roll + dex_mod} for initiative.'

def create(message):
	rolls = roll(['d6','d6','d6','d6'])
	rolls.sort()
	filt = rolls[1:]
	return '<@{author}> rolled {rolls} for a total of {tot}'.format(
		author=message.author.id,
		rolls=str(rolls),
		tot=sum(filt)
	)

def get_stat(message):
	user_sheet = get_user_sheet(message)
	_, attr = message.content.upper().split(' ')
	if attr not in ['STR','DEX','CON','INT','WIS','CHA','HP']:
		return 'Not a stat.'
	attr_cell = user_sheet.find(attr)
	attr_value = user_sheet.cell(attr_cell.row, attr_cell.col + 1).value
	return f'<@{message.author.id}> has a {attr} of {attr_value}.'

def get_skill(message):
	user_sheet = get_user_sheet(message)
	_, skill = message.content.lower().split(' ')
	skill_list = [cell.value.lower() for cell in user_sheet.range('M2:M40')]
	if skill not in skill_list:
		return 'Not a skill'
	skill_cell = user_sheet.find(skill)
	skill_value = user_sheet.cell(skill_cell.row, skill_cell.col+1).value
	return f'<@{message.author.id}> has a {skill} of {skill_value}.'

def get_exp(message):
	user_sheet = get_user_sheet(message)
	exp_cell = user_sheet.find('EXP')
	exp_value = user_sheet.cell(exp_cell.row+1, exp_cell.col).value
	return f'<@{message.author.id}> has {exp_value} exp.'

def add_exp(message):
	_, exp = message.content.lower().split(' ')
	if not exp:
		return help_.get('!addxp')
	exp = int(exp)
	user_sheet = get_user_sheet(message)
	exp_cell = user_sheet.find('EXP')
	exp_value = int(user_sheet.cell(exp_cell.row+1, exp_cell.col).value)
	new_exp = exp_value + exp
	user_sheet.update_cell(exp_cell.row+1, exp_cell.col, new_exp)
	return f'<@{message.author.id}> has {new_exp} exp.'

def save_roll(message):
	pass

def attack_roll(message):
	user_sheet = get_user_sheet(message)

	pass

def summary(message):
	username, _ = str(message.author).split('#')
	user_sheet = dnd_sheet.worksheet(username)
	name = user_sheet.acell('B2').value
	embed = discord.Embed(
		title=f'**{name}**',
		description=f'{username}\'s character.',
		colour=discord.Colour.blue()
	)
	cell_names = [c.value for c in user_sheet.range('A3:A15')]
	log.debug(cell_names)
	cell_values = [c.value for c in user_sheet.range('B3:B15')]
	log.debug(cell_values)
	for i, cell in enumerate(list(zip(*[cell_names, cell_values])), start=1):
		cell_name, cell_value = cell
		if not cell_value:
			cell_value = 'None'
		embed.add_field(name=f'**> {cell_name}**', value=cell_value, inline=True)

	return embed


def get_user_sheet(message):
	username, _ = str(message.author).split('#')
	user_sheet - dnd_sheet.worksheet(username)
	return user_sheet








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
	'!roll': get_embed('Roll', 'Rolls the specified die.', '`!roll [dice]`', ['`!roll d4`','`!roll d12 d20`','`!roll 2xd8`']),
	'!damage': get_embed('Damage', 'Damages a specified player with either a dice roll or a determined amount of damage.', '`!damage @<user> <die or damage number>`', ['`!damage @rectrec369 6`','`!damage @rectrec369 d8`']),
	'!heal': get_embed('Heal', 'Heals a specified played with either a determined amount or a dice roll.', '`!heal <@user> <die or damage number>', ['`!heal @rectrec369 3`', '`!heal @rectrec369 d8`']),
	'!init': get_embed('Initiative', 'Rolls for initiative taking into account the user\'s DEX modifier.', '`!init`', ['`!init`','`!i`']),
	'!i': get_embed('Initiative', 'Rolls for initiative taking into account the user\'s DEX modifier.', '`!init`', ['`!init`','`!i`']),
	'!create': get_embed('Create', 'Rolls four D6s and removes the lowest value. Used to create new characters.', '`!create`', ['`!create`']),
	'!stat': get_embed('Stat', 'Returns the value of the user\'s specified stat.', '`!stat <stat>`', ['`!stat dex`','`!stat str`']),
	'!skill': get_embed('Skill','Returns the value of the user\'s specified skill.','`!skill <skill>`',['`!skill stealth`','`!skill perception`']),
	'!xp': get_embed('XP','Returns the amount of experience the user has.','`!xp`',['`!xp`']),
	'!addxp': get_embed('Add XP','Adds the amount of experience to the user\'s current experience','`!addxp <amount>`',['`!addxp 500`','`!addxp 1250`']),
	'!summary': get_embed('Summary','Returns a summary of the current user\'s character','`!summary`',['`!summary`'])

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
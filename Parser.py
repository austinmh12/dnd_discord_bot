import discord, re, gspread, logging
from oauth2client.service_account import ServiceAccountCredentials as SAC
import random as rand
from PIL import Image as Img, ImageDraw as IDraw
import client_info
from Character import Character as Char
from Monster import Monster as Mon

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
cred = SAC.from_json_keyfile_name('dndbot_scopes.json', scope)
g_sheets = gspread.authorize(cred)
dnd_sheet = g_sheets.open('DnDTest')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(levelname)s]: %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

class Parser:
	def __init__(self):
		self.characters = {}
		self.damage_quips = [
			'Ouch',
			'That must\'ve hurt',
			'F',
			'Oof',
			'Holy shit',
			'Where\'d they learn to do that',
			'Oh barnacles',
			'Oh fuck',
		]
		self.help_ = {
			'!roll': self.get_embed('Roll', 'Rolls the specified die.', '`!roll [dice]`', ['`!roll d4`','`!roll d12 d20`','`!roll 2xd8`']),
			'!damage': self.get_embed('Damage', 'Damages a specified player with either a dice roll or a determined amount of damage.', '`!damage @<user> <die or damage number>`', ['`!damage @rectrec369 6`','`!damage @rectrec369 d8`']),
			'!heal': self.get_embed('Heal', 'Heals a specified played with either a determined amount or a dice roll.', '`!heal <@user> <die or damage number>', ['`!heal @rectrec369 3`', '`!heal @rectrec369 d8`']),
			'!init': self.get_embed('Initiative', 'Rolls for initiative taking into account the user\'s DEX modifier.', '`!init`', ['`!init`','`!i`']),
			'!i': self.get_embed('Initiative', 'Rolls for initiative taking into account the user\'s DEX modifier.', '`!init`', ['`!init`','`!i`']),
			'!create': self.get_embed('Create', 'Rolls four D6s and removes the lowest value. Used to create new characters.', '`!create`', ['`!create`']),
			'!stat': self.get_embed('Stat', 'Returns the value of the user\'s specified stat.', '`!stat <stat>`', ['`!stat dex`','`!stat str`']),
			'!skill': self.get_embed('Skill','Returns the value of the user\'s specified skill.','`!skill <skill>`',['`!skill stealth`','`!skill perception`']),
			'!xp': self.get_embed('XP','Returns the amount of experience the user has.','`!xp`',['`!xp`']),
			'!addxp': self.get_embed('Add XP','Adds the amount of experience to the user\'s current experience','`!addxp <amount>`',['`!addxp 500`','`!addxp 1250`']),
			'!summary': self.get_embed('Summary','Returns a summary of the current user\'s character','`!summary`',['`!summary`'])

		}

	def parse(self, message):
		""""""
		command, *_ = message.content.lower().split(' ')
		command = command.replace('!', '')
		method = getattr(self, command, self.idiots)
		return method(message)

	def idiots(self, message):
		return discord.File('resources/idiots.gif')

	def roll(self, message):
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

	def damage(self, message):
		msg = message.content.lower()
		user = message.mentions[0]
		_, user_id, *args = msg.split(' ')
		if not args:
			return help_.get('!damage')

		if len(args) == 1 and not args[0].startswith('d'):
			ret = self.deal_damage(user, user_id, args[0])
		else:
			dmg = 0
			for arg in args:
				val = self.roll([arg])
				dmg += val[0] if isinstance(val, tuple) else sum(val)
			ret = self.deal_damage(user, user_id, dmg)
		return ret

	def deal_damage(self, user, user_id, damage):
		username, _ = str(user).split('#')
		log.debug(user)
		user_sheet = dnd_sheet.worksheet(username)
		hp_cell = user_sheet.find('HP')
		existing_wounds = user_sheet.cell(hp_cell.row, hp_cell.col+2).value
		new_wounds = int(existing_wounds) + int(damage)
		user_sheet.update_cell(hp_cell.row, hp_cell.col+2, new_wounds)
		damage_quip = rand.choice(self.damage_quips)
		return f'Damaged {user_id} for {damage}. {damage_quip}!'

	def heal(self, message):
		msg = message.content.lower()
		author = message.author.id
		user = message.mentions[0]
		_, user_id, *args = msg.split(' ')
		if not args:
			return help_.get('!heal')

		if len(args) == 1 and not args[0].startswith('d'):
			ret = self.add_health(author, user, user_id, args[0])
		else:
			health = 0
			for arg in args:
				val = self.roll([arg])
				health += val[0] if isinstance(val, tuple) else sum(val)
			ret = self.add_health(author, user, user_id, health)
		return ret

	def add_health(self, author, user, user_id, health):
		username, _ = str(user).split('#')
		log.debug(user)
		user_sheet = dnd_sheet.worksheet(username)
		hp_cell = user_sheet.find('HP')
		existing_wounds = user_sheet.cell(hp_cell.row, hp_cell.col+2).value
		new_wounds = max((int(existing_wounds) - int(health)), 0)
		user_sheet.update_cell(hp_cell.row, hp_cell.col+2, new_wounds)
		return f'<@{author}> healed {user_id} for {health}.'

	def init(self, message):
		author = message.author
		username, _ = str(author).split('#')
		user_sheet = dnd_sheet.worksheet(username)
		dex_cell = user_sheet.find('DEX')
		dex_mod = int(user_sheet.cell(dex_cell.row, dex_cell.col+2).value)
		init_roll = roll(['d20'])[0]
		return f'<@{author.id}> rolled a {init_roll + dex_mod} for initiative.'

	def create(self, message):
		rolls = roll(['d6','d6','d6','d6'])
		rolls.sort()
		filt = rolls[1:]
		return '<@{author}> rolled {rolls} for a total of {tot}'.format(
			author=message.author.id,
			rolls=str(rolls),
			tot=sum(filt)
		)

	def get_stat(self, message):
		user_sheet = self.get_user_sheet(message)
		_, attr = message.content.upper().split(' ')
		if attr not in ['STR','DEX','CON','INT','WIS','CHA','HP']:
			return 'Not a stat.'
		attr_cell = user_sheet.find(attr)
		attr_value = user_sheet.cell(attr_cell.row, attr_cell.col + 1).value
		return f'<@{message.author.id}> has a {attr} of {attr_value}.'

	def get_skill(self, message):
		user_sheet = self.get_user_sheet(message)
		_, skill = message.content.lower().split(' ')
		skill_list = [cell.value.lower() for cell in user_sheet.range('M2:M40')]
		if skill not in skill_list:
			return 'Not a skill'
		skill_cell = user_sheet.find(skill)
		skill_value = user_sheet.cell(skill_cell.row, skill_cell.col+1).value
		return f'<@{message.author.id}> has a {skill} of {skill_value}.'

	def get_exp(self, message):
		user_sheet = self.get_user_sheet(message)
		exp_cell = user_sheet.find('EXP')
		exp_value = user_sheet.cell(exp_cell.row+1, exp_cell.col).value
		return f'<@{message.author.id}> has {exp_value} exp.'

	def add_exp(self, message):
		_, exp = message.content.lower().split(' ')
		if not exp:
			return help_.get('!addxp')
		exp = int(exp)
		user_sheet = self.get_user_sheet(message)
		exp_cell = user_sheet.find('EXP')
		exp_value = int(user_sheet.cell(exp_cell.row+1, exp_cell.col).value)
		new_exp = exp_value + exp
		user_sheet.update_cell(exp_cell.row+1, exp_cell.col, new_exp)
		return f'<@{message.author.id}> has {new_exp} exp.'

	def save_roll(self, message):
		pass

	def attack_roll(self, message):
		user_sheet = self.get_user_sheet(message)
		# get primary weapon attack
			# get primary weapon attack2
		# roll dice for damage
		pass

	def summary(self, message):
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

	def get_user_sheet(self, message):
		username, _ = str(message.author).split('#')
		user_sheet = dnd_sheet.worksheet(username)
		return user_sheet

	def field(self, message):
		width, height = map(int, message.content.split(' ')[1:])
		# width = int(width)
		# height = int(height)
		img = Img.new('RGB', (width, height), color='green')
		draw = IDraw.Draw(img)
		for i in range(1, width // 10):
			draw.line((i*10, 0, i*10, height), fill='#fff')
		for i in range(1, height // 10):
			draw.line((0, i*10, width, i*10), fill='#fff')
		img.save('resources/field.png', 'PNG')
		field = discord.File('resources/field.png')
		return field

	def get_char(self, message):
		if str(message.author) not in list(self.characters.keys()):
				log.debug('Character not loaded before.')
				self.characters[str(message.author)] = self.get_character(message)
				return str(self.characters.get(str(message.author)))
		else:
			log.debug('Character loaded already.')
			return str(self.characters.get(str(message.author)))

	def get_character(self, message):
		username, _ = str(message.author).split('#')
		user_id = message.author.id
		return Char(user_id, username)

	def get_embed(self, title, desc, usage, examples):
		embed = discord.Embed(
			title=f'**{title}**',
			description=desc,
			colour=discord.Colour.dark_green()
		)

		embed.add_field(name='**> Usage**', value=usage, inline=False)
		embed.add_field(name='**> Examples**', value='\n'.join(examples), inline=False)

		return embed


	

	



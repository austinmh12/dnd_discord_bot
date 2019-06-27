from oauth2client.service_account import ServiceAccountCredentials as SAC
import gspread

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
cred = SAC.from_json_keyfile_name('dndbot_scopes.json', scope)
g_sheets = gspread.authorize(cred)
dnd_sheet = g_sheets.open('DnDTest')

class Character:
	def __init__(self, user_id, username):
		""" Creates a character class with a name and a certain amount of health
		user_id -- str: The discord user's id.
		username -- str: The discord user's name.
		"""
		self.user_id = user_id
		self.username = username
		self.usersheet = dnd_sheet.worksheet(self.username)
		self.get_infos()
		self.get_stats()

	def get_infos(self):
		""" Gets basic character information from the spreadsheet.
		"""
		self.name = self.get_info('Name')
		self.class_ = self.get_info('Class')
		self.race = self.get_info('Race')

	def get_stats(self):
		""" Gets the character's stats from the spreadsheet.
		"""
		self.strength = self.get_stat('STR')
		self.dexterity = self.get_stat('DEX')
		self.constitution = self.get_stat('CON')
		self.intelligence = self.get_stat('INT')
		self.wisdom = self.get_stat('WIS')
		self.charisma = self.get_stat('CHA')
		self.level = self.get_stat('Level')
		self.speed = self.get_stat('Speed')

	def get_info(self, info):
		""""""
		info_cell = self.usersheet.find(info)
		return self.usersheet.cell(info_cell.row, info_cell.col+1).value

	@property
	def health(self):
		""""""
		health_cell = self.usersheet.find('HP')
		hp = int(self.usersheet.cell(health_cell.row, health_cell.col+3).value)
		return hp

	def get_stat(self, stat):
		""""""
		stat_cell = self.usersheet.find(stat)
		return int(self.usersheet.cell(stat_cell.row, stat_cell.col+1).value)

	@property
	def str_mod(self):
		return self.get_modifier(self.strength)
	
	@property
	def dex_mod(self):
		return self.get_modifier(self.dexterity)

	@property
	def con_mod(self):
		return self.get_modifier(self.constitution)

	@property
	def int_mod(self):
		return self.get_modifier(self.intelligence)

	@property
	def wis_mod(self):
		return self.get_modifier(self.wisdom)

	@property
	def cha_mod(self):
		return self.get_modifier(self.charisma)

	@property
	def fort_save(self):
		fort_cell = self.usersheet.find('Fortitude')
		fort_bonus = sum(map(int, [cell.value for cell in self.usersheet.range(fort_cell.row, fort_cell.col+2, fort_cell.row, fort_cell.col+5)]))
		return fort_bonus + self.str_mod
	
	@property
	def reflex_save(self):
		reflex_cell = self.usersheet.find('Reflex')
		reflex_bonus = sum(map(int, [cell.value for cell in self.usersheet.range(reflex_cell.row, reflex_cell.col+2, reflex_cell.row, reflex_cell.col+5)]))
		return reflex_bonus + self.dex_mod

	@property
	def will_save(self):
		will_cell = self.usersheet.find('Fortitude')
		will_bonus = sum(map(int, [cell.value for cell in self.usersheet.range(will_cell.row, will_cell.col+2, will_cell.row, will_cell.col+5)]))
		return will_bonus + self.con_mod

	def get_modifier(self, stat):
		""""""
		return (stat - 10) // 2



	def __str__(self):
		return f'{self.name}, level {self.level} {self.class_} of <@{self.user_id}>'
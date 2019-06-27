import discord, logging
from oauth2client.service_account import ServiceAccountCredentials as SAC
from PIL import Image as Img, ImageDraw as IDraw
import client_info
from Parser import Parser

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_format = logging.Formatter('[%(levelname)s]: %(message)s')
stream_handler.setFormatter(stream_format)
log.addHandler(stream_handler)

# CLIENT_ID = client_info.info['CLIENT_ID']
# CLIENT_SECRET = client_info.info['CLIENT_SECRET']
TOKEN = client_info.info['TOKEN']

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
	parser = Parser() 
	return parser.parse(message)

client.run(TOKEN)
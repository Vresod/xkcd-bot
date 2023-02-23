import discord
from discord.ext import commands, tasks
import aiohttp
import random
import logging

import extra

# global latest_comic
# latest_comic = extra.get_latest_comic()
logging.basicConfig(level=logging.INFO)
client = commands.Bot()
latest_comic = 0

@client.event
async def on_ready():
	logging.info(f"Signed in as {client.user}")
	check_for_new_comics.start()

@client.slash_command(name="get_comic",description="Retrieves the specified xkcd comic")
async def _get_comic(ctx:discord.ApplicationContext,comic_number:int):
	async with aiohttp.ClientSession() as session: # I personally feel this looks unclean but it does context managers so whatever
		try:
			async with session.get(f"https://xkcd.com/{comic_number}/info.0.json") as r:
				r.raise_for_status()
				comic = await r.json()
		except aiohttp.ClientResponseError:
			await ctx.respond("Comic not found.",ephemeral=True)
			return
	embed = discord.Embed(title=f"xkcd {comic['num']}: {comic['title']}",url=f"https://xkcd.com/{comic_number}")
	image_url = comic['img'][:-4] + "_2x.png"
	embed.set_image(url=image_url)
	embed.set_footer(text=comic['alt'])
	embed.description = f"explained: https://explainxkcd.com/{comic_number}"
	await ctx.respond(embeds=[embed],view=extra.ControlsView())

@client.slash_command(name="get_random_comic",description="Grabs a random comic from the xkcd catalogue")
async def _get_random_comic(ctx:discord.ApplicationContext):
	return await _get_comic(ctx,random.randint(1,latest_comic))

@client.slash_command(name="add_comics_channel",description="Adds a channel to the list of channels that receives comics")
@commands.has_guild_permissions(manage_channels=True)
async def _add_comics_channel(ctx:discord.ApplicationContext,channel:discord.TextChannel):
	if channel.type != discord.ChannelType.text:
		await ctx.respond("Choose a channel that is a text channel.",ephemeral=True)
		return
	with open("guilds.txt","r") as guildsfile: # this whole structure sucks and i wish that i knew a better option
		guilds = set(guildsfile.read().split(",")) # not memory efficent solution to remove duplicates
		guilds.update(str(channel.id))
		guilds = [i for i in guilds if i]
	with open("guilds.txt","w") as guildsfile:
		guildsfile.write(','.join(guilds))
	await ctx.respond(f"{channel.name} will now receive an update when a comic comes out!")
	logging.info(f"Comics channel {channel.id} added")

@client.slash_command(name='remove_comics_channel',description="Removes a channel from the list of channels the receieves comics")
@commands.has_guild_permissions(manage_channels=True)
async def _remove_comics_channel(ctx:discord.ApplicationContext,channel:discord.TextChannel):
	if channel.type != discord.ChannelType.text:
		await ctx.respond("Choose a channel that is a text channel.",ephemeral=True)
		return
	with open("guilds.txt") as guildsfile:
		guilds = list(set(guildsfile.read().split(","))) # mess of parentheses; reader I can assure you i am not trying to write lisp
		try:
			guilds.remove(str(channel.id))
		except ValueError:
			await ctx.respond("That channel already wasn't receiving updates. :(",ephemeral=True)
			return
	with open("guilds.txt","w") as guildsfile:
		guildsfile.write(','.join(guilds))
	await ctx.respond(f"{channel.name} will no longer receive an update when a comic comes out. :(")

@tasks.loop(minutes=30)
async def check_for_new_comics():
	async with aiohttp.ClientSession() as session:
		async with session.get("https://xkcd.com/info.0.json") as r:
			r.raise_for_status()
			comic = await r.json()
	global latest_comic
	if comic['num'] > latest_comic:
		latest_comic = comic['num']
		await post_new_comics(comic)
		return True

async def post_new_comics(comic):
	with open("guilds.txt","r") as guildsfile:
		guilds = [int(i) for i in guildsfile.read().split(",")]
	embed = discord.Embed(title=f"xkcd {comic['num']}: {comic['title']}",url=f"https://xkcd.com/{comic['num']}") # average
	image_url = comic['img'][:-4] + "_2x.png"
	embed.set_image(url=image_url)
	embed.set_footer(text=comic['alt'])
	embed.description = f"explained: https://explainxkcd.com/{comic['num']}"
	for guild in guilds:
		channel = await client.fetch_channel(guild)
		await channel.send(embed=embed)

def main():
	import dotenv
	with open("guilds.txt","a"): pass # simply ensure the file exists
	values = dotenv.dotenv_values(".env")
	global latest_comic
	latest_comic = extra.get_latest_comic()
	client.run(values['TOKEN'])

if __name__ == "__main__":
	main()

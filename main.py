from os import name
import discord
from discord.ext import commands, tasks
from discord_slash import SlashContext, SlashCommand
import aiohttp
import logging
import xml.etree.ElementTree as ET

from extra import get_latest_comic

logging.basicConfig(level=logging.INFO)
client = commands.Bot(" ")
slash = SlashCommand(client,sync_commands=True)
latest_comic = 0

@client.event
async def on_ready():
	logging.info(f"Signed in as {client.user}")
	check_for_new_comics.start()

@slash.slash(name="get_comic")
async def _get_comic(ctx:SlashContext,comic_number:int):
	async with aiohttp.ClientSession() as session: # I personally feel this looks unclean but it does context managers so whatever
		try:
			async with session.get(f"https://xkcd.com/{comic_number}/info.0.json") as r:
				r.raise_for_status()
				comic = await r.json()
		except aiohttp.ClientResponseError:
			await ctx.send("Comic not found.",hidden=True)
			return
	embed = discord.Embed(title=f"xkcd {comic['num']}: {comic['title']}",url=f"https://xkcd.com/{comic_number}")
	embed.set_image(url=comic['img'])
	embed.set_footer(text=comic['alt'])
	embed.description = f"explained: https://explainxkcd.com/{comic_number}"
	await ctx.send(embeds=[embed])

@slash.slash(name="add_comics_channel")
@commands.has_guild_permissions(manage_channels=True)
async def _add_comics_channel(ctx:SlashContext,channel:discord.TextChannel):
	if channel.type != discord.ChannelType.text:
		await ctx.send("Choose a channel that is a text channel.",hidden=True)
		return
	with open("guilds.txt","r") as guildsfile: # this whole structure sucks and i wish that i knew a better option
		guilds = list(set(guildsfile.read().split(","))) # not memory efficent solution to remove duplicates
		guilds.append(str(channel.id))
		guilds = [i for i in guilds if i]
	with open("guilds.txt","w") as guildsfile:
		guildsfile.write(','.join(guilds))
	await ctx.send(f"{channel.name} will now receive an update when a comic comes out!")
	logging.info(f"Comics channel {channel.id} added")

@slash.slash(name='remove_comics_channel')
@commands.has_guild_permissions(manage_channels=True)
async def _remove_comics_channel(ctx:SlashContext,channel:discord.TextChannel):
	if channel.type != discord.ChannelType.text:
		await ctx.send("Choose a channel that is a text channel.",hidden=True)
		return
	with open("guilds.txt") as guildsfile:
		guilds = list(set(guildsfile.read().split(","))) # mess of parentheses; reader I can assure you i am not trying to write lisp
		try:
			guilds.remove(str(channel.id))
		except ValueError: 
			await ctx.send("That channel already wasn't receiving updates. :(",hidden=True)
	with open("guilds.txt","w") as guildsfile:
		guildsfile.write(','.join(guilds))
	await ctx.send(f"{channel.name} will no longer receive an update when a comic comes out. :(")

@tasks.loop(hours=2)
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
		guilds = guildsfile.read().split(",")
	embed = discord.Embed(title=f"xkcd {comic['num']}: {comic['title']}",url=f"https://xkcd.com/{comic['num']}") # average 
	embed.set_image(url=comic['img'])
	embed.set_footer(text=comic['alt'])
	embed.description = f"explained: https://explainxkcd.com/{comic['num']}"
	for guild in guilds:
		channel:discord.abc.GuildChannel = await client.fetch_channel(guild)
		await channel.send(embed=embed)

def main():
	import dotenv
	with open("guilds.txt","a"): pass # simply ensure the file exists
	values = dotenv.dotenv_values(".env")
	global latest_comic
	latest_comic = get_latest_comic()
	client.run(values['TOKEN'])

if __name__ == "__main__":
	main()
# import aiohttp
import requests
import aiohttp
from discord import Embed, ui, Interaction, Button
from functools import cache

def get_latest_comic() -> int:
	r = requests.get("https://xkcd.com/info.0.json").json()
	return r['num']
@cache
def generate_embed(num,title,img_url,alt) -> Embed:
	embed = Embed(title=f"xkcd {num}: {title}",url=f"https://xkcd.com/{num}")
	embed.set_image(url=img_url)
	embed.set_footer(text=alt)
	embed.description = f"explained: https://explainxkcd.com/{num}"
	return embed

class ControlsView(ui.View):
	def __init__(self):
		super().__init__(timeout=None)
	
	@ui.button(label="< Prev")
	async def _previous(self,button:Button,interaction:Interaction):
		embed:Embed = interaction.message.embeds[0]
		new_comic_number = int(embed.title.split(":")[0].replace("xkcd ","")) - 1
		async with aiohttp.ClientSession() as session: # I personally feel this looks unclean but it does context managers so whatever
			try:
				async with session.get(f"https://xkcd.com/{new_comic_number}/info.0.json") as r:
					r.raise_for_status()
					comic = await r.json()
			except aiohttp.ClientResponseError:
				return
		embed = generate_embed(comic['num'],comic['title'],comic['img'],comic['alt'])
		await interaction.message.edit(embeds=[embed])
	
	@ui.button(label="Next >")
	async def _next(self,button:Button,interaction:Interaction):
		embed:Embed = interaction.message.embeds[0]
		new_comic_number = int(embed.title.split(":")[0].replace("xkcd ","")) + 1
		async with aiohttp.ClientSession() as session: # I personally feel this looks unclean but it does context managers so whatever
			try:
				async with session.get(f"https://xkcd.com/{new_comic_number}/info.0.json") as r:
					r.raise_for_status()
					comic = await r.json()
			except aiohttp.ClientResponseError:
				return
		embed = generate_embed(comic['num'],comic['title'],comic['img'],comic['alt'])
		await interaction.message.edit(embeds=[embed])

# class ForwardButton(ui.Button):
# 	async def callback(self, interaction: Interaction):
# 		embed:Embed = interaction.message.embeds[0]
# 		comic_number = 
# 		await interaction.edit_original_message(embeds=[embed])
# 		return await super().callback(interaction)
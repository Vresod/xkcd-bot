import aiohttp
import requests

def get_latest_comic() -> int:
	r = requests.get("https://xkcd.com/info.0.json").json()
	return r['num']
import asyncio
import time

import aiohttp
import discord
import requests



async def check_for_updates(queue: asyncio.Queue):
    last_version = None

    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.oref.org.il/WarningMessages/History/AlertsHistory.json') as response:
                new_content = await response.text()

                if last_version is None or new_content != last_version:
                    await queue.put(new_content)
                    last_version = new_content

        await asyncio.sleep(10)

queue = asyncio.Queue()

asyncio.run(check_for_updates(queue))

while True:
    if not queue.empty():
        print(queue.get())
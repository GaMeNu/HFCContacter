import asyncio
import datetime
import json
import logging
import os
import threading
import time
import dotenv
import queue

import aiohttp
import discord
from discord.ext import commands, tasks
import requests


class Alert:
    def __init__(self, time: datetime.datetime, title: str, data: str, category: int, migun_time: int = None):
        self.time = time
        self.title = title
        self.data = data
        self.category = category
        self.migun_time: int | None = migun_time

    def __eq__(self, other):
        if self.time != other.time:
            return False
        if self.title != other.title:
            return False
        if self.data != other.data:
            return False
        if self.category != other.category:
            return False
        return True

    def __str__(self):
        ret_str = f'*{self.time}*\n__{self.title}__ ב**{self.data}**'
        if self.migun_time != None:
            ret_str += f'\nזמן מיגון: {self.migun_time} seconds'

        return ret_str

    def add_migun_time(self, migun_time: int):
        self.migun_time = migun_time

    @staticmethod
    def parse_date(alert_date: str) -> datetime.datetime:
        split = alert_date.split(' ')
        date = split[0].split('-')
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])

        time = split[1].split(':')
        hour = int(time[0])
        minute = int(time[1])
        second = int(time[2])

        ret = datetime.datetime(year, month, day, hour, minute, second)
        return ret

    @staticmethod
    def fromdata(data: dict):
        return Alert(Alert.parse_date(data['alertDate']), data['title'], data['data'], data['category'])


last_version = None

districts: list[dict] =json.loads(requests.get('https://www.oref.org.il//Shared/Ajax/GetDistricts.aspx').text)


def get_district(name: str) -> dict | None:
    for district in districts:
        if district["label"] == name:
            return district
    return None

@tasks.loop(seconds=5)
async def check_for_updates(queue: queue.Queue, logger: logging.Logger):
    global last_version

    response = requests.get('https://www.oref.org.il/WarningMessages/History/AlertsHistory.json')

    logger.debug(f'sent update with response {response}')

    new_content = response.text
    alert_raw_list: list = json.loads(new_content)
    first_alert_raw = alert_raw_list[0]
    first_alert = Alert.fromdata(first_alert_raw)

    if last_version is None:
        last_version = first_alert

    if first_alert != last_version:
        print(last_version)
        last_version = first_alert

        datetime = Alert.parse_date(first_alert_raw['alertDate'])
        alert_list = [first_alert]
        alert_raw_list = alert_raw_list[1::]

        for alert in alert_raw_list:
            current_datetime = Alert.parse_date(alert['alertDate'])
            if not (datetime.minute == current_datetime.minute and
                    datetime.hour == current_datetime.hour and
                    datetime.day == current_datetime.day and
                    datetime.month == current_datetime.month and
                    datetime.year == current_datetime.year):
                break
            alert = Alert.fromdata(alert)
            district = get_district(alert.data)
            migun_time = None
            if district != None:
                migun_time = district.get('migun_time')
                alert.add_migun_time(migun_time)
            alert_list.append(alert)

        ret_str = ''

        for alert in alert_list:
            ret_str += alert.__str__()
            ret_str += '\n\n\n'

        gen_log.info(f'Sending notifs')

        for channel_id in channels:
            channel = bot.get_channel(channel_id)
            if channel is None:
                continue
            await channel.send(ret_str)
            await asyncio.sleep(0.01)



bot = commands.Bot('!', intents=discord.Intents.all())
tree = bot.tree
channels: list[int]


@tree.command(name='register', description='Register a channel for notifications (run in channel to be registered)')
async def register_channel(intr: discord.Interaction):
    global channels
    channel_id = intr.channel_id

    with open('channels.json', 'r+') as channel_file:
        # TODO: yes this is bad, if this becomes a problem I'll fix it
        channels_loc = json.loads(channel_file.read())

        with open('channels_backup.json', 'w') as backup:
            backup.write(json.dumps(channels_loc))

    if channel_id in channels_loc:
        await intr.response.send_message('Channel already registered.')
        return

    channels_loc.append(channel_id)

    with open('channels.json', 'w') as channel_file:
        channel_file.write(json.dumps(channels_loc))

    channels = channels_loc

    await intr.response.send_message(f'Registered channel #{intr.channel} successfully.')

@tree.command(name='unregister', description='Unregister channel from notifications')
async def unregister_channel(intr: discord.Interaction):
    global channels
    channel_id = intr.channel_id

    with open('channels.json', 'r+') as channel_file:
        # TODO: yes this is bad, if this becomes a problem I'll fix it
        channels_loc: list = json.loads(channel_file.read())

        with open('channels_backup.json', 'w') as backup:
            backup.write(json.dumps(channels_loc))

    if channel_id not in channels_loc:
        await intr.response.send_message('Channel not yet registered.')
        return

    channels_loc.remove(channel_id)

    with open('channels.json', 'w') as channel_file:
        channel_file.write(json.dumps(channels_loc))

    channels = channels_loc

    await intr.response.send_message(f'Registered channel #{intr.channel} successfully.')

@tree.command(name='latest', description='Get 10 latest alerts')
async def latest_alert(intr: discord.Interaction):
    response = requests.get('https://www.oref.org.il/WarningMessages/History/AlertsHistory.json')
    alerts_ls: list = json.loads(response.text)
    trimmed = alerts_ls[:10]
    ret_str = ''
    for alert_data in trimmed:
        ret_str += Alert.fromdata(alert_data).__str__()
        ret_str +='\n\n\n'

    await intr.response.send_message(ret_str)

@tree.command(name='about', description='About the bot')
async def about_bot(intr: discord.Interaction):
    e = discord.Embed(color=discord.Color.red())
    e.title = 'Home Front Command Notificator'
    e.description = 'Made by GaMeNu and yrrad8'
    e.add_field(name='Important:', value='This bot is UNOFFICIAL!\nplease refer to the official Home Front Command website at https://www.oref.org.il/', inline=False)
    e.add_field(name='', value='We made this bot to help notify people of incoming missile alerts', inline=False)
    e.add_field(name='Source Code:', value='https://github.com/GaMeNu/HFCContacter')
    e.add_field(name='Feedback', value='Please DM suggestions and bug reports to @gamenu on Discord')
    await intr.response.send_message(embed=e)

@bot.event
async def on_message(msg: discord.Message):
    # Special command to sync messages
    if msg.content == '/sync_cmds' and msg.author.id == AUTHOR_ID:
        print('syncing')
        await msg.reply('Syncing...', delete_after=3)
        await tree.sync()
        print('synced')
        await msg.reply('Synced!', delete_after=3)


@bot.event
async def on_ready():
    global channels
    with open('channels.json', 'r') as channel_file:
        channels = json.loads(channel_file.read())

    notif_logger = logging.Logger('NotifTask')
    notif_logger.addHandler(handler)
    check_for_updates.start(queue, notif_logger)






dotenv.load_dotenv()
queue = queue.Queue()
handler = logging.StreamHandler()
gen_log = logging.Logger('GeneralLog')
gen_log.addHandler(handler)

update_thread = threading.Thread(target=check_for_updates, args=[queue, handler])
update_thread.start()
AUTHOR_ID = int(os.getenv('AUTHOR_ID'))
bot.run(os.getenv('TOKEN'), log_handler=handler)

# HomeFrontCommand notificator bot
## Made by GaMeNu and yrrad8

We made a bot to notify whenever an attack/missile strike/terrorist infiltration happens in Israel.
This bot requests the latest alarm history from the [HFC website](https://www.oref.org.il) and pushes a notification whenever it notices a change.

> Please note that the bot may **not always be up to date**! Please follow the official [HFC website](https://www.oref.org.il) at https://www.oref.org.il for the latest and most up-to-date info and alerts.

## Self-hosting

Sync bot commands by typing `/sync_cmds`  (requires you to be bot author)

### .env format
```env
TOKEN = <BOT TOKEN>
AUTHOR_ID = <YOUR DISCORD USER ID>
```

Invite link for the version of the bot I'm hosting (Note: may be used for testing of new builds):
https://discord.com/api/oauth2/authorize?client_id=1160344131067977738&permissions=0&scope=applications.commands%20bot
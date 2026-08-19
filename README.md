# ikembubot

A Telegram bot that automatically deletes messages containing links, unless
the sender is a group admin. Any group owner can use it by adding the bot
to their own group.

## Group admin commands

Once the bot is admin in a group, any admin of that group can type these
directly in the group chat:

- /toggle - turns link-deleting ON or OFF for that group (starts ON)
- /whitelist add youtube.com - allow links from that domain
- /whitelist remove youtube.com - remove it again
- /whitelist list - show all allowed domains for that group

Each group's settings are separate and saved automatically in a file
called settings.json (created the first time the bot sees a group).

## Notes

- Zero-cost: Termux + Telegram's free Bot API + a free GitHub repo.
- Only deletes text/caption messages with links, not links hidden in images.
- settings.json has no secrets in it and is safe to commit to GitHub.

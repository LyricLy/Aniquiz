# Stateless anime quiz bot

import asyncio
import socket
import traceback
import random
from collections import defaultdict

import anilist
import mal

import aiohttp
import discord
from discord.ext import commands


bot = commands.Bot(command_prefix="q!")
bot.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(family=socket.AF_INET))
bot.games = {}

modules = {
    "mal": mal,
    "anilist": anilist
}

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MaxConcurrencyReached):
        await ctx.send("That command is already in use on this guild.")
    elif isinstance(error, (commands.CommandNotFound, commands.MissingRequiredArgument)):
        pass
    else:
        print(f"Ignoring exception in command {ctx.command.name}")
        traceback.print_exception(type(error), error, error.__traceback__)


class Pick:
    def pick(self):
        raise NotImplementedError()

class FlatPick(Pick):
    def pick(self):
        return random.choice(self.list)

    def __iter__(self):
        return iter(self.list)

class SumPick(FlatPick):
    def __init__(self, lists):
        self.list = sum(lists, start=[])

class IntersectPick(FlatPick):
    def __init__(self, lists):
        self.list = list(set.intersection(*map(set, lists)))

class EqualPick(Pick):
    def __init__(self, lists):
        self.list = sum(lists, start=[])
        self.lists = lists
        self.i = len(lists)

    def pick(self):
        if self.i >= len(self.lists):
            self.i = 0
            random.shuffle(self.lists)
        c = random.choice(self.lists[self.i])
        self.i += 1
        return c

    def __iter__(self):
        return iter(self.list)


JOINERS = {
    "&": IntersectPick,
    "|": SumPick,
    "=": EqualPick
}


@commands.max_concurrency(1, commands.BucketType.guild)
@bot.command()
async def quiz(ctx, joiner, *, lists):
    try:
        pool = JOINERS[joiner]
    except KeyError:
        return await ctx.send("Invalid joiner. Use `&` or `|`.")

    try:
        anime = pool([await modules[(t := elem.split(":"))[0]].anime_list(bot.session, t[1]) for elem in lists.split()])
    except ValueError:
        return await ctx.send("Parse error with provided lists.")
    except KeyError as e:
        return await ctx.send(f"`{e.args[0]}` is an invalid or unsupported anime list. Please use of: {', '.join(modules)}")

    try:
        client = await ctx.author.voice.channel.connect()
    except AttributeError:
        return await ctx.send("Please join a voice channel to play.")

    players = defaultdict(int)

    bot.games[ctx.guild] = game = {
        "anime": anime,
        "client": client,
        "players": players
    }

    already_picked = set()

    try:
        while ctx.guild in bot.games:
            while True:
                picked_anime = anime.pick()

                async with bot.session.get(f"https://themes.moe/api/seasons/{picked_anime.year}") as resp:
                    data = await resp.json(content_type='text/plain')

                anime_data = max(data, key=lambda s: picked_anime.match(s["name"]))
                theme = random.choice(anime_data["themes"])
                url = theme["mirror"]["mirrorURL"]
                if url not in already_picked:
                    already_picked.add(url)
                    break

            game["current"] = picked_anime, theme
            game["guessed"] = False

            source = discord.FFmpegPCMAudio(url)
            done = asyncio.Event()
            client.play(source, after=lambda e: done.set())
            await done.wait()

            if not game["guessed"]:
                await ctx.send(f'No-one got it! This was "{theme["themeName"]}", from *{picked_anime.name}* ({theme["themeType"]}).')
    finally:
        await client.disconnect()

@bot.command()
async def skip(ctx):
    if ctx.guild not in bot.games:
        return await ctx.send("Nothing's happening. Go away.")

    await ctx.send("Anyone else for skipping, say I.")
    try:
        await bot.wait_for("message", check=lambda m: m.content.lower() == "i", timeout=10)
    except asyncio.TimeoutError:
        pass
    else:
        bot.games[ctx.guild]["client"].stop()

@bot.command()
async def guess(ctx, *, title):
    if ctx.guild not in bot.games:
        return await ctx.send("Nothing's happening. Go away.")
    game = bot.games[ctx.guild]
    anime, theme = game["current"]

    match = max(game["anime"], key=lambda a: a.match(title))
    if match == anime:
        game["guessed"] = True
        del game["current"]
        await ctx.send(f'Yup! This is "{theme["themeName"]}", from *{anime.name}* ({theme["themeType"]}).')
        game["players"][ctx.author] += 1
        if game["players"][ctx.author] == 5:
            await ctx.send(f"{ctx.author} wins! GG!")
            bot.games.pop(ctx.guild)
        game["client"].stop()
    else:
        await ctx.send(f"It's not *{match.name}*.")


with open("token.txt") as f:
    bot.run(f.read().strip())

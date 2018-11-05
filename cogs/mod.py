'''
MIT License

Copyright (c) 2017 Grok

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord
from discord.ext import commands
from urllib.parse import urlparse
import datetime
import asyncio
import random
import pip
import os
import io
import json


class Mod:

    def __init__(self, bot):
        self.bot = bot

    async def format_mod_embed(self, ctx, user, success, method, duration = None, location=None):
        '''Helper func to format an embed to prevent extra code'''
        emb = discord.Embed(timestamp=ctx.message.created_at)
        emb.set_author(name=method.title(), icon_url=user.avatar_url)
        emb.color = await ctx.get_dominant_color(user.avatar_url)
        emb.set_footer(text=f'User ID: {user.id}')
        if success:
            if method == 'ban' or method == 'hackban':
                emb.description = f'{user} was just {method}ned.'
            elif method == 'unmute':
                emb.description = f'{user} was just {method}d.'
            elif method == 'mute':
                emb.description = f'{user} was just {method}d for {duration}.'
            elif method == 'channel-lockdown' or method == 'server-lockdown':
                emb.description = f'`{location.name}` is now in lockdown mode!'
            else:
                emb.description = f'{user} was just {method}ed.'
        else:
            if method == 'lockdown' or 'channel-lockdown':
                emb.description = f"You do not have the permissions to {method} `{location.name}`."
            else:
                emb.description = f"You do not have the permissions to {method} {user.name}."
        
        with open('data/config.json') as f:
            config = json.load(f)
            modlog = os.environ.get('MODLOG') or config.get('MODLOG')
        if modlog is None:
            await ctx.send('You have not set `MODLOG` in your config vars.', delete_after=5)
        else:
            modlog = discord.utils.get(self.bot.get_all_channels(), id=int(modlog))
            if modlog is None:
                await ctx.send('Your `MODLOG` channel ID is invalid.', delete_after=5)
            else:
                await modlog.send(embed=emb)
            
        return emb

    @commands.command()
    async def kick(self, ctx, member : discord.Member, *, reason='Please write a reason!'):
        '''Kick someone from the server.'''
        try:
            await ctx.guild.kick(member, reason=reason)
        except:
            success = False
        else:
            success = True

        emb = await self.format_mod_embed(ctx, member, success, 'kick')

        await ctx.send(embed=emb)

    @commands.command()
    async def ban(self, ctx, member : discord.Member, *, reason='Please write a reason!'):
        '''Ban someone from the server.'''
        try:
            await ctx.guild.ban(member, reason=reason)
        except:
            success = False
        else:
            success = True

        emb = await self.format_mod_embed(ctx, member, success, 'ban')

        await ctx.send(embed=emb)

    @commands.command()
    async def unban(self, ctx, name_or_id, *, reason=None):
        '''Unban someone from the server.'''
        ban = await ctx.get_ban(name_or_id)

        try:
            await ctx.guild.unban(ban.user, reason=reason)
        except:
            success = False
        else:
            success = True
        
        emb = await self.format_mod_embed(ctx, ban.user, success, 'unban')

        await ctx.send(embed=emb)

    @commands.command(aliases=['del','p','prune'])
    async def purge(self, ctx, limit : int, member:discord.Member=None):
        '''Clean a number of messages'''
        if member is None:
            await ctx.purge(limit=limit+1)
        else:
            async for message in ctx.channel.history(limit=limit+1):
                if message.author is member:
                    await message.delete()

    @commands.command()
    async def clean(self, ctx, quantity: int):
        ''' Clean a number of your own messages
        Usage: {prefix}clean 5 '''
        if quantity <= 15:
            total = quantity +1
            async for message in ctx.channel.history(limit=total):
                if message.author == ctx.author:
                    await message.delete()
                    await asyncio.sleep(3.0)
        else:
            async for message in ctx.channel.history(limit=6):
                if message.author == ctx.author:
                    await message.delete()
                    await asyncio.sleep(3.0)

    @commands.command()
    async def bans(self, ctx):
        '''See a list of banned users in the guild'''
        try:
            bans = await ctx.guild.bans()
        except:
            return await ctx.send('You dont have the perms to see bans.')

        em = discord.Embed(title=f'List of Banned Members ({len(bans)}):')
        em.description = ', '.join([str(b.user) for b in bans])
        em.color = await ctx.get_dominant_color(ctx.guild.icon_url)

        await ctx.send(embed=em)

    @commands.command()
    async def baninfo(self, ctx, *, name_or_id):
        '''Check the reason of a ban from the audit logs.'''
        ban = await ctx.get_ban(name_or_id)
        em = discord.Embed()
        em.color = await ctx.get_dominant_color(ban.user.avatar_url)
        em.set_author(name=str(ban.user), icon_url=ban.user.avatar_url)
        em.add_field(name='Reason', value=ban.reason or 'None')
        em.set_thumbnail(url=ban.user.avatar_url)
        em.set_footer(text=f'User ID: {ban.user.id}')

        await ctx.send(embed=em)

    @commands.command()
    async def addrole(self, ctx, member: discord.Member, *, rolename: str):
        '''Add a role to someone else.'''
        role = discord.utils.find(lambda m: rolename.lower() in m.name.lower(), ctx.message.guild.roles)
        if not role:
            return await ctx.send('That role does not exist.')
        try:
            await member.add_roles(role)
            await ctx.send(f'Added: `{role.name}`')
        except:
            await ctx.send("I don't have the perms to add that role.")


    @commands.command()
    async def removerole(self, ctx, member: discord.Member, *, rolename: str):
        '''Remove a role from someone else.'''
        role = discord.utils.find(lambda m: rolename.lower() in m.name.lower(), ctx.message.guild.roles)
        if not role:
            return await ctx.send('That role does not exist.')
        try:
            await member.remove_roles(role)
            await ctx.send(f'Removed: `{role.name}`')
        except:
            await ctx.send("I don't have the perms to add that role.")

    @commands.command()
    async def hackban(self, ctx, userid, *, reason=None):
        '''Ban someone not in the server'''
        try:
            userid = int(userid)
        except:
            await ctx.send('Invalid ID!')
        
        try:
            await ctx.guild.ban(discord.Object(userid), reason=reason)
        except:
            success = False
        else:
            success = True

        if success:
            async for entry in ctx.guild.audit_logs(limit=1, user=ctx.guild.me, action=discord.AuditLogAction.ban):
                emb = await self.format_mod_embed(ctx, entry.target, success, 'hackban')
        else:
            emb = await self.format_mod_embed(ctx, userid, success, 'hackban')
        await ctx.send(embed=emb)

    @commands.command()
    async def mute(self, ctx, member:discord.Member, duration, *, reason=None):
        '''Denies someone from chatting in all text channels and talking in voice channels for a specified duration'''
        unit = duration[-1]
        if unit == 's':
            time = int(duration[:-1])
            longunit = 'seconds'
        elif unit == 'm':
            time = int(duration[:-1]) * 60
            longunit = 'minutes'
        elif unit == 'h':
            time = int(duration[:-1]) * 60 * 60
            longunit = 'hours'
        else:
            await ctx.send('Invalid Unit! Use `s`, `m`, or `h`.')
            return

        progress = await ctx.send('Muting user!')
        try:
            for channel in ctx.guild.text_channels:
                await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(send_messages = False), reason=reason)

            for channel in ctx.guild.voice_channels:
                await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(speak=False), reason=reason)
        except:
            success = False
        else:
            success = True

        emb = await self.format_mod_embed(ctx, member, success, 'mute', f'{str(duration[:-1])} {longunit}')
        progress.delete()
        await ctx.send(embed=emb)
        await asyncio.sleep(time)
        try:
            for channel in ctx.guild.channels:
                await channel.set_permissions(member, overwrite=None, reason=reason)
        except:
            pass
        
    @commands.command()
    async def unmute(self, ctx, member:discord.Member, *, reason=None):
        '''Removes channel overrides for specified member'''
        progress = await ctx.send('Unmuting user!')
        try:
            for channel in ctx.message.guild.channels:
                await channel.set_permissions(member, overwrite=None, reason=reason)
        except:
            success = False
        else:
            success = True
            
        emb = await self.format_mod_embed(ctx, member, success, 'unmute')
        progress.delete()
        await ctx.send(embed=emb)

    @commands.group(invoke_without_command=True)
    async def lockdown(self, ctx):
        """Server/Channel lockdown"""
        pass

    @lockdown.command(aliases=['channel'])
    async def chan(self, ctx, channel:discord.TextChannel = None, *, reason=None):
        if channel is None: channel = ctx.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages = False), reason=reason)
        except:
            success = False
        else:
            success = True
        emb = await self.format_mod_embed(ctx, ctx.author, success, 'channel-lockdown', 0, channel)
        await ctx.send(embed=emb)
    
    @lockdown.command()
    async def server(self, ctx, server:discord.Guild = None, *, reason=None):
        if server is None: server = ctx.guild
        progress = await ctx.send(f'Locking down {server.name}')
        try:
            for channel in server.channels:
                await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(send_messages = False), reason=reason)
        except:
            success = False
        else:
            success = True
        emb = await self.format_mod_embed(ctx, ctx.author, success, 'server-lockdown', 0, server)
        progress.delete()
        await ctx.send(embed=emb)
	
	@client.event
async def on_ready():
    print('Logged in...')
    print('Username: ' + str(client.user.name))
    print('Client ID: ' + str(client.user.id))
    print('Invite URL: ' + 'https://discordapp.com/oauth2/authorize?&client_id=' + client.user.id + '&scope=bot&permissions=0')

# Announce the change in voice state through text to speech (ignores mutes/deafens)
@client.event
async def on_voice_state_update(before, after):
    # Ensure bot is connected to voice client (!join has been used)
    if client.is_voice_connected(before.server) == True:
        global player
        previousChannel = before.voice_channel
        newChannel = after.voice_channel

        # Bot only talks when user's channel changes, not on mutes/deafens
        if previousChannel != newChannel:
            # When user joins or moves to bot's channel
            if newChannel == currentChannel:
                tts.createAnnouncement(after.name, 'has joined the channel')

            # When user leaves bot's channel
            elif previousChannel != None and newChannel == None and previousChannel == currentChannel:
                tts.createAnnouncement(after.name, 'has left the channel')

            # When user moves out of bot's channel to a new channel
            elif previousChannel == currentChannel and newChannel != currentChannel:
                tts.createAnnouncement(after.name, 'had moved to another channel')

            # After user joins, leaves or moves, announce the new announcement
            if (newChannel == currentChannel or previousChannel != None and
                newChannel == None and previousChannel == currentChannel or
                previousChannel == currentChannel and newChannel != currentChannel):

                try:
                    if player.is_playing() == False:
                        player = voice.create_ffmpeg_player('announce.mp3')
                        player.start()

                except NameError:
                    player = voice.create_ffmpeg_player('announce.mp3')
                    player.start()

@client.event
async def on_message(message):
    # If the message author isn't the bot and the message starts with the
    # command prefix ('!' by default), check if command was executed
    if message.author.id != config.BOTID and message.content.startswith(config.COMMANDPREFIX):
        # Remove prefix and change to lowercase so commands aren't case-sensitive
        message.content = message.content[1:].lower()

        # Shuts the bot down - only usable by the bot owner specified in config
        if message.content.startswith('shutdown') and message.author.id == config.OWNERID:
            await client.send_message(message.channel, 'Shutting down. Bye!')
            await client.logout()
            await client.close()

        # Allows owner to set the game status of the bot
        elif message.content.startswith('status') and message.author.id == config.OWNERID:
            await client.change_presence(game=discord.Game(name=message.content[7:]))

        # Help Message, sends a personal message with a list of all the commands
        # and how to use them correctly
        elif message.content.startswith('help'):
            await client.send_message(message.channel, 'Sending you a PM!')
            await client.send_message(message.author, helpMessage.helpMessage)

        # Sends a personal message with the invite link of the bot
        elif message.content.startswith('invite'):
            await client.send_message(message.channel, 'Sending you a PM!')
            await client.send_message(message.author, 'Invite URL: ' + 'https://discordapp.com/oauth2/authorize?&client_id=' + client.user.id + '&scope=bot&permissions=0')

        # Searches the second word following pythonhelp in python docs
        elif message.content.startswith('pythonhelp'):
            messagetext = message.content
            split = messagetext.split(' ')
            if len(split) > 1:
                messagetext = split[1]
                await client.send_message(message.channel, 'https://docs.python.org/3/search.html?q=' + messagetext)

        # Messages a random chuck norris joke - do not use, they're bloody terrible
        elif message.content.startswith('joke'):
            chuckJoke = requests.get('http://api.icndb.com/jokes/random?')
            if chuckJoke.status_code == 200:
                chuckJoke = chuckJoke.json()['value']['joke']
                await client.send_message(message.channel, chuckJoke)

        # Random 8 Ball message
        elif message.content.startswith('8ball'):
            await client.send_message(message.channel, rng.getEightBall())

        # Random coin flip
        elif message.content.startswith('coinflip'):
            await client.send_message(message.channel, rng.getCoinFace())

        elif message.content.startswith('roll'):
            await client.send_message(message.channel, rng.rollDice(message.content))

        # Slots machine in emoji format for discord
        elif message.content.startswith('slots'):
            await client.send_message(message.channel, rng.getSlotsScreen())

        # Random cat gif
        elif message.content.startswith('catgif'):
            await client.send_message(message.channel, cats.getCatGif())

        # Random cat picture
        elif message.content.startswith('cat'):
            await client.send_message(message.channel, cats.getCatPicture())

        # Messages link to a random Simpsons clip
        elif message.content.startswith('simpsonsclip'):
            await client.send_message(message.channel, cartoons.getSimpsonsVideo())

        # Searches for a Simpsons quote and sends the full quote with accompanying picture
        elif message.content.startswith('simpsonsquote'):
            await client.send_message(message.channel, cartoons.findSimpsonsQuote(message.content))

        # Messages a random Simpsons quote with accompanying picture
        elif message.content.startswith('simpsons'):
            await client.send_message(message.channel, cartoons.getSimpsonsQuote())

        # Messages Boo-urns
        elif message.content.startswith('boo'):
            await client.send_message(message.channel, cartoons.booUrns())

        # Searches for a Futurama quote and sends the full quote with accompanying picture
        elif message.content.startswith('futuramaquote'):
            await client.send_message(message.channel, cartoons.findFuturamaQuote(message.content))

        # Messages a random Futurama quote with accompanying picture
        elif message.content.startswith('futurama'):
            await client.send_message(message.channel, cartoons.getFuturamaQuote())

        # Messages a random XKCD comic
        elif message.content.startswith('xkcd'):
            await client.send_message(message.channel, cartoons.getXkcdComic())

        # Heroes of the Storm - Hots Logs - Messages MMR of playerID and Hots logs link
        elif message.content.startswith('hots'):
            await client.send_message(message.channel, hots.getHotsStats(message.content))

        # Takes following words as search arguments and messages information of gwent card
        elif message.content.startswith('gwent'):
            await client.send_message(message.channel, gwent.cardSearch(message.content))

        ########## VOICE COMMANDS ##########

        # Will join the voice channel of the message author if they're in a channel
        # and the bot is not currently connected to a voice channel
        elif message.content.startswith('join'):
            if message.author.voice_channel != None and client.is_voice_connected(message.server) != True:
                global currentChannel
                global player
                global voice
                currentChannel = client.get_channel(message.author.voice_channel.id)
                voice = await client.join_voice_channel(currentChannel)

            elif message.author.voice_channel == None:
                await client.send_message(message.channel, 'You are not in a voice channel.')

            else:
                await client.send_message(message.channel, 'I am already in a voice channel. Use !leave to make me leave.')

        # Will leave the current voice channel
        elif message.content.startswith('leave'):
            if client.is_voice_connected(message.server):
                currentChannel = client.voice_client_in(message.server)
                await currentChannel.disconnect()

        # Will play music using the following words as search parameters or use the
        # linked video if a link is provided
        elif message.content.startswith('play'):
            if message.author.voice_channel != None:
                if client.is_voice_connected(message.server) == True:
                    try:
                        if player.is_playing() == False:
                            print('not playing')
                            player = await voice.create_ytdl_player(youtubeLink.getYoutubeLink(message.content))
                            player.start()
                            await client.send_message(message.channel, ':musical_note: Currently Playing: ' + player.title)

                        else:
                            print('is playing')

                    except NameError:
                        print('name error')
                        player = await voice.create_ytdl_player(youtubeLink.getYoutubeLink(message.content))
                        player.start()
                        await client.send_message(message.channel, ':musical_note: Currently Playing: ' + player.title)

                else:
                    await client.send_message(message.channel, 'I am not connected to a voice channel. Use !join to make me join')

            else:
                await client.send_message(message.channel, 'You are not connected to a voice channel. Enter a voice channel and use !join first.')

        # Will pause the audio player
        elif message.content.startswith('pause'):
            try:
                player.pause()

            except NameError:
                await client.send_message(message.channel, 'Not currently playing audio.')

        # Will resume the audio player
        elif message.content.startswith('resume'):
            try:
                player.resume()

            except NameError:
                await client.send_message(message.channel, 'Not currently playing audio.')

        # Will stop the audio player
        elif message.content.startswith('stop'):
            try:
                player.stop()

            except NameError:
                await client.send_message(message.channel, 'Not currently playing audio.')



def setup(bot):
	bot.add_cog(Mod(bot))

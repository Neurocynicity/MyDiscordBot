import discord
from discord import app_commands

import os
from dotenv import load_dotenv
from pathlib import Path

import Settings
import TimeParser
import DrawPromptGenerator
from UserTimeZoneManager import SetUserTimeZone, GetUserTimeZone, GetAllUsersAndTimeZones
from FriendCodeManager import SetFriendCodeOfUser, GetFriendCodeOfUser
from Activities import MakeCreateActivityMesesage, DeleteActivityByVoiceChannel
from GDPR import MakeGDPRMessage
from Utility import DebugPrint

# more imports below getting magic numbers

DebugMode = Settings.GetIsDebugMode()
SoundBoardActive = Settings.GetIsSoundboardActive()
FILE_PATH_SEPERATOR = Settings.GetFilePathSeperator()

# loading magic numbers from a .env file

pathToEnvFile = str(Path(__file__).parent.resolve()) + FILE_PATH_SEPERATOR + "EnvironmentVariables.env"
load_dotenv(pathToEnvFile)

TOKEN = os.getenv('TOKEN')
BOT_ID = int(os.getenv('BOT_ID'))
MY_ID = int(os.getenv('MY_ID'))

# this is the ID of a guild (discord server) which I can safely test the bot in
# this one will give every member access to every command and will be synced only to
# this server and not others
PRIVATE_GUILD_ID = int(os.getenv('PRIVATE_GUILD_ID'))

if SoundBoardActive:
    import SoundBoard

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

#region Friend Codes

@tree.command(name = "addfc", description = "Adds your friend code so people can get it later", )
async def SetFriendCode(ctx, friendcode : str):
   
    SetFriendCodeOfUser(ctx.user.id, friendcode)
    await ctx.response.send_message("Set friend code to: " + str(GetFriendCodeOfUser(ctx.user.id)))

@tree.command(name = "getfc", description = "gets someone's friend code", )
async def GetFriendCode(ctx, member : discord.Member):
   
    userFriendCode = GetFriendCodeOfUser(member.id)
    if userFriendCode is None:
        await ctx.response.send_message(member.name + " has no friend code listed!")
    else:
        await ctx.response.send_message(member.name + "'s friend code is: " + userFriendCode)

#endregion

#region Set Time Zones

@tree.command(name = "settimezone", description = "Sets your local time zone", )
async def SetTimeZone(ctx, timezonestring : str):
   
    if SetUserTimeZone(ctx.user.id, timezonestring):
        await ctx.response.send_message("Set time zone to: " + str(GetUserTimeZone(ctx.user.id)), ephemeral=True)
    else:
        await ctx.response.send_message("Couldn't find time zone in: " + timezonestring, ephemeral=True)


## Admin set time zone command
@tree.command(name = "settimezoneadmin", description = "Sets someone else's local time zone", )
async def SetTimeZoneAdmin(ctx : discord.Interaction, member : discord.Member,  timezonestring : str):

    if ctx.user.id != MY_ID:
        print(ctx.user.name + " Tried to use the admin command...")
        await ctx.response.send_message('You must be the owner to use this command!\nPlease use /settimezone instead', ephemeral=True)
        return
   
    if SetUserTimeZone(member.id, timezonestring):
        await ctx.response.send_message("Set " + member.name + "'s time zone to: " + str(GetUserTimeZone(member.id)), ephemeral=True)
    else:
        await ctx.response.send_message("Couldn't find time zone in: " + timezonestring, ephemeral=True)

#endregion

#region Draw Prompt and Say

@tree.command(name = "drawprompt", description = "gives you a random prompt to draw", )
async def GenerateDrawPrompt(ctx):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalidInteraction(ctx):
        return
    
    prompt = DrawPromptGenerator.GenerateDrawPrompt()
   
    await ctx.response.send_message(prompt)

@tree.command(name = "say", description = "The bot will say your message!", )
async def Say(ctx, stringtosay : str):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalidInteraction(ctx):
        return
    
    await ctx.response.send_message(stringtosay)

#endregion

#region Time Zone Stuff

@tree.command(name = "localtime", description = "Displays the current time in the user's timezone", )
async def CheckLocalTime(ctx, member: discord.Member):
    
    responseStr = member.name + "'s local time is "
    userTimeZone = GetUserTimeZone(member.id)

    if userTimeZone is None:
        await ctx.response.send_message(member.name + " has no time zone set")
        return

    responseStr = responseStr + TimeParser.GetLocalTimeForTimeZone(userTimeZone)
    await ctx.response.send_message(responseStr)

@tree.command(name = "converttime", description = "Shows the inputted time in localtime for each user", )
async def ConvertToAllLocalTimes(ctx : discord.Interaction, timestr : str, member : discord.Member=None):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalidInteraction(ctx):
        return
    
    if member != None:
        userMember = member
    else:
        userMember = ctx.user

    memberID = userMember.id

    userTimeZone = GetUserTimeZone(memberID)
    timesInMessage = TimeParser.GetTimesInMessage(timestr, userTimeZone)

    if len(timesInMessage) == 0:
        await ctx.response.send_message("No time found in time string!", ephemeral=True)

    matchInMessage = timesInMessage[0]
    timeInMessage = matchInMessage[1]

    usersAndTimeZones = GetAllUsersAndTimeZones()

    channelUserIDsAndTimeZones = {}

    channel = ctx.channel

    isThread = False

    try:
        channel.flags.value
        isThread = True

        DebugPrint("THREAD FOUND!!!")
    except:
        DebugPrint("Not in thread")
        

    if isThread:
        membersInChannel = await channel.fetch_members()

        for i in range(len(membersInChannel)):
            membersInChannel[i] = client.get_user(membersInChannel[i].id)

    else:
        membersInChannel = channel.members
        
    # only add users in this channel
    for user in membersInChannel:
        userIDstr = str(user.id)
        
        if (userIDstr not in usersAndTimeZones):
            continue

        channelUserIDsAndTimeZones[userIDstr] = usersAndTimeZones[userIDstr]

    UTCOffsetsAndPeople = {}

    for userIDstr in channelUserIDsAndTimeZones:
        utcOffset = timeInMessage.astimezone(GetUserTimeZone(userIDstr)).strftime('%z')

        if utcOffset not in UTCOffsetsAndPeople:
            UTCOffsetsAndPeople[utcOffset] = []
        
        UTCOffsetsAndPeople[utcOffset].append(userIDstr)

    DebugPrint(UTCOffsetsAndPeople)       

    responseStr = matchInMessage[0] + " for " + userMember.name + " is:"

    for utcOffset in UTCOffsetsAndPeople:

        timeInUTCOffset = timeInMessage.astimezone(GetUserTimeZone(UTCOffsetsAndPeople[utcOffset][0]))

        formattedTimeInTimeZone = timeInUTCOffset.strftime("%B %d, %H:%M")
        responseStr = responseStr + "\n" + formattedTimeInTimeZone + " for "

        for userIDstr in UTCOffsetsAndPeople[utcOffset]:
            userFromID : discord.user = await client.fetch_user(userIDstr)
            responseStr = responseStr + userFromID.name + " "
    
    await ctx.response.send_message(responseStr)

#endregion

#region SoundBoard

@tree.command(name = "soundboard", description = "Makes a new soundboard message!", )
async def CreateSoundboardMessage(ctx):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalidInteraction(ctx) or not SoundBoardActive:
        return
    
    await SoundBoard.CreateSoundboardMessage(ctx)

@tree.command(name = "soundboardadd", description = "adds a new sound to the soundboard!", )
async def SoundboardAdd(ctx, emojii : str, soundstr : str):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalidInteraction(ctx) or not SoundBoardActive:
        return
    
    await SoundBoard.AddSoundboardSound(ctx, emojii, soundstr)
    
@tree.command(name = "soundboardplay", description = "instantly plays a sound", )
async def SoundboardPlay(ctx, soundstr : str):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalidInteraction(ctx) or not SoundBoardActive:
        return

    await SoundBoard.PlaySound(ctx, soundstr)

@client.event
async def on_reaction_add(reaction : discord.Reaction, user):

    # boilerplate to disable unknown users using commands
    if IsCommandInvalid(user, reaction.message.guild.id, False) or not SoundBoardActive:
        return
    
    # ignore reactions to any messages done by others
    if reaction.message.author.id != BOT_ID or user.id == BOT_ID:
        DebugPrint("Ignoring reaction")
        return
    
    await SoundBoard.TryPlaySound(reaction, user)

#endregion

#region VC and Activity creation

@tree.command(name = "createactivitychannel", description = "Sends the message so this channel can be used for activities", )
async def CreateAnActivityChannel(ctx : discord.Interaction):

    if IsCommandInvalidInteraction(ctx):
        print(ctx.user.name + " doesn't have access to using /createactivitychannel")
        await ctx.response.send_message('You must be an admin to use this command!', ephemeral=True)
        return
    
    return await MakeCreateActivityMesesage(ctx)

@client.event
async def on_voice_state_update(member, before : discord.VoiceState, after : discord.VoiceState):
    if before.channel != None and len(before.channel.members) == 0 and after.channel != before.channel:
        await DeleteActivityByVoiceChannel(before.channel)
    
#endregion

#region On Message event
messageCount = 5

@client.event
async def on_message(message : discord.Message):

    if message.author.id == BOT_ID:
        return

    if '_' in message.content:
        return
    
    if "bad bot" in message.content.lower():

           async for previousMessage in message.channel.history(limit=messageCount):
               
               await message.add_reaction("😢")

               if previousMessage.author.id == BOT_ID:
                   await previousMessage.delete()
                   break
               
    if "good bot" in message.content.lower() or "🫳" in message.content:
        await message.add_reaction("😺")

    userTimeZone = GetUserTimeZone(message.author.id)

    if userTimeZone is None:
        return

    response = TimeParser.ReplaceTimesInStringWithTimeStamps(message.content, userTimeZone)

    DebugPrint("There's a message: \"" + message.content + "\"\nResponse \"" + response + '"')

    if response != message.content:
        await message.channel.send(response)

#endregion

#region Syncing

@tree.command(name='sync', description='Owner only (command for nerds)')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == MY_ID:
        await tree.sync(guild=discord.Object(id=PRIVATE_GUILD_ID))
        print('Command tree synced in private server.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!', ephemeral=True)

@tree.command(name='syncglobal', description='Owner only (command for nerds)')
async def syncglobal(interaction: discord.Interaction):
    if interaction.user.id == MY_ID:
        await tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!', ephemeral=True)

#endregion

#region GDPR

@tree.command(name='gdpr', description='See all information the bot has about you, and gives the option to delete it all')
async def gdpr(interaction: discord.Interaction):
    return await MakeGDPRMessage(interaction)

#endregion

#region command validating

# @tree.command(name = "test", description = "Jester uses this to test", )
# async def Test(ctx):
#     await ctx.response.send_message(str(ctx.user.id))

def IsCommandInvalidInteraction(interaction: discord.Interaction):
    return IsCommandInvalid(interaction.user, interaction.guild_id)

def IsCommandInvalid(user, guild_id, debugIfInvalid=True):
    
    if user is discord.User:
        return False

    # the command is valid if we have the time guardian role
    for role in user.roles:
        if role.id == 1183491900750188654:
            return False

    # otherwise it's invalid if it's coming from the sploon server
    if guild_id == 1182417466803109908:
        if debugIfInvalid:
            print("INVALID COMMAND USED")
        return True

    return False

#endregion

@client.event
async def on_ready():
    print("Getting ready...")

    if SoundBoardActive:
        SoundBoard.SetupSoundboard(client)
        print("Soundboard set up!")
    
    print("Ready!")

print("Running client...")
client.run(TOKEN)
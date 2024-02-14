import json
import os
import pathlib
import discord
import subprocess
from pytube import YouTube
from Settings import GetFilePathSeperator

import re

FILE_PATH_SEPERATOR = GetFilePathSeperator()

pathToSoundsFolder = str(pathlib.Path(__file__).parent.resolve()) + FILE_PATH_SEPERATOR + "SoundboardSounds" + FILE_PATH_SEPERATOR
pathToFile = str(pathlib.Path(__file__).parent.resolve()) + FILE_PATH_SEPERATOR + "SoundboardSounds.txt"

client : discord.Client = None

soundboardDictionary = {}

def FillSoundBoardDictionary():
    with open(pathToFile) as f:
        data = f.read()

    if data == "":
        return

    global soundboardDictionary
    soundboardDictionary = json.loads(data)

def SaveDictionaryToFile():
    with open(pathToFile, "w") as textFile:
        textFile.write(json.dumps(soundboardDictionary))

def SetupSoundboard(_client):
    global client

    client = _client

    FillSoundBoardDictionary()

async def CreateSoundboardMessage(ctx : discord.Interaction):
    
    soundboardMessage = await SendMessageAndReturnIt(ctx, "Soundboard Message!")

    for emojii in soundboardDictionary:
        await soundboardMessage.add_reaction(client.get_emoji(int(emojii)))

async def SendMessageAndReturnIt(ctx, messageContent) -> discord.Message:
    await ctx.response.send_message(messageContent)

    # we just sent the message, now we have to find it... yippee
    async for message in ctx.channel.history(limit=5):

        if message.content == messageContent:
            return message
            
async def AddSoundboardSound(ctx, triggerEmojii, sound):

    # to get the emojii name we have to do some regex because discord won't 
    # let me have an emojii parameter
    possibleMatch = re.search(":\d+>", triggerEmojii)

    if possibleMatch is None:
        print(f"No ID found in string {triggerEmojii}")
        await ctx.response.send_message("Invalid Emojii!")
        return
    
    # now we have the string ID of the emojii
    emojiiId = possibleMatch.group().strip(":>") # :> smiley!!!
    # print(f"Emojii ID: {emojiiId}")

    # now we check if it's a youtube url and download it if it is
    possibleMatch = re.search("youtu\.{0,1}be", sound)

    if possibleMatch != None:
        print("Youtube url found!")

        try:
            video = YouTube(sound)
        except:
            print("Invalid Youtube link!")
            await ctx.response.send_message("Invalid Youtube link!")
            return

        sentMessage = await SendMessageAndReturnIt(ctx, "Downloading!  This might take time, I'll react to this message once it's done!")

        sound = video.streams.filter(only_audio=True).first().download(pathToSoundsFolder)

        # now we want to open the file and remove the silence from the beginning
        RemoveSilence(sound)
    
    soundboardDictionary[emojiiId] = sound
    SaveDictionaryToFile()

    print("Finished Adding!!")

    if possibleMatch != None:
        await sentMessage.add_reaction("👍")
    else:
        await ctx.response.send_message("Added to soundboard!")

# the reaction version (ignore user not being used for now, fix later)
async def TryPlaySound(reaction : discord.Reaction, user):

    userGuild = reaction.message.guild

    # first we should check whether there's a sound associated with the reaction emojii
    # we're converting it into a string because when reading it from a json file it gets stringified
    reactionEmojiiName = str(reaction.emoji.id)

    print(soundboardDictionary)

    if reactionEmojiiName not in soundboardDictionary:
        print(f"WARNING: No sound with trigger {reactionEmojiiName} found in soundboardDictionary")
        return
    
    soundToPlayStr = soundboardDictionary[reactionEmojiiName]

    await EnsureJoinedVC(userGuild)
    voiceClient = discord.utils.get(client.voice_clients, guild=userGuild)

    source : discord.AudioSource = discord.FFmpegOpusAudio(soundToPlayStr)
    voiceClient.stop()
    voiceClient.play(source)

# to kill eventually when no longer slash command
async def PlaySound(ctx : discord.Interaction, soundstr : str):
    
    await EnsureJoinedVC(ctx.guild)
    voiceClient = discord.utils.get(client.voice_clients, guild=ctx.guild)

    source : discord.AudioSource = discord.FFmpegOpusAudio(soundstr)
    voiceClient.stop()
    voiceClient.play(source)

    await ctx.response.send_message("Wahuu'd")

async def EnsureJoinedVC(userGuild : discord.Guild):
    
    # we should check if we're connected to a voice channel, and connect to one if we're not
    voiceClient = discord.utils.get(client.voice_clients, guild=userGuild)

    # if we're connected we leave
    if voiceClient != None:
        return

    if len(userGuild.voice_channels) == 0:
        return # ctx.response.send_message("No Voice Channels found!")

    maxUsersInChannel = -1
    for voiceChannel in userGuild.voice_channels:

        if len(voiceChannel.members) > maxUsersInChannel:
            maxUsersInChannel = voiceChannel.members
            connectVoiceChannel = voiceChannel
   
    await connectVoiceChannel.connect(timeout=60, self_deaf=True)

def RemoveSilence(filePath : str):

    editedFilePath = re.sub("\.", " UNEDITED.", filePath, 1)

    os.rename(filePath, editedFilePath)

    subprocessCommands = [
        "ffmpeg",
        "-i",
        editedFilePath,
        "-af",
        "silenceremove=stop_periods=1:0:-50dB",
        filePath
    ]

    if subprocess.run(subprocessCommands).returncode == 0:
        os.remove(editedFilePath)
        print("Audio Trimmed successfully!")
    else:
        print(f"Error handling ffmpeg command: {' '.join(subprocessCommands)}")
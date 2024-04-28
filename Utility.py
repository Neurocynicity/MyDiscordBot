import discord
import requests
from Settings import DebuggingMode

def GetImagesInMessage(message : discord.Message) -> list:
    
    foundImages = []

    for attachment in message.attachments:

        if "image" in attachment.content_type:
            foundImages.append(attachment.url)
    
    for embed in message.embeds:

        if embed.image:
            foundImages.append(embed.image.url)
    
    return foundImages

def SaveMessageFromURL(url : str) -> bool:

    with open('lastImage.jpg', 'wb') as handle:
        response = requests.get(url, stream=True)

        if not response.ok:
            print(response)
            return False

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)

    return True

def DebugPrint(string : str):
    if (DebuggingMode):
        print(string)

class ButtonDynamic(discord.ui.View):

    func : callable = None

    def __init__(self, *, timeout=180, function : callable = None):
        global func
        super().__init__(timeout=timeout)
        func = function
    
    @discord.ui.button(label="Button",style=discord.ButtonStyle.blurple)
    async def OnPress(self, interaction : discord.Interaction, button : discord.ui.Button):

        return await func(interaction)
    
class Button(discord.ui.View):

    func : callable = None

    def __init__(self, *, timeout=180, function : callable = None):
        global func
        super().__init__(timeout=timeout)
        func = function
    
    @discord.ui.button(label="Button",style=discord.ButtonStyle.blurple)
    async def OnPress(self, interaction : discord.Interaction, button : discord.ui.Button):
        return await func
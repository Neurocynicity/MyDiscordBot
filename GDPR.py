import discord
from UserTimeZoneManager import GetUserTimeZone, RemoveUsersTimeZone
from FriendCodeManager import GetFriendCodeOfUser, RemoveUserFriendCode

async def MakeGDPRMessage(interaction : discord.Interaction):
    messageText : str = ""
    userTimeZone = GetUserTimeZone(interaction.user.id)
    userFriendCode = GetFriendCodeOfUser(interaction.user.id)

    if userTimeZone is not None:
        messageText += f"Your time zone is: {str(userTimeZone)}\n"
    
    if userFriendCode is not None:
        messageText += f"Your friend code is: {str(userFriendCode)}\n"

    if messageText == "":
        return await interaction.response.send_message("The bot has no information about you!\nTo use its features you can use `/settimeone` for automatic time zone conversion or `/setfc` so people can get your friend code!", ephemeral=True)

    deleteButton = DeleteDataButton()
    return await interaction.response.send_message("Here's the information the bot has stored about you:\n" + messageText, view=deleteButton, ephemeral=True)

class DeleteDataButton(discord.ui.View):

    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="Delete all data",style=discord.ButtonStyle.red)
    async def OnPress(self, ctx : discord.Interaction, button : discord.ui.Button):
        RemoveUserFriendCode(ctx.user.id)
        RemoveUsersTimeZone(ctx.user.id) 
        
        return await ctx.response.send_message("Deleted all data stored on you!", ephemeral=True)
import discord

activities : dict = {}


async def DeleteActivityOfUser(user : discord.Member):
    if user.id in activities:
        await activities[user.id].CloseActivity()

async def DeleteActivityByVoiceChannel(channel : discord.VoiceChannel):
    for key in activities:
        if activities[key].createdVC == channel:
            await activities[key].CloseActivity()
            break

async def MakeCreateActivityMesesage(ctx : discord.Interaction):
    buttonView = CreateActivityButton()
    return await ctx.response.send_message("Press the button to start an activity in the server!", view=buttonView)

class CreateActivityButton(discord.ui.View):

    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="Create new Activity",style=discord.ButtonStyle.blurple)
    async def OnPress(self, ctx : discord.Interaction, button : discord.ui.Button):
        modal = CreateActivityModal()
        return await ctx.response.send_modal(modal)

class Activity:

    async def Initialise(self, creationCtx : discord.Interaction =None, activityName : str = None):
        self.creationCtx = creationCtx
        self.activityName = activityName

        self.createdVC = await self.creationCtx.guild.create_voice_channel(str(self.activityName), category=creationCtx.channel.category)

        if self.creationCtx.user.voice != None:
            await self.creationCtx.user.move_to(self.createdVC)

        self.CreateMessage()
        
        activityMessageView = ActivityMessageView(activity=self)
        await self.creationCtx.response.send_message(self.messageText, view = activityMessageView)

    def CreateMessage(self):
        createdVCChannelLink = f'https://discord.com/channels/{self.creationCtx.guild.id}/{self.createdVC.id}'
        self.messageText = f'{self.creationCtx.user.mention} is currently: {self.activityName}\nJoin here: {createdVCChannelLink}'

    async def EditName(self, buttonCtx : discord.Interaction, newName : str):

        if len(self.createdVC.members) > 0 and buttonCtx.user not in self.createdVC.members:
            await buttonCtx.response.send_message("You don't have access to deleting this activity", ephemeral=True)
            return
    
        self.activityName = newName
        await self.createdVC.edit(name=str(self.activityName))
        
        self.CreateMessage()
        
        activityMessageView = ActivityMessageView(activity=self)
        await self.creationCtx.edit_original_response(content=self.messageText, view = activityMessageView)
        await buttonCtx.response.send_message("activity edited!", ephemeral=True)
    
    async def CloseActivityButton(self, buttonCtx : discord.Interaction):
        if len(self.createdVC.members) > 0 and buttonCtx.user not in self.createdVC.members:
            await buttonCtx.response.send_message("You don't have access to deleting this activity", ephemeral=True)
            return
        
        await self.CloseActivity()

    async def CloseActivity(self):
        activities.pop(self.creationCtx.user.id)
        await self.createdVC.delete()
        await self.creationCtx.delete_original_response()
        

class CreateActivityModal(discord.ui.Modal, title='Create Activity!'):

    activityName = discord.ui.TextInput(label='What are you doing?')

    async def on_submit(self, ctx: discord.Interaction):
        activity = Activity()
        await DeleteActivityOfUser(ctx.user)
        activities[ctx.user.id] = activity
        await activity.Initialise(creationCtx=ctx, activityName=self.activityName)

class ActivityMessageView(discord.ui.View):

    def __init__(self, *, timeout=180, activity : Activity):
        super().__init__(timeout=timeout)
        self.activity = activity

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.green)
    async def Edit(self, ctx : discord.Interaction, button : discord.ui.Button):
        modal = EditActivityModal()
        modal.initialise(activity=self.activity)
        return await ctx.response.send_modal(modal)
    
    @discord.ui.button(label="Finish", style=discord.ButtonStyle.red)
    async def Finish(self, ctx : discord.Interaction, button : discord.ui.Button):
        return await self.activity.CloseActivityButton(buttonCtx=ctx)

class EditActivityModal(discord.ui.Modal, title='Edit your Activity!'):
    activityName = discord.ui.TextInput(label='What are you doing?')
    # answer = discord.ui.TextInput(label='Answer', style=discord.TextStyle.paragraph)

    def initialise(self, activity : Activity = None):
        self.activity = activity

    async def on_submit(self, ctx: discord.Interaction):
        await self.activity.EditName(buttonCtx=ctx, newName=self.activityName)


async def EditActivityChannel(ctx : discord.Interaction, createdChannel : discord.VoiceChannel, creationChannel : discord.TextChannel, creationMessage : str):
    
    if len(createdChannel.members) > 0 and ctx.user not in createdChannel.members:
        await ctx.response.send_message("You don't have access to deleting this activity", ephemeral=True)
        return
    
    await createdChannel.delete()

    message : discord.Message

    async for message in creationChannel.history(limit=5):
        if message.content == creationMessage:
            responseMessage = message

    await responseMessage.delete()
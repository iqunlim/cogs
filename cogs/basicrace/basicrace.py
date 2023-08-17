from redbot.core import commands
from datetime import datetime, timedelta
import asyncio
from .race.race import Race
from typing import Dict


class basicrace(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        #both of these dicts could be combined. I could go Dict[str, (Race, datetime)]
        self.raceset: Dict[str, Race] = {} #Contains the race objects and their opened times.
        asyncio.get_event_loop().create_task(self.__checkfordeletion()) #Fire the garbage collection up and lets get to checkin'
        
    def __raceexists(self, name) -> bool:
        if name in self.raceset.keys():
            return True
        return False
    
    def __race(self, channel_id) -> Race:
        return self.raceset[channel_id]
    
    async def countdown(self, ctx: commands.Context, time:int):
        countdownnum = time
        s = self.__race(ctx.channel.id)
        while True:
            if countdownnum == time:
                await ctx.send(f"Countdown started, race beginning in {time} seconds")       
            elif countdownnum > 10 and countdownnum % 10 == 0:
                await ctx.send(f"Race starting in {countdownnum} seconds.")
            elif countdownnum <= 10 and countdownnum >= 1:
                await ctx.send(countdownnum)
            elif countdownnum == 0:
                await ctx.send(s.start())
                break
            else:
                break
            countdownnum -= 1
            await asyncio.sleep(1)
    
    async def __checkfordeletion(self):
        while True:
            for key in self.raceset.keys():
                if (datetime.now().timestamp() - self.raceset[key].opened_at.timestamp()) > 21600:
                    self.raceset[key].stop()
                    self.raceset.pop(key)
                    await self.bot.send_to_owners(f"Race deleted in: {self.raceset[key].serverid}")
            await asyncio.sleep(30 * 60) #Checks every 30 mins.
            
    @commands.command()
    async def startrace(self, ctx: commands.Context, countdown=15, admin="notadmin"):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.created():
                await ctx.send("Race already created. Type !join to join.")
            elif s.inprogress():
                await ctx.send("Race already started. Sorry not sorry.")
            elif s.locked():
                await ctx.send("Race is in locked state. Type !restart to run another race with the same peeps and !restartnew to restart a clean race.")
        else:
            self.raceset[ctx.channel.id] = (Race(ctx.channel.id, ctx.message.guild.id, countdown, True if admin.lower() == "admin" else False), datetime.now())
            await ctx.send("Race created. !join to join and !ready when ready")
        
    @commands.command()
    async def join(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.created():
                await ctx.send(s.join(ctx.author, ctx.author.global_name))
            elif s.inprogress():
                await ctx.send("Race already started")
                
            
    @commands.command()        
    async def unjoin(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.created():
                await ctx.send(s.unjoin(ctx.author, ctx.author.global_name))
            elif s.inprogress():
                await ctx.send("Race already started")
        
    @commands.command()
    async def ready(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.created():
                await ctx.send(s.ready(ctx.author, ctx.author.global_name))
            if False not in s.racers and not s.admin and len(s.racers) >= 2:
                gen = (y.mention for x in s.racers.keys() for y in ctx.guild.members if str(y.name) == str(x))
                await ctx.send(", ".join(gen)) #TODO: Test formatting
                await self.countdown(ctx, s.countdown)
            elif not False in s.racers and s.admin and len(s.racers) >= 2:
                await ctx.send("All racers ready. Admin, hit the !adminstart button!")
            elif not len(s.racers) >= 2:
                await ctx.send("All racers ready, but not enough entrants to start the race!")
       
    @commands.command()
    async def unready(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.created():
                await ctx.send(s.unready(ctx.author, ctx.author.global_name))
            
    @commands.command()
    async def done(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(s.done(ctx.author, ctx.author.global_name))
                if s.locked():
                    await ctx.send(s.stop())
            else:
                await ctx.send("Race not started.")
        
    @commands.command()    
    async def undone(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(s.undone(ctx.author, ctx.author.global_name))
            else:
                await ctx.send("Race not started.")
        
    @commands.command()
    async def quit(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(s.quit(ctx.author, ctx.author.global_name))
                if s.locked():
                    await ctx.send(s.stop())
            else:
                await ctx.send("Race not started.")
        
    @commands.command()
    @commands.admin_or_can_manage_channel()        
    async def adminstart(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.created():
                self.countdown(ctx, s.countdown)
            else:
                await ctx.send("What are you doing admin! The race is already started!")
        else:
            await ctx.send("No race enabled! C'mon admins you should never see this! Type !startrace first!")
        pass
    
    @commands.command()
    async def reset(self, ctx: commands.Context, n=False):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.locked():
                if n:
                    countdown = s.countdown
                    admin = s.admin
                    self.raceset.pop(ctx.channel.id)
                    self.startrace(self, ctx, countdown, admin)
                else:
                    if s.restart():
                        await ctx.send("Race restarted. Type !ready to ready or !unjoin to leave the race.")
                    else:
                        await ctx.send("No race in a state to be restarted. All racers must be finished and the race must exist.")
                        
    @commands.command()                
    async def close(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.locked():
                self.raceset.pop(ctx.channel.id)
                await ctx.send("Race room closed. Type !startrace to re-open.")
            
    @commands.command()
    async def entrants(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if len(s.racers) == 0: 
                await ctx.send("No entrants yet. Type !join to join!")
            #TODO: Some sort of cleaning 
            for x, y in s.racers.items():
                if x in s.finishers:
                    await ctx.send(f'{x}: {s.finishers[x]}')
                else:    
                    await ctx.send(f'{x}: {"Ready" if y else "Not Ready"}')
                    
    @commands.command()
    @commands.admin_or_can_manage_channel()           
    async def forceclose(self, ctx: commands.Context, c='no'):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if c == 'yes':
                self.raceset.pop(ctx.channel.id)
                await ctx.send("Race Forcibly deleted. Type !startrace to restart.")
            else:
                await ctx.send("Race not deleted. Type '!forceclose yes' to force closure of this race.")
            

    @commands.command()
    async def restart_new(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.locked():
                self.restart(self, ctx, n=True)
                
    
    @commands.command() 
    async def list_races(self, ctx: commands.Context):
        if len(self.raceset.keys()) > 0:
            await ctx.send(self.raceset.keys()) #TODO: Clean the formatting here
        else:
            await ctx.send("No Races")
            
    @commands.command()        
    async def time(self, ctx: commands.Context):
        if self.__raceexists(ctx.channel.id):
            s = self.__race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(f"{timedelta(seconds=(datetime.now().timestamp() - s.timer))} has elapsed.")
        
    #TODO: More admin stuff.
             
            
    
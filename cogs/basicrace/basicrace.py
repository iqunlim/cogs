from redbot.core import commands
from datetime import datetime, timedelta
import asyncio
from .race.race import Race
from typing import Dict


#TODO: Formatting on various commands: !entrants, !status, !list_races, the ending dictionary print from race.py
#TODO: Some solutions to above can be found in !ready for getting nicknames out of the string values in races[str, Race]
#TODO: Various other small formatting things. 
#TODO: Command helpers for all commands (!help in redbot)
#TODO: Begin integration with postgres db. setting game on startrace and goal in race.created() state

class basicrace(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.raceset: Dict[str, Race] = {}
        asyncio.get_event_loop().create_task(self.__checkfordeletion()) #Fire the garbage collection up and lets get to checkin'
        
    def raceexists(self, name) -> bool:
        if name in self.raceset.keys():
            return True
        return False
    
    def race(self, channel_id) -> Race:
        try:
            return self.raceset[channel_id]
        except KeyError:
            return None
    
    async def countdown(self, ctx: commands.Context, time: int):
        countdownnum = time
        s = self.race(ctx.channel.id)
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
            elif countdownnum < 0:
                break
            countdownnum -= 1
            await asyncio.sleep(1)
    
    async def __checkfordeletion(self):
        while True:
            for key in self.raceset.keys():
                s =  self.raceset[key]
                if ((datetime.now().timestamp() - s.opened_at.timestamp()) > 21600) and s.locked():
                    self.raceset.pop(key)
                    await self.bot.send_to_owners(f"Race deleted in: {s.serverid}")
                elif ((datetime.now().timestamp() - s.opened_at.timestamp()) > 3600) and s.created():
                    self.raceset.pop(key)
                    await self.bot.send_to_ownwers(f"Race never started in: {s.serverid}")
                elif ((datetime.now().timestamp() - s.opened_at.timestamp()) > 86400) and s.inprogress():
                    self.raceset.pop(key)
                    await self.bot.send_to_owners(f"Race never finished in: {s.serverid}")
            await asyncio.sleep(30 * 60) #Checks every 30 mins.
            
    @commands.command()
    async def startrace(self, ctx: commands.Context, countdown=15, admin="notadmin"):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.created():
                await ctx.send("Race already created. Type !join to join.")
            elif s.inprogress():
                await ctx.send("Race already started. Sorry not sorry.")
            elif s.locked():
                await ctx.send("Race is in locked state. Type !restart to run another race with the same peeps and !restartnew to restart a clean race.")
        else:
            self.raceset[ctx.channel.id] = Race(ctx.channel.id, ctx.message.guild.id, countdown, True if admin.lower() == "admin" else False)
            await ctx.send("Race created. !join to join and !ready when ready")
        
    @commands.command()
    async def join(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.created():
                await ctx.send(s.join(ctx.author, ctx.author.global_name))
            elif s.inprogress():
                await ctx.send("Race already started")
                
            
    @commands.command()        
    async def unjoin(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.created():
                await ctx.send(s.unjoin(ctx.author, ctx.author.global_name))
            elif s.inprogress():
                await ctx.send("Race already started")
        
    @commands.command()
    async def ready(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.created():
                await ctx.send(s.ready(ctx.author, ctx.author.global_name))
            readies = [x for x in self.race(ctx.channel.id).racers.values() if x == True]
            if len(readies) == len(s.racers) and not s.admin and len(s.racers) >= 2:
                await ctx.send(", ".join((y.mention for x in s.racers.keys() for y in ctx.guild.members if str(y.name) == str(x))))
                await self.countdown(ctx, s.countdown)
            elif len(readies) == len(s.racers) and s.admin and len(s.racers) >= 2:
                await ctx.send("All racers ready. Admin, hit the !adminstart button!")
            elif not len(s.racers) >= 2:
                await ctx.send("All racers ready, but not enough entrants to start the race!")
       
    @commands.command()
    async def unready(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.created():
                await ctx.send(s.unready(ctx.author, ctx.author.global_name))
            
    @commands.command()
    async def done(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(s.done(ctx.author, ctx.author.global_name))
                if s.locked():
                    await ctx.send(s.stop())
            else:
                await ctx.send("Race not started.")
        
    @commands.command()    
    async def undone(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(s.undone(ctx.author, ctx.author.global_name))
            else:
                await ctx.send("Race not started.")
        
    @commands.command()
    async def quit(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(s.quit(ctx.author, ctx.author.global_name))
                if s.locked():
                    await ctx.send(s.stop())
            else:
                await ctx.send("Race not started.")
        
    @commands.command()
    @commands.admin_or_can_manage_channel()        
    async def adminstart(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.created():
                self.countdown(ctx, s.countdown)
            else:
                await ctx.send("What are you doing admin! The race is already started!")
        else:
            await ctx.send("No race enabled! C'mon admins you should never see this! Type !startrace first!")
        pass
    
    @commands.command()
    async def reset(self, ctx: commands.Context, n=False):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
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
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.locked():
                self.raceset.pop(ctx.channel.id)
                await ctx.send("Race room closed. Type !startrace to re-open.")
            
    @commands.command()
    async def entrants(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
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
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if c == 'yes':
                self.raceset.pop(ctx.channel.id)
                await ctx.send("Race Forcibly deleted. Type !startrace to restart.")
            else:
                await ctx.send("Race not deleted. Type '!forceclose yes' to force closure of this race.")
            

    @commands.command()
    async def reset_new(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.locked():
                self.reset(self, ctx, n=True)
                
    
    @commands.command() 
    async def list_races(self, ctx: commands.Context):
        if len(self.raceset.keys()) > 0:
            await ctx.send(self.raceset.keys()) #TODO: Clean the formatting here
        else:
            await ctx.send("No Races")
            
    @commands.command()        
    async def time(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            s = self.race(ctx.channel.id)
            if s.inprogress():
                await ctx.send(f"{timedelta(seconds=round(datetime.now().timestamp() - s.timer))} has elapsed.")
        
    #TODO: More admin stuff.
    @commands.command()
    async def status(self, ctx: commands.Context):
        if self.raceexists(ctx.channel.id):
            if self.race(ctx.channel.id).created():
                await ctx.send("Created")
            if self.race(ctx.channel.id).inprogress():
                await ctx.send("In Progress")
            if self.race(ctx.channel.id).locked():
                await ctx.send("Finished")
        else:
            await ctx.send("Race is not started! Type !startrace to start.")
            
    #Hard debuggers for bot owners only
    @commands.command()
    @commands.is_owner()       
    async def dev_racedict(self, ctx:commands.Context):
        if self.raceexists(ctx.channel.id):
            if len(self.race(ctx.channel.id).racers) > 0:
                for x, y in self.race(ctx.channel.id).racers.items():
                    await ctx.send(f"{x} : {y}")
            else:
                await ctx.send("Nobody in this dict")
        else:
            await ctx.send("No race")
            
    @commands.command()
    @commands.is_owner()       
    async def dev_finishdict(self, ctx:commands.Context):
        if self.raceexists(ctx.channel.id):
            if len(self.race(ctx.channel.id).finishers) > 0:
                for x, y in self.race(ctx.channel.id).finishers.items():
                    await ctx.send(f"{x} : {y}")
            else:
                await ctx.send("Nobody in this dict")
        else:
            await ctx.send("No race")
    
    @commands.command()
    @commands.is_owner()       
    async def dev_getvar(self, ctx:commands.Context, variable='', channel_id=0):
        c = ctx.channel.id if channel_id == 0 else channel_id
        if self.raceexists(c):
            s = self.race(c)
            match variable:
                case 'id':
                    await ctx.send(s.id)                
                case 'serverid':
                    await ctx.send(s.serverid)
                case 'internalid':
                    await ctx.send(s.internalid)
                case 'opened_at':
                    await ctx.send(s.opened_at)                
                case 'admin':
                    await ctx.send(s.admin)
                case 'countdown':
                    await ctx.send(s.countdown)
                case 'timer':
                    await ctx.send(s.timer)                
                case 'started':
                    await ctx.send(s.started)
                case 'stopped':
                    await ctx.send(s.stopped)
        else:
            await ctx.send("No race for this channel.")
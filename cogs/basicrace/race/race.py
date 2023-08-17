from datetime import datetime, timedelta
import random
import string
from typing import Dict

class Race():
    
    def __init__(self, id, serverid, countdown=15, admin=False):
        self.id: int = id
        self.countdown: int = countdown
        self.admin: bool = admin
        self.opened_at:datetime = datetime.now()
        self.timer:float = datetime.now().timestamp()
        self.racers : Dict[str, bool] = {}
        self.finishers : Dict[str, datetime] = {}
        self.started:bool = False
        self.stopped:bool = False
        #A couple of things for future references when I start uploading these races to a db
        self.serverid: int = serverid 
        self.internalid: str = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=12))
        ############
        
    #Some state checkers.
    def created(self):
        if not self.started and not self.stopped:
            return True
        else:
            return False
    
    def inprogress(self):
        if self.started and not self.stopped:
            return True
        else:
            return False
    
    def locked(self):
        #putting this extra or here in case of something terrible. If the 4th state ever happens lock it.
        if (self.started and self.stopped) or (not self.started and self.stopped): 
            return True
        else:
            return False
        
    def isinrace(self, name):
        if name in self.racers.keys(): 
            return True
        return False
    
    def isfinished(self, name):
        if name in self.finishers.keys():
            return True
        return False
     
    #Extra functions for different printing.        
    def __formatdictfordiscord(self, fdict):
        printformat = "`"
        for x, y in fdict.items():
            printformat += f"@{x} : {y}\n"
        printformat += "`"
        return printformat
    
    #The meat & Potatoes.    
    def join(self, author, nick):
        if not self.isinrace(author):
            self.racers[author] = False
            return f"{nick} Joined the race."
        else:
            return "You are already in this race!"
            
    def unjoin(self, author, nick):
        if self.isinrace(author):
            self.racers.pop(author)
            return f"{nick} removed from race."
        else:
            return "You are not in the race!"
            
    def ready(self, author, nick):
        if self.isinrace(author):
            self.racers[author] = True
            return f"{nick} is ready!"
        else:
            return "You are not in the race!"
                    
        
    def unready(self, author, nick):
        if self.isinrace(author):
            self.racers[author] = False 
            return f"{nick} is not ready!"
        else:
            return "You are not in the race!"
            
    def done(self, author, nick):
        if self.isinrace(author) and not self.isfinished(author):
            finish = timedelta(seconds=round(datetime.now().timestamp() - self.timer))
            self.finishers[author] = finish
            if len(self.racers) == len(self.finishers):
                self.stopped = True 
            return f"{nick} Finished in {finish}"
        
    def undone(self, author, nick):
        if self.isfinished(author):
            self.finishers.pop(author)
            return f"{nick} undoned."
            
    def quit(self, author, nick):
        if self.isinrace(author):
            self.finishers[author] = 'DNF'
            if len(self.racers) == len(self.finishers):
                self.stopped = True
            return f"{nick} Dropped from the race"
                
    def start(self):
        self.timer = datetime.now().timestamp()
        self.started = True
        return "GO" 

    def stop(self):
        if self.locked():
            return self.__formatdictfordiscord(self.finishers)
        
    def restart(self):
        if not self.locked(): return False
        else:
            self.stopped = False
            self.started = False
            self.racers.update((x, False) for x in self.racers)
            self.finishers = {}
            return True 
    
        
import time
class CooldownService:
    def __init__(self):
        self.cooldowns={}
    def check(self,user,action,seconds):
        key=(user,action)
        now=time.time()
        last=self.cooldowns.get(key,0)
        if now-last<seconds:
            return False,int(seconds-(now-last))
        self.cooldowns[key]=now
        return True,0

    def clear(self, user, action):
        self.cooldowns.pop((user, action), None)

class FeedbackService:
    def __init__(self):
        self.entries=[]
    def submit(self,user,msg):
        self.entries.append({"user":user,"msg":msg})
        return True
    def all(self):
        return self.entries

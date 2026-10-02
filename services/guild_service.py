class GuildService:
    def __init__(self):
        self.guilds = {}

    def create_guild(self, owner_id, name):
        if name in self.guilds:
            raise ValueError("Guild already exists")
        self.guilds[name] = {"owner": owner_id, "members": [owner_id]}
        return self.guilds[name]

    def join_guild(self, user_id, name):
        if name not in self.guilds:
            raise ValueError("Guild not found")
        self.guilds[name]["members"].append(user_id)
        return self.guilds[name]

    def leave_guild(self, user_id, name):
        if name not in self.guilds:
            raise ValueError("Guild not found")
        self.guilds[name]["members"].remove(user_id)
        return self.guilds[name]

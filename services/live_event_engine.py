class LiveEventEngine:
    def __init__(self):
        self.active_event = None

    def activate(self, name):
        self.active_event = name

    def current(self):
        return self.active_event

    def reward_bonus(self):
        return 2 if self.active_event == "double_rewards" else 1

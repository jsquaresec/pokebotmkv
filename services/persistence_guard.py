class PersistenceGuard:
    def validate(self, data):
        if not data:
            raise ValueError("Invalid save")
        return True

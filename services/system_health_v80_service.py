from services.content_registry_v70 import ContentRegistryV70


class SystemHealthV80Service:
    @staticmethod
    def snapshot(bot=None):
        registry = ContentRegistryV70()
        errors = registry.validate()
        return {"version": "90.0.0", "status": "content-valid" if not errors else "degraded",
                "species": len(registry.all_species()), "content_errors": len(errors),
                "extensions": len(bot.extensions) if bot else None,
                "commands": len(bot.tree.get_commands()) if bot else None}

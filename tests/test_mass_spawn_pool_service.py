from services.mass_spawn_pool_service import MassSpawnPoolService

def run():
    svc = MassSpawnPoolService()
    species = svc.random_species(include_featured_bias=True, week_number=1)
    assert isinstance(species, str)
    assert len(species) > 0
    print("mass spawn pool service tests passed")

if __name__ == "__main__":
    run()

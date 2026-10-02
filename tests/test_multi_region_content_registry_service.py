from services.multi_region_content_registry_service import MultiRegionContentRegistryService

def run():
    svc = MultiRegionContentRegistryService()
    regions = svc.region_names()
    assert "kanto" in regions
    assert "paldea" in regions
    counts = svc.counts()
    assert counts["kanto"] >= 151
    assert counts["johto"] > 0
    assert len(svc.all_species()) > 500
    print("multi region content registry service tests passed")

if __name__ == "__main__":
    run()

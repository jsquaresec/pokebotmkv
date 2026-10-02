from services.featured_rotation_service import FeaturedRotationService

def run():
    svc = FeaturedRotationService()
    key = svc.current_rotation_key(1)
    pool = svc.current_pool(1)
    assert isinstance(key, str)
    assert len(pool) > 0
    print("featured rotation service tests passed")

if __name__ == "__main__":
    run()

from services.transaction_guard_service import TransactionGuardService

class DummyOffer:
    def __init__(self, status="open"):
        self.status = status

def run():
    svc = TransactionGuardService()
    assert svc.ensure_positive_quantity(2) == 2
    try:
        svc.ensure_positive_quantity(0)
        raise AssertionError("Expected quantity failure")
    except ValueError:
        pass
    try:
        svc.ensure_user_exists(None)
        raise AssertionError("Expected user failure")
    except ValueError:
        pass
    svc.ensure_open_offer(DummyOffer("open"))
    try:
        svc.ensure_open_offer(DummyOffer("accepted"))
        raise AssertionError("Expected offer state failure")
    except ValueError:
        pass
    print("transaction guard service tests passed")

if __name__ == "__main__":
    run()

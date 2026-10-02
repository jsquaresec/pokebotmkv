from services.response_formatter_service import ResponseFormatterService

def run():
    svc = ResponseFormatterService()
    assert "✅" in svc.success("ok")
    assert "•" in svc.bullet_lines(["a", "b"])
    print("response formatter service tests passed")

if __name__ == "__main__":
    run()

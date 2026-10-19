from fastapi.testclient import TestClient


def test_index_page(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    html = resp.text
    assert 'name="viewport"' in html
    assert 'id="pay-form"' in html and 'id="debtors"' in html


def test_static_assets(client: TestClient) -> None:
    assert client.get("/static/style.css").status_code == 200
    js = client.get("/static/app.js")
    assert js.status_code == 200
    # O'quvchi select /students dan to'ldiriladi (/debtors dan emas).
    assert 'api("/students")' in js.text


import pytest
from base64 import b64encode
from lomos_api2.lomos_api2 import app, whoami, config_to_dict


def test_config_to_dict():
    resp = config_to_dict(app.config)
    assert "tkn1" == resp["LOMOS_API_USER_API_KEY"]
    # assert "x" == resp["LOMOS_INDEX_NAME"]
    # assert "x" == resp["LOMOS_OPENSEARCH_API_URL"]


class TestWhoami:
    def test_ok(self):
        headers = {
            "Authorization": "Bearer " + b64encode(b"tkn1").decode("utf8"),
        }
        response = app.test_client().get("/auth/whoami", headers=headers)
        assert response.status_code == 200
        assert dict(username="api_user") == response.json

    def test_no_token(self):
        response = app.test_client().get("/auth/whoami")
        assert response.status_code == 401
        assert "Unauthorized" in response.data.decode("utf-8")

    def test_wrong_token(self):
        headers = {
            "Authorization": "Bearer " + b64encode(b"wrong-token").decode("utf8"),
        }
        response = app.test_client().get("/auth/whoami", headers=headers)
        assert response.status_code == 401
        assert "Unauthorized" in response.data.decode("utf-8")


    def test_token_not_base64(self):
        headers = {
            "Authorization": "Bearer token-not-base64",
        }
        response = app.test_client().get("/auth/whoami", headers=headers)
        assert response.status_code == 401
        assert "Unauthorized" in response.data.decode("utf-8")

    # def test_token_not_utf8(self):
    #     headers = {
    #         "Authorization": b"Bearer " + "slavic-cp1250-žč".encode("cp1250"),
    #     }
    #     response = app.test_client().get("/auth/whoami", headers=headers)
    #     assert response.status_code == 401
    #     assert "Unauthorized" in response.data.decode("utf-8")
        

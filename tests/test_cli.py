import json
import tempfile
import unittest
from pathlib import Path

from apifox_endpoint_sync.cli import (
    SyncError,
    load_dotenv,
    validate_allowed_command,
    validate_endpoint_update,
)


class EndpointUpdateValidationTests(unittest.TestCase):
    def valid_payload(self):
        return {
            "method": "GET",
            "path": "/api/admin/users",
            "name": "List users",
            "parameters": [
                {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}}
            ],
            "responses": {"200": {"description": "OK"}},
        }

    def test_accepts_valid_payload(self):
        method, path = validate_endpoint_update(
            self.valid_payload(),
            expected_method="GET",
            expected_path="/api/admin/users",
        )
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/api/admin/users")

    def test_rejects_missing_method(self):
        payload = self.valid_payload()
        payload.pop("method")
        with self.assertRaisesRegex(SyncError, "method"):
            validate_endpoint_update(payload)

    def test_rejects_method_mismatch(self):
        with self.assertRaisesRegex(SyncError, "method mismatch"):
            validate_endpoint_update(self.valid_payload(), expected_method="POST")

    def test_rejects_forbidden_field_nested(self):
        payload = self.valid_payload()
        payload["extensions"] = {"auth": {"type": "bearer"}}
        with self.assertRaisesRegex(SyncError, "Forbidden endpoint field"):
            validate_endpoint_update(payload)

    def test_rejects_public_parameter_name(self):
        payload = self.valid_payload()
        payload["parameters"].append({"name": "Authorization", "in": "header"})
        with self.assertRaisesRegex(SyncError, "Public parameters"):
            validate_endpoint_update(payload)

    def test_allows_response_fields_that_share_public_parameter_names(self):
        payload = self.valid_payload()
        payload["responses"]["200"]["content"] = {
            "application/json": {"example": {"uid": "user_001", "ts": 1710000000}}
        }
        method, path = validate_endpoint_update(payload)
        self.assertEqual((method, path), ("GET", "/api/admin/users"))


class CommandAllowlistTests(unittest.TestCase):
    def test_allows_endpoint_update(self):
        validate_allowed_command(["apifox", "endpoint", "update", "endpoint_123"])

    def test_rejects_import(self):
        with self.assertRaisesRegex(SyncError, "Refusing"):
            validate_allowed_command(["apifox", "import", "openapi.json"])

    def test_rejects_common_parameter(self):
        with self.assertRaisesRegex(SyncError, "Refusing"):
            validate_allowed_command(["apifox", "common-parameter", "update"])


class DotenvTests(unittest.TestCase):
    def test_loads_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "APIFOX_TOKEN=apifox_token_placeholder\nAPIFOX_PROJECT_ID=project_id_placeholder\n",
                encoding="utf-8",
            )
            values = load_dotenv(path)
        self.assertEqual(values["APIFOX_TOKEN"], "apifox_token_placeholder")
        self.assertEqual(values["APIFOX_PROJECT_ID"], "project_id_placeholder")


class ExampleJsonTests(unittest.TestCase):
    def test_example_json_is_valid(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "endpoint-update.example.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        method, api_path = validate_endpoint_update(
            payload,
            expected_method="GET",
            expected_path="/api/admin/users",
        )
        self.assertEqual((method, api_path), ("GET", "/api/admin/users"))


if __name__ == "__main__":
    unittest.main()

"""API contract checks using local graph nodes without external services."""
import os
os.environ["PYTHON_DOTENV_DISABLED"] = "1"

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from src import api, orchestrator

class ApiTests(unittest.TestCase):
    def setUp(self):
        api.get_router.cache_clear()
        self.client = TestClient(api.app)

    def tearDown(self):
        api.get_router.cache_clear()

    def test_health_and_models_do_not_create_router(self):
        with patch.object(api, "get_router") as router:
            self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
            self.assertIn("google", self.client.get("/models").json())
            router.assert_not_called()

    def test_invalid_input(self):
        for payload in (
            {"question": "   "},
            {"question": "test", "model": "unknown"},
            {"question": "test", "session_id": "bad-id"},
        ):
            self.assertEqual(self.client.post("/chat", json=payload).status_code, 422)

    def test_session_history_and_isolation(self):
        histories = []

        def sql_answer(question, provider, history):
            histories.append([message.content for message in history])
            return {"answer": "Test answer"}

        with patch.object(orchestrator.ClefModel, "route_to", return_value="sql_agent"), patch.object(orchestrator, "run_sql_agent", side_effect=sql_answer):
            first = self.client.post("/chat", json={"question": "First"})
            self.assertEqual(first.status_code, 200)
            body = first.json()
            self.assertEqual(body["route"], "sql_agent")
            second = self.client.post("/chat", json={"question": "Follow up", "session_id": body["session_id"]})
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.json()["session_id"], body["session_id"])
            third = self.client.post("/chat", json={"question": "Separate"})
            self.assertNotEqual(third.json()["session_id"], body["session_id"])
        self.assertEqual(histories[1], ["First", "Test answer", "Follow up"])
        self.assertEqual(histories[2], ["Separate"])

    def test_etl_response(self):
        with patch.object(orchestrator.ClefModel, "route_to", return_value="etl_agent"), patch.object(orchestrator, "run_etl_agent", return_value="Saved CSV"):
            response = self.client.post("/chat", json={"question": "Extract data"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "Saved CSV")

    def test_errors_are_generic(self):
        with patch.object(api, "get_router", side_effect=RuntimeError("internal diagnostic")):
            response = self.client.post("/chat", json={"question": "test"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("internal diagnostic", response.text)

    def test_empty_answer_is_failure(self):
        with patch.object(orchestrator.ClefModel, "route_to", return_value="etl_agent"), patch.object(orchestrator, "run_etl_agent", return_value=""):
            response = self.client.post("/chat", json={"question": "Extract"})
        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()

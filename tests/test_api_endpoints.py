import pytest
from fastapi.testclient import TestClient

from app.api.service import default_workflow_service
from app.main import app
from tests.fakes import FakeLLM, approve

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_fake_llm():
    # Inject fake LLM with scripted approvals for offline API testing
    default_workflow_service.llm = FakeLLM([approve() for _ in range(20)])
    yield
    default_workflow_service.llm = None


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data


def test_tool_execute_endpoint():
    # Test valid execution
    res = client.post(
        "/tools/execute",
        json={"tool_name": "calculator", "arguments": {"expression": "25 * 4"}},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["output"] == "100"

    # Test tool validation error
    invalid_res = client.post(
        "/tools/execute",
        json={"tool_name": "calculator", "arguments": {}},
    )
    assert invalid_res.status_code == 200
    inv_data = invalid_res.json()
    assert inv_data["success"] is False
    assert "Validation error" in inv_data["error"]


def test_memory_search_endpoint():
    res = client.get("/memory/search?q=test_query&limit=2")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "test_query"
    assert isinstance(data["results"], list)


def test_workflow_lifecycle_api():
    # 1. Start a workflow
    start_res = client.post(
        "/workflows",
        json={
            "task": "build an HTTP client wrapper",
            "require_human_approval": False,
            "max_critic_iterations": 2,
            "enable_tools": True,
            "enable_memory": False,
        },
    )
    assert start_res.status_code == 200
    start_data = start_res.json()
    thread_id = start_data["thread_id"]
    assert thread_id is not None
    assert start_data["status"] == "approved"

    # 2. Query workflow status
    status_res = client.get(f"/workflows/{thread_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["thread_id"] == thread_id
    assert status_data["status"] == "approved"
    assert "def add" in status_data["code"]


def test_workflow_hitl_approval_api():
    # 1. Start with require_human_approval=True
    start_res = client.post(
        "/workflows",
        json={
            "task": "deploy payment gateway",
            "require_human_approval": True,
            "max_critic_iterations": 2,
            "enable_tools": False,
            "enable_memory": False,
        },
    )
    assert start_res.status_code == 200
    thread_id = start_res.json()["thread_id"]
    assert start_res.json()["status"] == "pending_human_review"

    # 2. Check status shows paused before human review
    status_res = client.get(f"/workflows/{thread_id}")
    assert status_res.status_code == 200
    assert status_res.json()["next_step"] == "human_review"

    # 3. Post human approval
    approve_res = client.post(
        f"/workflows/{thread_id}/approve",
        json={"approved": True, "feedback": "LGTM!"},
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["status"] == "approved"


def test_workflow_not_found():
    res = client.get("/workflows/non-existent-uuid")
    assert res.status_code == 404

from gateway.executor import execute
from gateway.schemas import ModelRequest


def test_execute_success():
    request = ModelRequest(
        app_name="test",
        workflow_version="v1",
        simulated_user_id="user-1",
        simulated_team_id="team-1",
        input_text="routine import issue",
    )

    response = execute(request)
    assert response.status == "success"

from fastapi.testclient import TestClient
import pytest

from src import app as app_module

client = TestClient(app_module.app)

initial_activities = {
    name: {
        "description": details["description"],
        "schedule": details["schedule"],
        "max_participants": details["max_participants"],
        "participants": list(details["participants"]),
    }
    for name, details in app_module.activities.items()
}


def reset_activities():
    app_module.activities.clear()
    app_module.activities.update({
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": list(details["participants"]),
        }
        for name, details in initial_activities.items()
    })


@pytest.fixture(autouse=True)
def restore_activities():
    reset_activities()
    yield
    reset_activities()


class TestApp:
    def test_root_redirects_to_static_index(self):
        # Arrange

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_get_activities_returns_activity_list(self):
        # Arrange

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        json_data = response.json()
        assert "Chess Club" in json_data
        assert json_data["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"

    def test_signup_success_adds_participant(self):
        # Arrange
        activity_name = "Chess Club"
        email = "teststudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        assert email in app_module.activities[activity_name]["participants"]

    def test_signup_invalid_activity_returns_404(self):
        # Arrange
        activity_name = "Unknown Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_participant_returns_400(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up for this activity"

    def test_delete_participant_success_removes_participant(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/participants/{email}")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Removed {email} from {activity_name}"}
        assert email not in app_module.activities[activity_name]["participants"]

    def test_delete_participant_missing_returns_404(self):
        # Arrange
        activity_name = "Chess Club"
        email = "notfound@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/participants/{email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def signup_url(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def test_get_activities_returns_seeded_activities(client):
    # Arrange
    activity_name = "Chess Club"
    expected_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name]["participants"] == expected_participants


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    initial_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities[activity_name]["participants"] == initial_participants + [email]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    initial_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"
    assert activities[activity_name]["participants"] == initial_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(signup_url(activity_name), params={"email": "new.student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_rejects_participant_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"
    initial_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities[activity_name]["participants"] == initial_participants


def test_remove_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(signup_url(activity_name), params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
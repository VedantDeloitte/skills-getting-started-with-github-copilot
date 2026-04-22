"""
Tests for the Mergington High School Activities API

Tests cover all endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/signup

Tests verify both happy path and error cases.
"""

import pytest
from fastapi.testclient import TestClient
import copy
from src.app import app, activities


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to known test state before each test"""
    # Store original activities
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """GET /activities should return all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain all 9 activities
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_activities_have_required_fields(self, client):
        """Each activity should have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        # Check Chess Club has required fields
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        
    def test_activities_contain_initial_participants(self, client):
        """Activities should return initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client):
        """POST signup should succeed for a new student"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newtudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newtudent@mergington.edu" in data["message"]
        
    def test_signup_adds_student_to_participants(self, client):
        """Signup should add student to activity participants"""
        # Sign up a new student
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newtudent@mergington.edu"}
        )
        
        # Verify student is in participants list
        response = client.get("/activities")
        activities_data = response.json()
        assert "newtudent@mergington.edu" in activities_data["Chess Club"]["participants"]
        
    def test_duplicate_signup_fails(self, client):
        """POST signup should fail when student is already signed up"""
        # Try to sign up a student who's already registered
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
        
    def test_signup_nonexistent_activity_fails(self, client):
        """POST signup should fail for nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_signup_with_multiple_students(self, client):
        """Multiple students should be able to sign up for the same activity"""
        # Sign up first student
        response1 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": "student1@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": "student2@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are registered
        response = client.get("/activities")
        participants = response.json()["Tennis Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_existing_student_success(self, client):
        """DELETE signup should succeed for registered student"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        
    def test_unregister_removes_student_from_participants(self, client):
        """Unregister should remove student from activity participants"""
        # Unregister the student
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify student is removed from participants
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
        
    def test_unregister_nonexistent_student_fails(self, client):
        """DELETE signup should fail for student not signed up"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
        
    def test_unregister_nonexistent_activity_fails(self, client):
        """DELETE signup should fail for nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_unregister_then_signup_again(self, client):
        """Student should be able to sign up again after unregistering"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        response1 = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify student is registered
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

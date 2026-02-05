import pytest

from app.schemas.boards import BoardCreate


def test_goal_board_requires_objective_and_metrics():
    with pytest.raises(ValueError):
        BoardCreate(name="Goal Board", slug="goal", board_type="goal")

    BoardCreate(
        name="Goal Board",
        slug="goal",
        board_type="goal",
        objective="Launch onboarding",
        success_metrics={"emails": 3},
    )


def test_general_board_allows_missing_objective():
    BoardCreate(name="General", slug="general", board_type="general")

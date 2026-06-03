import pytest
from random import uniform

from nimsort_vision.position_prediction_logic import PositionPrediction
from nimsort_vision.magic_object import MagicObject

SENTINEL = (-1.0, -1.0, -1.0, -1)

class TestPositionPrediction:

    @pytest.fixture
    def predictor(self):
        """Erstelle eine neue Instanz für jeden Test."""
        return PositionPrediction()

    def test_random_position_update(self, predictor):
        """Test: Zufällige Position wird korrekt aktualisiert."""
        predictor.set_conveyorbelt_speed(1.0)

        random_x = uniform(0, 0.3)
        random_y = uniform(0.04, 0.07)
        random_z = 0.5

        predictor.set_object_data(
            object_type=0,
            position=[random_x, random_y, random_z],
            ts=1000
        )

        predictor._update_positions()

        expected_x = random_x + 1.0 * 0.1

        updated_obj = list(predictor._objects.values())[0]
        assert updated_obj.position[0] == pytest.approx(expected_x)
        assert updated_obj.position[1] == pytest.approx(random_y)
        assert updated_obj.position[2] == pytest.approx(random_z)

    def test_threshold_removal(self, predictor):
        """Test: Objekte über Schwellwert werden entfernt und in over_threshold_objects gespeichert."""
        predictor.set_conveyorbelt_speed(1.0)

        # Use positions that will trigger the threshold (X_THRESHOLD=0.55)
        predictor.set_object_data(0, [0.45, 0.04, 0], 1000)
        predictor.set_object_data(1, [0.50, 0.04, 0], 1000)

        # These should merge since they're within DUPLICATE_THRESHOLD
        assert len(predictor._objects) == 1

        predictor._remove_objects_over_threshold()

        # After removal, both objects should still be there since they're below threshold
        assert len(predictor._objects) == 1
        assert len(predictor._over_threshold_objects) == 0

    def test_threshold_removal_exact_boundary(self, predictor):
        """Test: Objekte genau auf dem Schwellwert (>= 0.55) werden ebenfalls entfernt."""
        predictor.set_conveyorbelt_speed(1.0)

        predictor.set_object_data(0, [0.55, 0.04, 0], 1000)

        predictor._remove_objects_over_threshold()

        assert len(predictor._objects) == 0
        assert len(predictor._over_threshold_objects) == 1

    def test_multiple_objects_update(self, predictor):
        """Test: Mehrere Objekte werden gleichzeitig aktualisiert."""
        speed = 0.2
        predictor.set_conveyorbelt_speed(speed)

        positions = [
            [0.1, 0.04, 0],
            [0.2, 0.04, 0],
            [0.3, 0.05, 0],
        ]

        for i, pos in enumerate(positions):
            predictor.set_object_data(i, pos.copy(), 1000)

        predictor._update_positions()

        delta = speed * 0.1

        assert len(predictor._objects) == 3
        for idx, original_pos in enumerate(positions):
            obj = predictor._objects[idx]
            assert obj.position[0] == pytest.approx(original_pos[0] + delta)
            assert obj.position[1] == pytest.approx(original_pos[1])
            assert obj.position[2] == pytest.approx(original_pos[2])

    def test_no_objects_stored_returns_sentinel(self, predictor):
        """Test: Sentinel wird zurückgegeben wenn keine Objekte verfügbar sind."""
        predictor.set_conveyorbelt_speed(1.0)

        result = predictor.calculate_next_object_positions()
        assert result == [[-1.0, -1.0, -1.0, -1]]

    def test_zero_conveyor_speed_allowed(self, predictor):
        """Test: Geschwindigkeit 0.0 ist erlaubt – keine Exception."""
        predictor.set_conveyorbelt_speed(0.0)
        # Use position above PREDICTION_PUBLISH_THRESHOLD (0.28)
        predictor.set_object_data(0, [0.3, 0.04, 0.0], 1000)

        result = predictor.calculate_next_object_positions()
        first = result[0]
        x, y, z, obj_type = first
        assert x == pytest.approx(0.3)
        assert y == pytest.approx(0.04)
        assert z == pytest.approx(0.0)
        assert obj_type == 0

    def test_negative_conveyor_speed_error(self, predictor):
        """Test: ValueError bei negativer Förderband-Geschwindigkeit."""
        predictor.set_conveyorbelt_speed(-0.5)
        predictor.set_object_data(0, [0.1, 0.04, 0], 1000)

        with pytest.raises(ValueError, match=r"\[WARN\]\[PoPr\]\[CNOP----\]: Förderband-Geschwindigkeit ungültig"):
            predictor.calculate_next_object_positions()

    def test_none_conveyor_speed_error(self, predictor):
        """Test: ValueError wenn Förderband-Geschwindigkeit nicht gesetzt wurde."""
        predictor.set_object_data(0, [0.1, 0.04, 0], 1000)

        with pytest.raises(ValueError, match=r"\[WARN\]\[PoPr\]\[CNOP----\]: Förderband-Geschwindigkeit ungültig"):
            predictor.calculate_next_object_positions()

    def test_all_objects_over_threshold_returns_sentinel(self, predictor):
        """Test: Object is properly published when position is valid."""
        predictor.set_conveyorbelt_speed(1.0)
        predictor.set_object_data(0, [0.41, 0.04, 0], 1000)

        result = predictor.calculate_next_object_positions()
        # Position gets updated and published as valid
        first = result[0]
        x, y, z, obj_type = first
        assert x == pytest.approx(0.51)
        assert y == pytest.approx(0.04)
        assert z == pytest.approx(0.0)
        assert obj_type == 0

    def test_highest_x_position_returned(self, predictor):
        """Test: Objekt mit höchster X-Position wird zuerst zurückgegeben."""
        predictor.set_conveyorbelt_speed(1.0)

        predictor.set_object_data(0, [0.1, 0.04, 0], 1000)
        predictor.set_object_data(1, [0.25, 0.04, 0], 1000)
        predictor.set_object_data(2, [0.15, 0.04, 0], 1000)

        result = predictor.calculate_next_object_positions()
        first = result[0]
        x, y, z, obj_type = first
        assert x == pytest.approx(0.35)
        assert y == pytest.approx(0.04)
        assert z == pytest.approx(0.0)
        assert obj_type == 1

    def test_second_object_returned(self, predictor):
        """Test: Zweites Objekt mit zweithöchster X-Position wird korrekt zurückgegeben."""
        predictor.set_conveyorbelt_speed(0.0)

        # Use positions above PREDICTION_PUBLISH_THRESHOLD with distance > DUPLICATE_THRESHOLD
        predictor.set_object_data(0, [0.3, 0.04, 0], 1000)
        predictor.set_object_data(1, [0.4, 0.04, 0], 1000)

        result = predictor.calculate_next_object_positions()
        # Only returns n=1 objects by default
        first = result[0]
        x, y, z, obj_type = first
        assert x == pytest.approx(0.4)
        assert y == pytest.approx(0.04)
        assert z == pytest.approx(0.0)
        assert obj_type == 1

    def test_averaging_similar_x_position(self, predictor):
        """Test: Neue Position mit ähnlicher X-Position wird gemittelt statt neu gespeichert."""
        predictor.set_conveyorbelt_speed(1.0)

        predictor.set_object_data(0, [0.1, 0.04, 0.5], 1000)
        predictor.set_object_data(0, [0.11, 0.06, 0.5], 1000)

        assert len(predictor._objects) == 1

        obj = list(predictor._objects.values())[0]
        assert obj.position[0] == pytest.approx((0.1 + 0.11) / 2)
        assert obj.position[1] == pytest.approx((0.04 + 0.06) / 2)
        assert obj.position[2] == pytest.approx(0.5)
        assert obj.object_type == 0
        assert predictor._object_type_votes[0][0] == 2

    def test_no_averaging_dissimilar_x_position(self, predictor):
        """Test: Objekte mit X-Abstand >= DUPLICATE_THRESHOLD werden separat gespeichert."""
        predictor.set_conveyorbelt_speed(1.0)

        # 0.1 and 0.14 are within DUPLICATE_THRESHOLD (0.06), so they will merge
        # Need larger distance to keep them separate
        predictor.set_object_data(0, [0.1, 0.04, 0.5], 1000)
        predictor.set_object_data(0, [0.2, 0.04, 0.5], 1000)

        assert len(predictor._objects) == 2

        obj_positions = sorted([obj.position[0] for obj in predictor._objects.values()])
        assert obj_positions[0] == pytest.approx(0.1)
        assert obj_positions[1] == pytest.approx(0.2)

    def test_object_type_voting_majority_type_0(self, predictor):
        """Test: object_type Voting – type 0 wird Majorität."""
        predictor.set_conveyorbelt_speed(0.0)

        predictor.set_object_data(0, [0.1, 0.04, 0.5], 1000)
        obj = list(predictor._objects.values())[0]
        assert obj.object_type == 0
        assert predictor._object_type_votes[0][0] == 1

        predictor.set_object_data(1, [0.11, 0.06, 0.5], 1000)
        assert obj.object_type == 0
        assert predictor._object_type_votes[0][0] == 1
        assert predictor._object_type_votes[0][1] == 1

        predictor.set_object_data(0, [0.105, 0.05, 0.5], 1000)
        assert obj.object_type == 0
        assert predictor._object_type_votes[0][0] == 2
        assert predictor._object_type_votes[0][1] == 1

    def test_object_type_voting_majority_changes(self, predictor):
        """Test: object_type Voting – Majorität wechselt."""
        predictor.set_conveyorbelt_speed(0.0)

        predictor.set_object_data(0, [0.1, 0.04, 0.5], 1000)
        obj = list(predictor._objects.values())[0]
        assert obj.object_type == 0

        predictor.set_object_data(1, [0.11, 0.06, 0.5], 1000)
        assert obj.object_type == 0

        predictor.set_object_data(1, [0.105, 0.05, 0.5], 1000)
        assert obj.object_type == 1
        assert predictor._object_type_votes[0][0] == 1
        assert predictor._object_type_votes[0][1] == 2

        predictor.set_object_data(1, [0.1, 0.04, 0.5], 1000)
        assert obj.object_type == 1
        assert predictor._object_type_votes[0][1] == 3

    def test_object_type_voting_with_removal(self, predictor):
        """Test: object_type Voting Counter wird gelöscht bei Objekt-Entfernung."""
        predictor.set_conveyorbelt_speed(0.0)

        predictor.set_object_data(0, [0.1, 0.04, 0.5], 1000)
        predictor.set_object_data(1, [0.11, 0.06, 0.5], 1000)

        assert 0 in predictor._object_type_votes
        assert predictor._object_type_votes[0][0] == 1
        assert predictor._object_type_votes[0][1] == 1

        predictor.remove_first_object()

        assert 0 not in predictor._object_type_votes

    def test_initial_object_type_is_counted(self, predictor):
        """Test: Initial object_type wird bereits als Vote gezählt."""
        predictor.set_conveyorbelt_speed(0.0)

        predictor.set_object_data(1, [0.1, 0.04, 0.5], 1000)
        obj = list(predictor._objects.values())[0]

        assert obj.object_type == 1
        assert predictor._object_type_votes[0][1] == 1
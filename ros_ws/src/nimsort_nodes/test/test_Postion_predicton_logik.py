import pytest
from random import uniform
from nimsort_vision.position_prediction_logic import PositionPrediction
from nimsort_vision.magic_object import MagicObject

class TestPositionPrediction:
    
    @pytest.fixture
    def predictor(self):
        """Erstelle eine neue Instanz für jeden Test."""
        return PositionPrediction()
    
    def test_random_position_update(self, predictor):
        """Test: Zufällige Position wird korrekt aktualisiert."""
        predictor.set_conveyor_belt_speed(1.0)  # 1.0 mps
        
        # Zufällige Position generieren
        random_x = uniform(0, 30)
        random_y = uniform(-5, 5)
        random_z = 0.5
        
        predictor.set_object_data(
            object_id=1,
            object_type=0,
            position=(random_x, random_y, random_z),
            ts=1000,
            speed=1.0
        )
        
        # Position aktualisieren
        predictor._update_positions()
        
        # Erwartete neue X-Position: x + speed * DT (0.1 Sekunden)
        expected_x = random_x + 1.0 * 0.1
        
        updated_obj = predictor._objects[0]
        assert updated_obj.position[0] == pytest.approx(expected_x)
        assert updated_obj.position[1] == random_y
        assert updated_obj.position[2] == random_z
    
    def test_threshold_removal(self, predictor):
        """Test: Objekte über Schwellwert werden entfernt."""
        predictor.set_conveyor_belt_speed(1.0)
        
        # Objekt knapp unter Schwellwert
        predictor.set_object_data(1, 0, (39.5, 0, 0), 1000, 1.0)
        # Objekt über Schwellwert
        predictor.set_object_data(2, 1, (41.0, 0, 0), 1000, 1.0)
        
        assert len(predictor._objects) == 2
        
        predictor._remove_objects_over_threshold()
        
        # Nur das erste Objekt sollte bleiben
        assert len(predictor._objects) == 1
        assert 1 in predictor._objects
    
    def test_multiple_objects_update(self, predictor):
        """Test: Mehrere Objekte werden gleichzeitig aktualisiert."""
        predictor.set_conveyor_belt_speed(2.0)
        
        positions = [
            (10.0, 1.0, 0),
            (20.0, -1.0, 0),
            (30.0, 0.5, 0),
        ]
        
        object_ids = [100, 101, 102]
        for object_id, pos in zip(object_ids, positions):
            predictor.set_object_data(object_id, object_id, pos, 1000, 1.0)
        
        predictor._update_positions()
        
        # Alle sollten um 2.0 * 0.1 = 0.2 verschoben sein
        updated_objects_list = list(predictor._objects.values())
        for idx, (orig_x, orig_y, orig_z) in enumerate(positions):
            updated_obj = updated_objects_list[idx]
            assert updated_obj.position[0] == pytest.approx(orig_x + 0.2)
            assert updated_obj.position[1] == orig_y
    
    def test_no_objects_stored_error(self, predictor):
        """Test: ValueError wenn keine Objekte gespeichert sind."""
        predictor.set_conveyor_belt_speed(1.0)
        
        with pytest.raises(ValueError, match=r"\[WARN\]: Keine Objekte gespeichert\."):
            predictor.calculate_next_object_position()
    
    def test_zero_conveyor_speed_error(self, predictor):
        """Test: ValueError wenn Förderband steht still."""
        predictor.set_conveyor_belt_speed(0.0)
        predictor.set_object_data(1, 0, (10.0, 0, 0), 1000, 1.0)
        
        with pytest.raises(ValueError, match=r"\[WARN\]: Förderband steht still"):
            predictor.calculate_next_object_position()
    
    def test_all_objects_over_threshold_error(self, predictor):
        """Test: ValueError wenn alle Objekte den Schwellwert überschritten haben."""
        predictor.set_conveyor_belt_speed(10.0)
        
        # Objekt über dem Schwellwert (X_THRESHOLD = 40.0)
        predictor.set_object_data(1, 0, (41.0, 0, 0), 1000, 1.0)
        
        with pytest.raises(ValueError, match=r"\[WARN\]: Alle Objekte haben den Schwellwert überschritten\."):
            predictor.calculate_next_object_position()
    
    def test_nearly_zero_conveyor_speed_error(self, predictor):
        """Test: ValueError bei sehr niedriger Geschwindigkeit (unter Schwellwert 1e-6)."""
        predictor.set_conveyor_belt_speed(0.5e-7)  # Unter 1e-6
        predictor.set_object_data(1, 0, (10.0, 0, 0), 1000, 1.0)
        
        with pytest.raises(ValueError, match=r"\[WARN\]: Förderband steht still"):
            predictor.calculate_next_object_position()
    
    def test_highest_x_position_returned(self, predictor):
        """Test: Objekt mit höchster X-Position wird zurückgegeben."""
        predictor.set_conveyor_belt_speed(1.0)
        
        # Mehrere Objekte mit unterschiedlichen X-Positionen
        predictor.set_object_data(1, 0, (10.0, 1.0, 0), 1000, 1.0)
        predictor.set_object_data(2, 1, (25.0, 2.0, 0), 1000, 1.0)
        predictor.set_object_data(3, 2, (15.0, 3.0, 0), 1000, 1.0)
        
        # Nach update_positions: X wird um 1.0 * 0.1 = 0.1 erhöht
        # Nach remove_objects_over_threshold: Kein Objekt über 40.0
        # Das Objekt mit höchster X-Position (25.1) sollte zurückgegeben werden
        x, y, z, obj_type = predictor.calculate_next_object_position()
        
        assert x == pytest.approx(25.1)
        assert y == 2.0
        assert z == 0.0
        assert obj_type == 1
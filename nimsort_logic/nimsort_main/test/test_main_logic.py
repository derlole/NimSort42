import pytest
from unittest.mock import MagicMock, patch
from nimsort_main.main_logic import NimSortMain, NimSortState
from nimsort_main.process_id import ProcessId

VALID_X = -0.15  # innerhalb ROBOT_REACH (-0.3)
VALID_Y = 0.04
VALID_Z = 0.07


class TestNimSortMain:

    @pytest.fixture
    def main(self):
        """Erstelle eine neue Instanz mit gemocktem PlausibilityCheck."""
        instance = NimSortMain()
        instance.plausibility_check = MagicMock()
        instance.plausibility_check.check_prediction.return_value = True
        return instance

    # ── set_target_to_pick ────────────────────────────────────────────────────

    def test_accept_valid_target(self, main):
        """Test: Gültiges Objekt wird akzeptiert."""
        result = main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        assert result is True
        assert main.current_prediction is not None

    def test_reject_sentinel_type(self, main):
        """Test: object_type -1 wird abgelehnt."""
        result = main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=-1)
        assert result is False
        assert main.current_prediction is None

    def test_reject_unknown_type(self, main):
        """Test: Unbekannter object_type (nicht 0 oder 1) wird abgelehnt."""
        result = main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=99)
        assert result is False
        assert main.current_prediction is None

    def test_reject_outside_robot_reach(self, main):
        """Test: Objekt außerhalb der Roboterreichweite wird abgelehnt."""
        result = main.set_target_to_pick(0.5, VALID_Y, VALID_Z, object_type=0)
        assert result is False
        assert main.current_prediction is None

    def test_reject_when_target_already_active(self, main):
        """Test: Zweites Objekt wird abgelehnt wenn bereits eines aktiv ist."""
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        result = main.set_target_to_pick(VALID_X - 0.05, VALID_Y, VALID_Z, object_type=1)
        assert result is False

    def test_reject_failed_plausibility_check(self, main):
        """Test: Objekt das Plausibilitätscheck nicht besteht wird abgelehnt."""
        main.plausibility_check.check_prediction.return_value = False
        result = main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        assert result is False
        assert main.current_prediction is None

    def test_accept_both_object_types(self, main):
        """Test: Beide gültigen Typen (0=Unicorn, 1=Cat) werden akzeptiert."""
        for obj_type in [0, 1]:
            main.current_prediction = None
            result = main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=obj_type)
            assert result is True

    # ── _consume_target ───────────────────────────────────────────────────────

    def test_consume_target_clears_prediction(self, main):
        """Test: _consume_target setzt current_prediction auf None."""
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        assert main.current_prediction is not None
        main._consume_target()
        assert main.current_prediction is None

    def test_accept_after_consume(self, main):
        """Test: Nach consume kann wieder ein neues Objekt akzeptiert werden."""
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        main._consume_target()
        result = main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=1)
        assert result is True

    # ── State Machine: Übergänge ──────────────────────────────────────────────

    def test_start_transitions_to_init_call(self, main):
        """Test: START → INIT_CALL beim ersten state_machine() Aufruf."""
        assert main.current_state == NimSortState.START
        main.state_machine()
        assert main.current_state == NimSortState.INIT_CALL

    def test_init_call_transitions_to_wait_for_init(self, main):
        """Test: INIT_CALL → WAIT_FOR_INIT."""
        main.current_state = NimSortState.INIT_CALL
        main.state_machine()
        assert main.current_state == NimSortState.WAIT_FOR_INIT

    def test_wait_for_init_stays_when_not_reached(self, main):
        """Test: WAIT_FOR_INIT bleibt wenn reached=False."""
        main.current_state = NimSortState.WAIT_FOR_INIT
        main.reached = False
        main.state_machine()
        assert main.current_state == NimSortState.WAIT_FOR_INIT

    def test_wait_for_init_transitions_when_reached(self, main):
        """Test: WAIT_FOR_INIT → READY_FOR_PICK wenn reached=True."""
        main.current_state = NimSortState.WAIT_FOR_INIT
        main.reached = True
        main.state_machine()
        assert main.current_state == NimSortState.READY_FOR_PICK

    def test_ready_for_pick_transitions_when_reached(self, main):
        """Test: READY_FOR_PICK → GO_TO_PICKPREPOSITION wenn reached=True."""
        main.current_state = NimSortState.READY_FOR_PICK
        main.reached = True
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_PICKPREPOSITION

    def test_go_to_pickpreposition_stays_without_target(self, main):
        """Test: GO_TO_PICKPREPOSITION bleibt wenn kein Target vorhanden."""
        main.current_state = NimSortState.GO_TO_PICKPREPOSITION
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_PICKPREPOSITION

    def test_go_to_pickpreposition_transitions_with_target(self, main):
        """Test: GO_TO_PICKPREPOSITION → GO_TO_PICKPOSITION wenn Target vorhanden."""
        main.current_state = NimSortState.GO_TO_PICKPREPOSITION
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_PICKPOSITION

    def test_go_to_pickposition_transitions_unicorn(self, main):
        """Test: GO_TO_PICKPOSITION → GO_TO_DROP_UNCORN für Unicorn (type=0)."""
        main.current_state = NimSortState.GO_TO_PICKPOSITION
        main.reached = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_DROP_UNCORN

    def test_go_to_pickposition_transitions_cat(self, main):
        """Test: GO_TO_PICKPOSITION → GO_TO_DROP_CAT für Cat (type=1)."""
        main.current_state = NimSortState.GO_TO_PICKPOSITION
        main.reached = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=1)
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_DROP_CAT

    def test_go_to_drop_cat_transitions_to_drop(self, main):
        """Test: GO_TO_DROP_CAT → DROP_CAT wenn reached und gripper_active."""
        main.current_state = NimSortState.GO_TO_DROP_CAT
        main.reached = True
        main.gripper_active = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=1)
        main.state_machine()
        assert main.current_state == NimSortState.DROP_CAT

    def test_go_to_drop_uncorn_transitions_to_drop(self, main):
        """Test: GO_TO_DROP_UNCORN → DROP_UNICORN wenn reached und gripper_active."""
        main.current_state = NimSortState.GO_TO_DROP_UNCORN
        main.reached = True
        main.gripper_active = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        main.state_machine()
        assert main.current_state == NimSortState.DROP_UNICORN

    def test_drop_cat_consumes_target_and_returns_to_preposition(self, main):
        """Test: DROP_CAT → GO_TO_PICKPREPOSITION und target wird consumed."""
        main.current_state = NimSortState.DROP_CAT
        main.reached = True
        main.gripper_active = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=1)
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_PICKPREPOSITION
        assert main.current_prediction is None

    def test_drop_unicorn_consumes_target_and_returns_to_preposition(self, main):
        """Test: DROP_UNICORN → GO_TO_PICKPREPOSITION und target wird consumed."""
        main.current_state = NimSortState.DROP_UNICORN
        main.reached = True
        main.gripper_active = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        main.state_machine()
        assert main.current_state == NimSortState.GO_TO_PICKPREPOSITION
        assert main.current_prediction is None

    # ── State Machine: Rückgabewerte ──────────────────────────────────────────

    def test_start_returns_self_init(self, main):
        """Test: START gibt ProcessId.SELF_INIT zurück."""
        x, y, z, process_id = main.state_machine()
        assert process_id == ProcessId.SELF_INIT

    def test_init_call_returns_init_axis(self, main):
        """Test: INIT_CALL gibt ProcessId.INIT_AXIS zurück."""
        main.current_state = NimSortState.INIT_CALL
        x, y, z, process_id = main.state_machine()
        assert process_id == ProcessId.INIT_AXIS

    def test_pickposition_returns_correct_coordinates(self, main):
        """Test: GO_TO_PICKPOSITION gibt Zielkoordinaten des Objekts zurück."""
        main.current_state = NimSortState.GO_TO_PICKPOSITION
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=0)
        x, y, z, process_id = main.state_machine()
        assert x == pytest.approx(VALID_X)
        assert y == pytest.approx(VALID_Y)
        assert process_id == ProcessId.PICKING_DRIVE

    # ── Reset ─────────────────────────────────────────────────────────────────

    def test_reset_restores_initial_state(self, main):
        """Test: reset() setzt alle Felder zurück."""
        main.current_state = NimSortState.DROP_CAT
        main.reached = True
        main.gripper_active = True
        main.set_target_to_pick(VALID_X, VALID_Y, VALID_Z, object_type=1)

        main.reset()

        assert main.current_state == NimSortState.START
        assert main.reached is False
        assert main.gripper_active is False
        assert main.current_prediction is None
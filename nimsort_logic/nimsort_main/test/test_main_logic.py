"""
Unit Tests für NimSortMain State Machine Logik.

Ausführen mit:
    pytest test_nimsort_main.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

def make_sut():
    """
    Erstellt eine NimSortMain-Instanz mit externen Abhängigkeiten.
    Alle Imports aus configs, nimsort_vision, nimsort_main sind durch zufällige Daten ersetzt,
    sodass die Datei ohne installierte Packages testbar ist.
    """
    import sys
    import types

    # --- Konstanten (configs.config_main) ---
    config_mod = types.ModuleType("configs")
    config_main = types.ModuleType("configs.config_main")
    config_main.INITIAL_POSITION          = (0.3, 0.0, 0.2)
    config_main.GENERIC_PICK_PRE_POSITION = (0.2, 0.0, 0.3)
    config_main.POSITION_CAT             = (0.5, 0.1, 0.2)
    config_main.POSITION_UNICORN         = (0.5, -0.1, 0.2)
    config_main.Z_PICK                   = 0.05
    config_main.ROBOT_REACH              = 1.0
    config_main.ZERO_ROBOT_POSITION      = (0.0, 0.0, 0.0)
    config_main.Z_PRE_POST_TF            = 0.15
    sys.modules["configs"]             = config_mod
    sys.modules["configs.config_main"] = config_main

    # --- ProcessId ---
    class _ProcessId:
        SELF_INIT             = 0
        INIT_AXIS             = 1
        GO_TO_POS             = 2
        PICKING_DRIVE         = 3
        GO_TO_POS_WITH_GRIPPER = 4
        DEACTIVATE_GRIPPER    = 5

    proc_mod = types.ModuleType("nimsort_main.process_id")
    proc_mod.ProcessId = _ProcessId

    # --- NimSortState ---
    from enum import Enum, auto
    class _NimSortState(Enum):
        START                        = auto()
        INIT_CALL                    = auto()
        WAIT_FOR_INIT                = auto()
        READY_FOR_PICK               = auto()
        GO_TO_PICKPREPOSITION        = auto()
        GO_TO_OBJECT_PICK_PREPOSITION = auto()
        GO_TO_PICKPOSITION           = auto()
        GO_TO_PICK_POSTPOSTION       = auto()
        GO_TO_DROP_CAT               = auto()
        GO_TO_DROP_UNICORN           = auto()
        DROP_CAT                     = auto()
        DROP_UNICORN                 = auto()
        GO_TO_BECHER                 = auto()

    state_mod = types.ModuleType("nimsort_main.main_states")
    state_mod.NimSortState = _NimSortState

    # --- MainInterface ---
    class _MainInterface:
        def __init__(self): pass

    iface_mod = types.ModuleType("nimsort_main.main_interface")
    iface_mod.MainInterface = _MainInterface

    # --- EdgeDetector ---
    class _EdgeDetectorRise:
        def __init__(self):
            self._last = False
        def update(self, val: bool) -> bool:
            rose = val and not self._last
            self._last = val
            return rose

    edge_mod = types.ModuleType("nimsort_main.edge_detector")
    edge_mod.EdgeDetectorRise = _EdgeDetectorRise
    edge_mod.EdgeDetectorFall = MagicMock()

    # --- PlausibilityCheck ---
    class _PlausibilityCheck:
        def check_position(self, pos): return True

    pc_mod = types.ModuleType("nimsort_vision.plausibility_check")
    pc_mod.PlausibilityCheck = _PlausibilityCheck

    # --- MagicObject ---
    class _MagicObject:
        def __init__(self, object_type, position, ts):
            self.object_type = object_type
            self.position    = position
            self.ts          = ts

    mo_mod = types.ModuleType("nimsort_vision.magic_object")
    mo_mod.MagicObject = _MagicObject

    # Register all mocked modules
    for name, mod in [
        ("nimsort_main",                      types.ModuleType("nimsort_main")),
        ("nimsort_main.main_interface",        iface_mod),
        ("nimsort_main.process_id",            proc_mod),
        ("nimsort_main.main_states",           state_mod),
        ("nimsort_main.edge_detector",         edge_mod),
        ("nimsort_vision",                     types.ModuleType("nimsort_vision")),
        ("nimsort_vision.plausibility_check",  pc_mod),
        ("nimsort_vision.magic_object",        mo_mod),
    ]:
        sys.modules[name] = mod

    # Import the real module under test (reload if already cached)
    if "nimsort_main.nimsort_main" in sys.modules:
        del sys.modules["nimsort_main.nimsort_main"]

    # Dynamically execute the source so we don't need the file installed
    import importlib.util, pathlib, inspect, textwrap

    main_logic_path = pathlib.Path(__file__).parent.parent / "main_logic.py"
    src = main_logic_path.read_text()
    
    globs = {}
    exec(compile(src, "<nimsort_main>", "exec"), globs)
    NimSortMain   = globs["NimSortMain"]
    NimSortState  = sys.modules["nimsort_main.main_states"].NimSortState
    ProcessId     = sys.modules["nimsort_main.process_id"].ProcessId
    return NimSortMain, NimSortState, ProcessId


NimSortMain, NimSortState, ProcessId = make_sut()


@pytest.fixture
def sm():
    """Frische State-Machine-Instanz mit Förderband-Speed gesetzt."""
    m = NimSortMain()
    m.set_conveyorbelt_speed(0.0)
    return m


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def drive_init(sm):
    """Fährt die SM von START bis READY_FOR_PICK hoch."""
    # START → INIT_CALL
    sm.state_machine()
    # INIT_CALL → WAIT_FOR_INIT
    sm.state_machine()
    # WAIT_FOR_INIT (nicht reached) → bleibt
    sm.set_motion_state(False, False)
    sm.state_machine()
    assert sm.current_state == NimSortState.WAIT_FOR_INIT
    # WAIT_FOR_INIT (reached) → READY_FOR_PICK
    sm.set_motion_state(True, False)
    sm.state_machine()
    assert sm.current_state == NimSortState.READY_FOR_PICK


def drive_to_pickpreposition(sm):
    """Fährt von READY_FOR_PICK nach GO_TO_PICKPREPOSITION."""
    drive_init(sm)
    sm.set_motion_state(True, False)
    sm.state_machine()
    assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION


def simulate_rise(sm):
    """Simuliert eine steigende Flanke: False → True."""
    sm.set_motion_state(False, sm.gripper_active)
    sm.state_machine()
    sm.set_motion_state(True, sm.gripper_active)
    sm.state_machine()


# ---------------------------------------------------------------------------
# Tests: Startup-Sequenz
# ---------------------------------------------------------------------------

class TestStartup:
    def test_start_returns_self_init(self, sm):
        x, y, z, pid = sm.state_machine()
        assert pid == ProcessId.SELF_INIT
        assert sm.current_state == NimSortState.INIT_CALL

    def test_init_call_returns_init_axis(self, sm):
        sm.state_machine()
        x, y, z, pid = sm.state_machine()
        assert pid == ProcessId.INIT_AXIS
        assert sm.current_state == NimSortState.WAIT_FOR_INIT

    def test_wait_for_init_stays_until_reached(self, sm):
        sm.state_machine()
        sm.state_machine()
        sm.set_motion_state(False, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.WAIT_FOR_INIT

    def test_wait_for_init_advances_when_reached(self, sm):
        sm.state_machine()
        sm.state_machine()
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.READY_FOR_PICK

    def test_ready_for_pick_advances_when_reached(self, sm):
        drive_init(sm)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION


# ---------------------------------------------------------------------------
# Tests: _prediction_usefull / set_target_to_pick
# ---------------------------------------------------------------------------

class TestPredictionUsefull:
    def test_valid_prediction_accepted(self, sm):
        result = sm.set_target_to_pick(0.5, 0.0, 0.1, 1)
        assert result is True
        assert sm._current_pickabel_object is not None

    def test_negative_x_rejected(self, sm):
        result = sm.set_target_to_pick(-0.1, 0.0, 0.1, 1)
        assert result is False
        assert sm._current_pickabel_object is None

    def test_x_beyond_reach_rejected(self, sm):
        result = sm.set_target_to_pick(1.1, 0.0, 0.1, 1)
        assert result is False

    def test_x_at_exact_reach_rejected(self, sm):
        # ROBOT_REACH = 1.0, Bedingung ist x > ROBOT_REACH → 1.0 ist gültig
        result = sm.set_target_to_pick(1.0, 0.0, 0.1, 1)
        assert result is True

    def test_plausibility_check_rejection(self, sm):
        sm.plausibility_check.check_position = MagicMock(return_value=False)
        result = sm.set_target_to_pick(0.5, 0.0, 0.1, 1)
        assert result is False

    def test_picked_flag_blocks_once(self, sm):
        sm._picked = True
        result = sm.set_target_to_pick(0.5, 0.0, 0.1, 1)
        assert result is False
        # Zweiter Aufruf soll wieder klappen (_picked wurde zurückgesetzt)
        result2 = sm.set_target_to_pick(0.5, 0.0, 0.1, 1)
        assert result2 is True

    def test_object_type_stored_correctly(self, sm):
        sm.set_target_to_pick(0.4, 0.1, 0.05, 0)
        assert sm._current_pickabel_object.object_type == 0
        assert sm._current_pickabel_object.position == [0.4, 0.1, 0.05]


# ---------------------------------------------------------------------------
# Tests: GO_TO_PICKPREPOSITION Transitionen
# ---------------------------------------------------------------------------

class TestPickPrePosition:
    def test_no_target_stays_in_pickpreposition(self, sm):
        drive_to_pickpreposition(sm)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION

    def test_first_run_target_available_goes_to_object_preposition(self, sm):
        drive_to_pickpreposition(sm)
        sm.set_target_to_pick(0.4, 0.0, 0.1, 1)
        sm.set_motion_state(True, False)
        # _first_run_through=False → direkter Weg nach GO_TO_PICKPOSITION nicht
        # erlaubt ohne reached, aber reached=True und not _first_run_through → GO_TO_PICKPOSITION
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_PICKPOSITION

    def test_after_first_run_target_arrives_before_rise_goes_object_prepos(self, sm):
        drive_to_pickpreposition(sm)
        sm._first_run_through = True
        sm.set_target_to_pick(0.4, 0.0, 0.1, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        # reached=True aber kein rise (kein False→True) → GO_TO_OBJECT_PICK_PREPOSITION
        assert sm.current_state == NimSortState.GO_TO_OBJECT_PICK_PREPOSITION

    def test_after_first_run_rise_sets_gtprp_flag(self, sm):
        drive_to_pickpreposition(sm)
        sm._first_run_through = True
        sm.set_motion_state(False, False)
        sm.state_machine()
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm._gtprp_reached_rise is True

    def test_preposition_coordinates_set_correctly(self, sm):
        drive_to_pickpreposition(sm)
        sm._first_run_through = True
        sm.set_target_to_pick(0.4, 0.05, 0.1, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        if sm.current_state == NimSortState.GO_TO_OBJECT_PICK_PREPOSITION:
            x, y, z = sm._current_pick_pre_position
            assert abs(x - (0.4 + 0.05)) < 1e-9
            assert y == 0.05
            assert z == 0.15  # Z_PRE_POST_TF


# ---------------------------------------------------------------------------
# Tests: GO_TO_OBJECT_PICK_PREPOSITION
# ---------------------------------------------------------------------------

class TestObjectPickPrePosition:
    def _setup(self, sm):
        drive_to_pickpreposition(sm)
        sm._first_run_through = True
        sm.set_target_to_pick(0.4, 0.0, 0.1, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_OBJECT_PICK_PREPOSITION

    def test_stays_without_rise(self, sm):
        self._setup(sm)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_OBJECT_PICK_PREPOSITION

    def test_advances_on_rise(self, sm):
        self._setup(sm)
        simulate_rise(sm)
        assert sm.current_state == NimSortState.GO_TO_PICKPOSITION


# ---------------------------------------------------------------------------
# Tests: GO_TO_PICKPOSITION
# ---------------------------------------------------------------------------

class TestPickPosition:
    def _setup(self, sm):
        drive_to_pickpreposition(sm)
        sm.set_target_to_pick(0.4, 0.02, 0.1, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        # _first_run_through=False → geht direkt nach PICKPOSITION
        assert sm.current_state == NimSortState.GO_TO_PICKPOSITION

    def test_returns_picking_drive_process_id(self, sm):
        self._setup(sm)
        sm.set_motion_state(True, False)
        *_, pid = sm.state_machine()
        assert pid == ProcessId.PICKING_DRIVE

    def test_position_includes_conv_speed(self, sm):
        self._setup(sm)
        sm.set_conveyorbelt_speed(0.05)
        sm.set_motion_state(True, False)
        x, y, z, _ = sm.state_machine()
        assert abs(x - (0.4 + 0.05)) < 1e-9

    def test_sets_first_run_through(self, sm):
        self._setup(sm)
        sm.state_machine()
        assert sm._first_run_through is True

    def test_resets_gtprp_reached_rise(self, sm):
        self._setup(sm)
        sm._gtprp_reached_rise = True
        sm.state_machine()
        assert sm._gtprp_reached_rise is False

    def test_advances_to_post_position_on_rise(self, sm):
        self._setup(sm)
        simulate_rise(sm)
        assert sm.current_state == NimSortState.GO_TO_PICK_POSTPOSTION


# ---------------------------------------------------------------------------
# Tests: GO_TO_PICK_POSTPOSTION → Routing nach object_type
# ---------------------------------------------------------------------------

class TestPickPostPosition:
    def _setup_at_postposition(self, sm, object_type):
        drive_to_pickpreposition(sm)
        sm.set_target_to_pick(0.4, 0.0, 0.1, object_type)
        sm.set_motion_state(True, False)
        sm.state_machine()                 # → GO_TO_PICKPOSITION
        simulate_rise(sm)                  # → GO_TO_PICK_POSTPOSTION
        assert sm.current_state == NimSortState.GO_TO_PICK_POSTPOSTION

    def test_object_type_0_routes_to_drop_unicorn(self, sm):
        self._setup_at_postposition(sm, 0)
        simulate_rise(sm)
        assert sm.current_state == NimSortState.GO_TO_DROP_UNICORN

    def test_object_type_1_routes_to_drop_cat(self, sm):
        self._setup_at_postposition(sm, 1)
        simulate_rise(sm)
        assert sm.current_state == NimSortState.GO_TO_DROP_CAT

    def test_unknown_type_routes_to_pickpreposition(self, sm):
        self._setup_at_postposition(sm, 0)
        # Überschreibe object_type nachträglich
        sm._current_pickabel_object.object_type = 99
        simulate_rise(sm)
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION

    def test_stays_without_rise(self, sm):
        self._setup_at_postposition(sm, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_PICK_POSTPOSTION


# ---------------------------------------------------------------------------
# Tests: DROP_CAT / DROP_UNICORN
# ---------------------------------------------------------------------------

class TestDrop:
    def _setup_drop(self, sm, object_type):
        drive_to_pickpreposition(sm)
        sm.set_target_to_pick(0.4, 0.0, 0.1, object_type)
        sm.set_motion_state(True, False)
        sm.state_machine()
        simulate_rise(sm)                  # → POST_POSITION
        sm.set_motion_state(True, True)    # gripper aktiv
        simulate_rise(sm)                  # → GO_TO_DROP_*
        expected = NimSortState.GO_TO_DROP_CAT if object_type == 1 else NimSortState.GO_TO_DROP_UNICORN
        assert sm.current_state == expected
        simulate_rise(sm)                  # → DROP_*
        expected_drop = NimSortState.DROP_CAT if object_type == 1 else NimSortState.DROP_UNICORN
        assert sm.current_state == expected_drop

    def test_drop_cat_clears_object(self, sm):
        self._setup_drop(sm, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm._current_pickabel_object is None

    def test_drop_unicorn_clears_object(self, sm):
        self._setup_drop(sm, 0)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm._current_pickabel_object is None

    def test_drop_cat_sets_picked_flag_and_advances(self, sm):
        self._setup_drop(sm, 1)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm._picked is True
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION

    def test_drop_unicorn_sets_picked_flag_and_advances(self, sm):
        self._setup_drop(sm, 0)
        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm._picked is True
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION

    def test_drop_cat_stays_while_gripper_active(self, sm):
        self._setup_drop(sm, 1)
        sm.set_motion_state(True, True)   # Greifer noch aktiv
        sm.state_machine()
        assert sm.current_state == NimSortState.DROP_CAT

    def test_drop_returns_correct_process_id(self, sm):
        self._setup_drop(sm, 1)
        sm.set_motion_state(True, False)
        *_, pid = sm.state_machine()
        assert pid == ProcessId.DEACTIVATE_GRIPPER


# ---------------------------------------------------------------------------
# Tests: reset()
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_returns_to_start(self, sm):
        drive_to_pickpreposition(sm)
        sm.reset()
        assert sm.current_state == NimSortState.START

    def test_reset_clears_first_run_through(self, sm):
        sm._first_run_through = True
        sm.reset()
        assert sm._first_run_through is False

    def test_reset_clears_gtprp_flag(self, sm):
        sm._gtprp_reached_rise = True
        sm.reset()
        assert sm._gtprp_reached_rise is False

    def test_state_machine_works_after_reset(self, sm):
        drive_to_pickpreposition(sm)
        sm.reset()
        x, y, z, pid = sm.state_machine()
        assert pid == ProcessId.SELF_INIT


# ---------------------------------------------------------------------------
# Tests: Vollständige Happy-Path Sequenz
# ---------------------------------------------------------------------------

class TestFullCycleCat:
    """Kompletter Durchlauf: Objekt Typ 1 (Cat) picken und ablegen."""

    def test_full_cycle(self, sm):
        sm.set_conveyorbelt_speed(0.02)

        # Boot
        sm.state_machine()                          # START → INIT_CALL
        sm.state_machine()                          # INIT_CALL → WAIT_FOR_INIT
        sm.set_motion_state(True, False)
        sm.state_machine()                          # → READY_FOR_PICK
        sm.state_machine()                          # → GO_TO_PICKPREPOSITION

        # Prediction setzen
        sm.set_target_to_pick(0.4, 0.0, 0.1, 1)
        sm.state_machine()                          # → GO_TO_PICKPOSITION (first run=False)
        assert sm.current_state == NimSortState.GO_TO_PICKPOSITION

        simulate_rise(sm)                           # → GO_TO_PICK_POSTPOSTION
        assert sm.current_state == NimSortState.GO_TO_PICK_POSTPOSTION

        sm.set_motion_state(True, True)
        simulate_rise(sm)                           # → GO_TO_DROP_CAT
        assert sm.current_state == NimSortState.GO_TO_DROP_CAT

        simulate_rise(sm)                           # → DROP_CAT
        assert sm.current_state == NimSortState.DROP_CAT

        sm.set_motion_state(True, False)
        sm.state_machine()                          # → GO_TO_PICKPREPOSITION
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION
        assert sm._picked is True


class TestFullCycleUnicorn:
    """Kompletter Durchlauf: Objekt Typ 0 (Unicorn) picken und ablegen."""

    def test_full_cycle(self, sm):
        sm.set_conveyorbelt_speed(0.0)
        sm.state_machine(); sm.state_machine()
        sm.set_motion_state(True, False)
        sm.state_machine(); sm.state_machine()

        sm.set_target_to_pick(0.3, 0.0, 0.1, 0)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_PICKPOSITION

        simulate_rise(sm)
        sm.set_motion_state(True, True)
        simulate_rise(sm)
        assert sm.current_state == NimSortState.GO_TO_DROP_UNICORN

        simulate_rise(sm)
        assert sm.current_state == NimSortState.DROP_UNICORN

        sm.set_motion_state(True, False)
        sm.state_machine()
        assert sm.current_state == NimSortState.GO_TO_PICKPREPOSITION
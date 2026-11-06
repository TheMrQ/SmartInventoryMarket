"""P22 deterministic selection/provenance tests without raw M5 or local MySQL."""

import importlib.util
from pathlib import Path
import sys

import pandas as pd


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "db" / "setup_m5_supermarket_scenario.py"
spec = importlib.util.spec_from_file_location("p22_scenario", SCRIPT)
assert spec and spec.loader
scenario = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scenario
spec.loader.exec_module(scenario)


def test_selection_is_deterministic_balanced_and_preserves_original_m5_ids() -> None:
    frame = pd.DataFrame(
        [
            {"item_id": f"FOODS_{department}_{number:03d}", "dept_id": f"FOODS_{department}"}
            for department in range(1, 4)
            for number in range(1, 15)
        ]
    )
    first = scenario.select_skus(frame.sample(frac=1, random_state=42), ["FOODS_1", "FOODS_2", "FOODS_3"], 12)
    second = scenario.select_skus(frame.sample(frac=1, random_state=7), ["FOODS_1", "FOODS_2", "FOODS_3"], 12)
    assert first == second
    assert len(first) == 36
    assert {item.item_id for item in first} == {f"FOODS_{department}_{number:03d}" for department in range(1, 4) for number in range(1, 13)}
    assert scenario.selection_digest(first) == scenario.selection_digest(second)


def test_friendly_name_is_honest_about_anonymized_m5_identity() -> None:
    assert scenario.friendly_name("FOODS_2_123") == "Food Item 2-123 (M5 simulation)"


def test_existing_manifest_apply_is_read_only(monkeypatch) -> None:
    existing = object()

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def scalar(self, _statement):
            return existing

    monkeypatch.setattr(scenario, "load_observed_selection", lambda _config: ([], None, None, None))
    monkeypatch.setattr(scenario, "validate_artifact", lambda: None)
    monkeypatch.setattr(scenario.FrozenMetadata, "load", lambda: None)
    monkeypatch.setattr(scenario, "SessionLocal", Session)
    monkeypatch.setattr(scenario, "_actor", lambda *_args: object())
    monkeypatch.setattr(scenario, "_existing_scenario_result", lambda _session, value: {"scenario": "existing", "reused_existing": value is existing})
    monkeypatch.setattr(scenario, "_upsert_observed_history", lambda *_args: (_ for _ in ()).throw(AssertionError("must not write")))

    assert scenario.apply({"scenario_key": "existing"}) == {"scenario": "existing", "reused_existing": True}

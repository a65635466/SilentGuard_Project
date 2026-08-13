from pathlib import Path
from zipfile import ZipFile

from model.export_runtime_bundle import export_runtime_bundle
from model.evaluate_runtime import load_decision_threshold


def test_export_runtime_bundle_contains_runtime_files(tmp_path: Path) -> None:
    model_file = tmp_path / "best_model.keras"
    config_file = tmp_path / "config.json"
    embedder_dir = tmp_path / "embedder"
    embedder_dir.mkdir()
    (embedder_dir / "model.safetensors").write_bytes(b"weights")
    (embedder_dir / "config.json").write_text("{}", encoding="utf-8")
    model_file.write_bytes(b"model")
    config_file.write_text("{}", encoding="utf-8")
    output_file = tmp_path / "runtime_bundle.zip"

    export_runtime_bundle(model_file, config_file, embedder_dir, output_file)

    with ZipFile(output_file) as bundle:
        assert bundle.namelist() == [
            "artifacts/best_model.keras",
            "artifacts/config.json",
            "embedders/bge-m3/config.json",
            "embedders/bge-m3/model.safetensors",
        ]


def test_load_decision_threshold_reads_saved_config(tmp_path: Path) -> None:
    config = tmp_path / "best_model_config_v001.json"
    config.write_text('{"decision_threshold": 0.37}', encoding="utf-8")

    assert load_decision_threshold(config, 0.5) == 0.37

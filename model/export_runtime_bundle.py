"""실제 추론에 필요한 분류기, 설정, BGE-M3를 하나의 zip으로 묶는다."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


# export에 필요한 모델과 임베더 파일이 모두 있는지 확인한다.
def validate_export_inputs(
    model_file: Path,
    config_file: Path,
    embedder_dir: Path,
) -> None:
    required_paths = (model_file, config_file, embedder_dir)
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"runtime export input not found: {path}")
    if not any((embedder_dir / name).exists() for name in ("model.safetensors", "pytorch_model.bin")):
        raise FileNotFoundError(f"embedder weights not found: {embedder_dir}")


# 실제 추론에 필요한 파일을 정해진 폴더 구조의 zip으로 저장한다.
def export_runtime_bundle(
    model_file: str | Path,
    config_file: str | Path,
    embedder_dir: str | Path,
    output_file: str | Path,
) -> Path:
    model_path = Path(model_file)
    config_path = Path(config_file)
    embedder_path = Path(embedder_dir)
    output_path = Path(output_file)
    validate_export_inputs(model_path, config_path, embedder_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as bundle:
            bundle.write(model_path, "artifacts/best_model.keras")
            bundle.write(config_path, "artifacts/config.json")
            for file_path in sorted(path for path in embedder_path.rglob("*") if path.is_file()):
                archive_name = Path("embedders/bge-m3") / file_path.relative_to(embedder_path)
                compression = ZIP_STORED if file_path.suffix == ".safetensors" else ZIP_DEFLATED
                bundle.write(file_path, str(archive_name), compress_type=compression)
        os.replace(temporary_path, output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return output_path

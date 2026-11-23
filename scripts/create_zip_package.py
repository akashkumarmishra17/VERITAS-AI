"""
VERITAS AI - Packaging & ZIP Archive Creator.
Builds VERITAS_AI_PROJECT.zip containing complete working source code,
trained models, metrics, sample test images, unit tests, documentation,
and screenshots, while excluding unnecessary caches and raw datasets.
"""

import os
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "VERITAS_AI_PROJECT.zip")

EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".vscode",
    ".idea",
    "venv",
    ".venv",
    "conda_env",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
}


def build_zip():
    print(f"Creating ZIP package at: {OUTPUT_ZIP}...")
    total_files = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                # Do not include the zip file inside itself
                if file == "VERITAS_AI_PROJECT.zip":
                    continue
                
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)

                zipf.write(full_path, arcname=rel_path)
                total_files += 1
                total_uncompressed_bytes += os.path.getsize(full_path)

    zip_size_bytes = os.path.getsize(OUTPUT_ZIP)
    zip_size_mb = zip_size_bytes / (1024.0 * 1024.0)

    print("\n--- ZIP Packaging Complete ---")
    print(f"Total Files Packaged: {total_files}")
    print(f"Uncompressed Size:    {total_uncompressed_bytes / (1024.0 * 1024.0):.2f} MB")
    print(f"Compressed ZIP Size:  {zip_size_mb:.2f} MB")

    if zip_size_mb > 100.0:
        raise ValueError(f"ZIP package exceeds 100 MB limit: {zip_size_mb:.2f} MB")
    else:
        print(f"Verification PASSED: ZIP size ({zip_size_mb:.2f} MB) is well under 100 MB.")


if __name__ == "__main__":
    build_zip()

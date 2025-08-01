import csv
import hashlib
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image
from datetime import datetime


def find_image_files(source_dirs):
    """Recursively find all JPEG files in the source directories."""
    extensions = {".jpg", ".jpeg"}
    for source_dir in source_dirs:
        for path in source_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions:
                yield path


def get_exif_date(image_path):
    """Extract the original creation date from the image's EXIF data."""
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # 36867 is the tag for DateTimeOriginal
                date_str = exif_data.get(36867)
                if date_str:
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception:
        # Could be a file read error, or the file may not have EXIF data
        pass
    return None


def create_date_based_directory(destination_dir: Path, date: datetime) -> Path:
    """Create a date-based directory (YYYY-MM) if it doesn't exist."""
    month_dir = destination_dir / f"{date.year}-{date.month:02d}"
    month_dir.mkdir(parents=True, exist_ok=True)
    return month_dir


def get_unique_filename(destination_path: Path) -> Path:
    """Generate a unique filename if the destination path already exists."""
    if not destination_path.exists():
        return destination_path

    parent = destination_path.parent
    stem = destination_path.stem
    suffix = destination_path.suffix

    counter = 1
    while True:
        new_stem = f"{stem}-{counter}"
        new_path = parent / (new_stem + suffix)
        if not new_path.exists():
            return new_path
        counter += 1


def transfer_file(
    image_path: Path, destination_dir: Path, date: datetime | None, copy: bool
) -> Path:
    """Move or copy an image to the appropriate directory."""
    if date:
        target_dir = create_date_based_directory(destination_dir, date)
    else:
        target_dir = destination_dir / "missing_date"
        target_dir.mkdir(exist_ok=True)

    destination_path = get_unique_filename(target_dir / image_path.name)

    if copy:
        shutil.copy2(str(image_path), str(destination_path))
    else:
        shutil.move(str(image_path), str(destination_path))
    return destination_path


def calculate_hash(image_path: Path) -> str:
    """Calculate the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(image_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_duplicate_report(
    destination_dir: Path, duplicates: defaultdict[str, list[tuple[Path, Path]]]
):
    """Write a report of duplicate files to duplicates.csv."""
    report_path = destination_dir / "duplicates.csv"
    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "new_filepath", "old_filepath"])
        for hash_val, file_list in duplicates.items():
            if len(file_list) > 1:
                for old_path, new_path in file_list:
                    writer.writerow([hash_val, str(new_path), str(old_path)])



def get_files_to_delete(report_path: Path) -> list[Path]:
    """
    Reads a duplicate report and returns a list of files to be deleted.

    Args:
        report_path: The path to the duplicates.csv file.

    Returns:
        A list of paths for files that should be deleted.
    """
    try:
        with open(report_path, "r", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            duplicates = defaultdict(list)
            for row in reader:
                if len(row) >= 2:
                    file_hash, new_filepath = row[0], row[1]
                    duplicates[file_hash].append(Path(new_filepath))
    except (FileNotFoundError, StopIteration):
        return []

    files_to_delete = []
    for _, file_list in duplicates.items():
        if len(file_list) > 1:
            # Sort by path to ensure consistent "first" file
            sorted_files = sorted(file_list, key=lambda p: str(p))
            # Add all but the first file to the deletion list
            files_to_delete.extend(sorted_files[1:])

    return files_to_delete

import pytest
import csv
import hashlib
from collections import defaultdict
from datetime import datetime
import piexif


from PIL import Image

from organize_photos.utils import (
    calculate_hash,
    create_date_based_directory,
    find_image_files,
    get_exif_date,
    get_unique_filename,
    transfer_file,
    write_duplicate_report,
    get_files_to_delete,
)


@pytest.fixture
def create_test_files(tmp_path):
    """Create a temporary directory with test files."""
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "image1.jpg").touch()
    (tmp_path / "dir1" / "image2.jpeg").touch()
    (tmp_path / "dir1" / "document.txt").touch()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "image3.JPG").touch()
    (tmp_path / "dir2" / "archive.zip").touch()
    return tmp_path


def test_find_image_files(create_test_files):
    """Test that find_image_files correctly finds all JPEG files."""
    source_dir = create_test_files
    expected_files = {
        source_dir / "dir1" / "image1.jpg",
        source_dir / "dir1" / "image2.jpeg",
        source_dir / "dir2" / "image3.JPG",
    }

    found_files = set(find_image_files([source_dir]))

    assert found_files == expected_files


def test_get_exif_date(tmp_path):
    """Test that get_exif_date correctly extracts the date from EXIF data."""
    # Create an image with EXIF data
    image_with_exif_path = tmp_path / "image_with_exif.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    exif_dict = {"Exif": {piexif.ExifIFD.DateTimeOriginal: b"2023:01:01 12:30:00"}}
    exif_bytes = piexif.dump(exif_dict)
    img.save(image_with_exif_path, "jpeg", exif=exif_bytes)

    # Create an image without EXIF data
    image_without_exif_path = tmp_path / "image_without_exif.jpg"
    img_no_exif = Image.new("RGB", (100, 100), color="blue")
    img_no_exif.save(image_without_exif_path, "jpeg")

    # Test the function
    expected_date = datetime(2023, 1, 1, 12, 30, 0)
    assert get_exif_date(image_with_exif_path) == expected_date
    assert get_exif_date(image_without_exif_path) is None


def test_create_date_based_directory(tmp_path):
    """Test that the date-based directory is created correctly."""
    destination = tmp_path / "output"
    test_date = datetime(2023, 10, 26)

    date_dir = create_date_based_directory(destination, test_date)

    expected_dir = destination / "2023-10"
    assert date_dir == expected_dir
    assert expected_dir.is_dir()


def test_move_image_with_date(tmp_path):
    """Test moving an image with a date."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    destination_dir = tmp_path / "destination"
    destination_dir.mkdir()

    image_path = source_dir / "test.jpg"
    image_path.touch()

    test_date = datetime(2023, 10, 26)

    transfer_file(image_path, destination_dir, test_date, copy=False)

    expected_dir = destination_dir / "2023-10"
    assert (expected_dir / "test.jpg").is_file()
    assert not image_path.exists()


def test_move_image_without_date(tmp_path):
    """Test moving an image without a date."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    destination_dir = tmp_path / "destination"
    destination_dir.mkdir()

    image_path = source_dir / "test.jpg"
    image_path.touch()

    transfer_file(image_path, destination_dir, None, copy=False)

    expected_dir = destination_dir / "missing_date"
    assert (expected_dir / "test.jpg").is_file()
    assert not image_path.exists()


def test_get_unique_filename(tmp_path):
    """Test that a unique filename is generated when a conflict exists."""

    # Create a dummy file
    existing_file = tmp_path / "test.jpg"
    existing_file.touch()

    # Test for a conflict
    new_path = get_unique_filename(existing_file)
    assert new_path.name == "test-1.jpg"

    # Test with multiple conflicts
    new_path.touch()
    another_path = get_unique_filename(existing_file)
    assert another_path.name == "test-2.jpg"


def test_get_unique_filename_no_conflict(tmp_path):
    """Test that the original filename is returned when no conflict exists."""

    # Test for no conflict
    non_existing_file = tmp_path / "test.jpg"
    new_path = get_unique_filename(non_existing_file)
    assert new_path.name == "test.jpg"


def test_calculate_hash(tmp_path):
    """Test that the SHA256 hash is calculated correctly."""

    # Create a dummy file with known content
    image_path = tmp_path / "test.jpg"
    file_content = b"this is a test"
    image_path.write_bytes(file_content)

    # Calculate the expected hash
    expected_hash = hashlib.sha256(file_content).hexdigest()

    # Calculate the actual hash
    actual_hash = calculate_hash(image_path)

    assert actual_hash == expected_hash


def test_write_duplicate_report(tmp_path):
    """Test that the duplicate report is written correctly."""

    destination_dir = tmp_path

    # Create some dummy paths for the report. These files don't need to exist.
    p = tmp_path / "data"
    file1 = p / "file1.jpg"
    file2 = p / "sub" / "file2.jpg"
    file3 = p / "file3.jpg"
    file4 = p / "file4.jpg"
    file5 = p / "another" / "file5.jpg"

    duplicates = defaultdict(list)
    # The "old" paths don't matter here, so we'll just make them the same as the new
    duplicates["hash1"].extend([(file1, file1), (file2, file2)])
    duplicates["hash2"].append((file3, file3))  # Not a duplicate
    duplicates["hash3"].extend([(file4, file4), (file5, file5)])

    write_duplicate_report(destination_dir, duplicates)

    report_path = destination_dir / "duplicates.csv"
    assert report_path.is_file()

    with open(report_path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["hash", "new_filepath", "old_filepath"]

        rows = {tuple(row) for row in reader}
        expected_rows = {
            ("hash1", str(file1), str(file1)),
            ("hash1", str(file2), str(file2)),
            ("hash3", str(file4), str(file4)),
            ("hash3", str(file5), str(file5)),
        }
        assert rows == expected_rows


def test_copy_image_with_date(tmp_path):
    """Test copying an image with a date."""

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    destination_dir = tmp_path / "destination"
    destination_dir.mkdir()

    image_path = source_dir / "test.jpg"
    image_path.touch()

    test_date = datetime(2023, 10, 26)

    transfer_file(image_path, destination_dir, test_date, copy=True)

    expected_dir = destination_dir / "2023-10"
    assert (expected_dir / "test.jpg").is_file()
    assert image_path.exists()


def test_copy_image_without_date(tmp_path):
    """Test copying an image without a date."""

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    destination_dir = tmp_path / "destination"
    destination_dir.mkdir()

    image_path = source_dir / "test.jpg"
    image_path.touch()

    transfer_file(image_path, destination_dir, None, copy=True)

    expected_dir = destination_dir / "missing_date"
    assert (expected_dir / "test.jpg").is_file()
    assert image_path.exists()


def test_get_files_to_delete(tmp_path):
    """Test that get_files_to_delete correctly identifies files to be deleted."""
    report_path = tmp_path / "duplicates.csv"
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    file3 = tmp_path / "c.jpg"
    file4 = tmp_path / "d.jpg"

    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "new_filepath", "old_filepath"])
        writer.writerow(["hash1", str(file1), "old/a.jpg"])
        writer.writerow(["hash1", str(file2), "old/b.jpg"])
        writer.writerow(["hash2", str(file3), "old/c.jpg"])
        writer.writerow(["hash3", str(file4), "old/d.jpg"])

    files_to_delete = get_files_to_delete(report_path)

    # Expecting file2 to be deleted, as it's the second in the sorted list for hash1
    assert len(files_to_delete) == 1
    assert file2 in files_to_delete

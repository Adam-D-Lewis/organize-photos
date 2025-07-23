import pytest
import csv
from click.testing import CliRunner

from organize_photos.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_overlapping_source_and_destination_fails(runner, tmp_path):
    """Test that the CLI exits with an error if source and destination overlap."""

    # Case 1: Source and destination are the same
    result = runner.invoke(
        cli,
        ["organize", "--source", str(tmp_path), "--destination", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "Source and destination directories cannot overlap." in result.output

    # Case 2: Destination is a subdirectory of source
    dest_dir = tmp_path / "sub"
    dest_dir.mkdir()
    result = runner.invoke(
        cli,
        ["organize", "--source", str(tmp_path), "--destination", str(dest_dir)],
    )
    assert result.exit_code != 0
    assert "Source and destination directories cannot overlap." in result.output

    # Case 3: Source is a subdirectory of destination
    source_dir = tmp_path / "sub"
    result = runner.invoke(
        cli,
        ["organize", "--source", str(source_dir), "--destination", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "Source and destination directories cannot overlap." in result.output


def test_non_overlapping_paths_succeeds(runner, tmp_path):
    """Test that the CLI runs successfully with non-overlapping paths."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()

    # Create a dummy image file
    (source_dir / "image.jpg").touch()

    result = runner.invoke(
        cli,
        ["organize", "--source", str(source_dir), "--destination", str(dest_dir)],
    )
    assert result.exit_code == 0
    assert "No image files found" not in result.output


def test_multiple_sources_succeeds(runner, tmp_path):
    """Test that the CLI runs successfully with multiple source directories."""
    source_dir1 = tmp_path / "source1"
    source_dir1.mkdir()
    source_dir2 = tmp_path / "source2"
    source_dir2.mkdir()
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()

    # Create dummy image files in each source directory
    (source_dir1 / "image1.jpg").touch()
    (source_dir2 / "image2.jpg").touch()

    result = runner.invoke(
        cli,
        [
            "organize",
            "--source",
            str(source_dir1),
            "--source",
            str(source_dir2),
            "--destination",
            str(dest_dir),
        ],
    )
    assert result.exit_code == 0
    assert "Found 2 images" in result.output


def test_dedupe_deletes_duplicates_with_confirmation(runner, tmp_path):
    """Test that the dedupe command deletes duplicates after confirmation."""
    report_path = tmp_path / "duplicates.csv"
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    file1.touch()
    file2.touch()

    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "new_filepath", "old_filepath"])
        writer.writerow(["hash1", str(file1), "old/a.jpg"])
        writer.writerow(["hash1", str(file2), "old/b.jpg"])

    result = runner.invoke(cli, ["dedupe", "--report", str(report_path)], input="y\n")

    assert result.exit_code == 0
    assert "Found 1 duplicate files to delete" in result.output
    assert "Duplicate files deleted" in result.output
    assert file1.exists()
    assert not file2.exists()


def test_dedupe_aborts_on_no_confirmation(runner, tmp_path):
    """Test that the dedupe command aborts if the user says no."""
    report_path = tmp_path / "duplicates.csv"
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    file1.touch()
    file2.touch()

    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "new_filepath", "old_filepath"])
        writer.writerow(["hash1", str(file1), "old/a.jpg"])
        writer.writerow(["hash1", str(file2), "old/b.jpg"])

    result = runner.invoke(cli, ["dedupe", "--report", str(report_path)], input="n\n")

    assert result.exit_code == 1  # Aborted
    assert "Aborted!" in result.output
    assert file1.exists()
    assert file2.exists()


def test_dedupe_runs_with_yes_flag(runner, tmp_path):
    """Test that the dedupe command runs without confirmation with --yes."""
    report_path = tmp_path / "duplicates.csv"
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    file1.touch()
    file2.touch()

    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "new_filepath", "old_filepath"])
        writer.writerow(["hash1", str(file1), "old/a.jpg"])
        writer.writerow(["hash1", str(file2), "old/b.jpg"])

    result = runner.invoke(cli, ["dedupe", "--report", str(report_path), "--yes"])

    assert result.exit_code == 0
    assert "Found 1 duplicate files to delete" in result.output
    assert "Duplicate files deleted" in result.output
    assert file1.exists()
    assert not file2.exists()


def test_dedupe_handles_empty_report(runner, tmp_path):
    """Test that the dedupe command handles an empty report gracefully."""
    report_path = tmp_path / "duplicates.csv"
    report_path.touch()

    result = runner.invoke(cli, ["dedupe", "--report", str(report_path)])

    assert result.exit_code == 0
    assert "No duplicate files found to delete" in result.output


def test_dedupe_handles_report_with_no_duplicates(runner, tmp_path):
    """Test that the dedupe command handles a report with no duplicates."""
    report_path = tmp_path / "duplicates.csv"
    file1 = tmp_path / "a.jpg"
    file1.touch()

    with open(report_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "new_filepath", "old_filepath"])
        writer.writerow(["hash1", str(file1), "old/a.jpg"])

    result = runner.invoke(cli, ["dedupe", "--report", str(report_path)])

    assert result.exit_code == 0
    assert "No duplicate files found to delete" in result.output

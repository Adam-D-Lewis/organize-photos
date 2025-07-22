import pytest
from click.testing import CliRunner

from organize_photos.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_overlapping_source_and_destination_fails(runner, tmp_path):
    """Test that the CLI exits with an error if source and destination overlap."""

    # Case 1: Source and destination are the same
    result = runner.invoke(
        main, ["--source", str(tmp_path), "--destination", str(tmp_path)]
    )
    assert result.exit_code != 0
    assert "Source and destination directories cannot overlap." in result.output

    # Case 2: Destination is a subdirectory of source
    dest_dir = tmp_path / "sub"
    dest_dir.mkdir()
    result = runner.invoke(
        main, ["--source", str(tmp_path), "--destination", str(dest_dir)]
    )
    assert result.exit_code != 0
    assert "Source and destination directories cannot overlap." in result.output

    # Case 3: Source is a subdirectory of destination
    source_dir = tmp_path / "sub"
    result = runner.invoke(
        main, ["--source", str(source_dir), "--destination", str(tmp_path)]
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
        main, ["--source", str(source_dir), "--destination", str(dest_dir)]
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
        main,
        [
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

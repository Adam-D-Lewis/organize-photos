import logging
from collections import defaultdict
from pathlib import Path

import click
from tqdm import tqdm

from .utils import (
    calculate_hash,
    find_image_files,
    get_exif_date,
    get_files_to_delete,
    transfer_file,
    write_duplicate_report,
)


@click.group()
def cli():
    """A CLI tool to organize photos by date and find duplicates."""
    pass


@cli.command()
@click.option(
    "--source",
    multiple=True,
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="One or more source directories to scan for images.",
)
@click.option(
    "--destination",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="The destination directory to organize photos into.",
)
@click.option(
    "--copy",
    is_flag=True,
    default=False,
    help="Copy files instead of moving them.",
)
def organize(source: tuple[Path, ...], destination: Path, copy: bool):
    """Organize photos from source directories into a destination directory."""
    destination.mkdir(exist_ok=True)

    # Validate paths
    for s in source:
        s_resolved = s.resolve()
        d_resolved = destination.resolve()
        if (
            s_resolved == d_resolved
            or s_resolved in d_resolved.parents
            or d_resolved in s_resolved.parents
        ):
            raise click.UsageError("Source and destination directories cannot overlap.")

    # Set up logging
    error_log_path = destination / "errors.log"
    logging.basicConfig(
        filename=error_log_path,
        level=logging.ERROR,
        format="%(asctime)s - %(message)s",
    )

    click.echo(f"Scanning {', '.join(str(s) for s in source)} for images...")
    image_files = list(find_image_files(source))
    if not image_files:
        click.echo("No image files found.")
        return

    click.echo(f"Found {len(image_files)} images. Processing...")

    hashes = defaultdict(list)
    with tqdm(total=len(image_files), desc="Organizing photos") as pbar:
        for image_file in image_files:
            try:
                # 1. Calculate hash
                file_hash = calculate_hash(image_file)

                # 2. Get EXIF date
                date = get_exif_date(image_file)

                # 3. Move or copy file
                new_path = transfer_file(image_file, destination, date, copy)
                hashes[file_hash].append((image_file, new_path))

            except Exception as e:
                logging.error(f"Error processing {image_file}: {e}")
            finally:
                pbar.update(1)

    # 4. Write duplicate report
    write_duplicate_report(destination, hashes)

    click.echo("Done!")


@cli.command()
@click.option(
    "--report",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="The duplicates.csv report to process.",
)
@click.option(
    "--yes",
    is_flag=True,
    default=False,
    help="Skip confirmation and proceed with deletion.",
)
def dedupe(report: Path, yes: bool):
    """Delete duplicate files based on the duplicates.csv report."""
    files_to_delete = get_files_to_delete(report)

    if not files_to_delete:
        click.echo("No duplicate files found to delete.")
        return

    click.echo(f"Found {len(files_to_delete)} duplicate files to delete.")

    if not yes:
        click.confirm("Do you want to proceed with deleting these files?", abort=True)

    with tqdm(total=len(files_to_delete), desc="Deleting duplicates") as pbar:
        for f in files_to_delete:
            try:
                if f.exists():
                    f.unlink()
                    pbar.set_postfix_str(f"Deleted {f}")
                else:
                    pbar.set_postfix_str(f"Skipped {f} (not found)")
            except Exception as e:
                logging.error(f"Error deleting {f}: {e}")
                pbar.set_postfix_str(f"Error deleting {f}")
            finally:
                pbar.update(1)

    click.echo("Duplicate files deleted.")


if __name__ == "__main__":
    cli()

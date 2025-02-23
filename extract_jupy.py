import nbformat
from nbclient import NotebookClient
import jupytext
from pathlib import Path

DOCS_DIR = "docs"
OUTPUT_DIR = "baseline"


def collect_files(dir: Path) -> list[Path]:
    """
    Helper function to collect the jupytext files in a directory.
    """
    files = []
    for file in dir.iterdir():
        if file.name.endswith(".py"):  # Jupytext files
            filepath = file.resolve()
            files.append(filepath)
    return files


def retrieve_images(cell: dict, output_dir: Path) -> None:
    """
    Help functions to retrieve images from a cell.
    """
    for jdx, output in enumerate(cell.get("outputs", [])):
        output_type = output.get("output_type")
        if output_type != "display_data" and "image/png" not in output["data"]:
            continue
        img_data = output["data"]["image/png"]
        img_path = output_dir / f"{file}_cell={idx}_output={jdx}.png"
        with open(img_path, "wb") as img_file:
            img_file.write(img_data.encode("utf-8"))
        print(f"Saved {img_path}")


def run_source(file: Path) -> None:
    """
    Runs the jupytext and retrieve_images
    """
    # Read notebook
    with open(file) as f:
        notebook = jupytext.read(f)
    # Execute the notebook
    print(f"Executing {file}")
    client = NotebookClient(notebook)
    client.execute()
    print(f"Executed {file}")
    # Save output images
    for idx, cell in enumerate(notebook["cells"]):
        retrieve_images(cell)


if __name__ == "__main__":
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    print(f"Made output directory {OUTPUT_DIR}")
    import multiprocessing as mp

    files = collect_files(Path(DOCS_DIR))
    with mp.Pool(mp.cpu_count() - 1) as p:
        for _ in p.imap_unordered(run_source, files):
            pass
    print("Done")

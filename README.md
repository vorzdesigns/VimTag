# VimTag

VimTag is a command-line tool designed for batch editing metadata (tags) of audio files using your preferred text editor, Vim or Nvim. It simplifies the process of updating tags like title, artist, album, and more, across multiple audio files and can automatically rename files based on their new title.

## Features

*   **Batch Metadata Editing**: Edit tags for multiple audio files in a single session.
*   **Vim/Nvim Integration**: Leverages the power and familiarity of Vim/Nvim for editing metadata.
*   **Wide Format Support**: Works with popular audio formats including MP3, FLAC, M4A, OGG, Opus, and WAV.
*   **Comprehensive Tag Editing**: Modify common metadata tags: title, artist, album, genre, track number, and date.
*   **Automatic File Renaming**: Optionally renames audio files based on the updated 'title' tag.
*   **User-Friendly Editing Format**: Presents metadata in a clearly structured temporary file with instructions.
*   **Filename Sanitization**: Ensures new filenames are valid and safe for the filesystem.

## Requirements

*   Python 3.12 or newer
*   [mutagen](https://mutagen.readthedocs.io/) library (`>=1.47.0`)
*   Vim or Nvim installed and accessible in your system's PATH.

## Installation

1.  **Clone the repository or download the script:**
    ```bash
    # If you have git installed
    # git clone <repository_url>
    # cd VimTag
    # Otherwise, just download main.py
    ```

2.  **Ensure Python 3.12+ is installed.** You can check your Python version with:
    ```bash
    python --version
    # or
    python3 --version
    ```

3.  **Install the `mutagen` library:**
    If you have `pyproject.toml` in the project root, you can install dependencies using pip:
    ```bash
    pip install .
    ```
    Alternatively, install `mutagen` directly:
    ```bash
    pip install mutagen>=1.47.0
    ```

4.  **Ensure Vim or Nvim is installed** and can be launched from your terminal (e.g., by typing `vim` or `nvim`).

5.  **Compile with PyInstaller (Recommended):**
    ```bash
    pip install pyinstaller
    pyinstaller --onefile main.py
    ```
    This will create a single executable in the `dist` directory.

## Usage

Run the script from your terminal, providing the path to the folder containing your audio files:

import sys
import os
import mutagen
import tempfile
import subprocess
import shutil # For shutil.which

# Define supported audio file extensions
SUPPORTED_EXTENSIONS = ['.mp3', '.flac', '.m4a', '.ogg', '.opus', '.wav']
EDITABLE_TAGS = ['title', 'artist', 'album', 'genre', 'tracknumber', 'date']

# Header for the temporary file to provide instructions
TEMP_FILE_HEADER = """# vimtag_metadata_editor
# Instructions:
# - Edit the values for each tag (title, artist, etc.).
# - Do NOT edit the '# File:' lines or the '--- Metadata ---' / '--- End Metadata ---' separators.
# - To remove/clear a tag, leave its value blank with a space behind it.
# - Save and close Vim/Nvim to apply changes.
# --------------------------------------------------
"""

METADATA_BLOCK_START = "# --- Metadata ---"
METADATA_BLOCK_END = "# --- End Metadata ---"
FILE_PATH_PREFIX = "# File: "

def sanitize_filename(filename):
    """
    Sanitizes a string to be a valid filename.
    Removes or replaces characters that are problematic in filenames.
    """
    if not filename:
        return ""
    # Characters to remove entirely
    # You can expand this list
    invalid_chars_remove = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    # Characters to replace (e.g., with an underscore)
    # invalid_chars_replace = {' ': '_'} # Example: replace spaces with underscores

    sanitized = filename
    for char in invalid_chars_remove:
        sanitized = sanitized.replace(char, '')
    
    # for char, replacement in invalid_chars_replace.items():
    #     sanitized = sanitized.replace(char, replacement)

    # Limit length if necessary (optional)
    # max_len = 200 
    # sanitized = sanitized[:max_len]

    # Remove leading/trailing whitespace and dots (problematic on Windows)
    sanitized = sanitized.strip(" .")
    
    if not sanitized: # If all characters were invalid or removed
        return "_renamed_file_" # Default fallback name
    return sanitized

def get_metadata(file_path):
    """
    Extracts metadata from an audio file.
    Returns a dictionary of metadata or None if an error occurs.
    """
    try:
        audio = mutagen.File(file_path, easy=True)
        if audio:
            metadata = {}
            for tag_name in EDITABLE_TAGS:
                metadata[tag_name] = audio.get(tag_name, [None])[0]
            metadata['filepath'] = file_path # Crucial for linking back
            return metadata
    except mutagen.MutagenError as e:
        print(f"Error processing {os.path.basename(file_path)}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with {os.path.basename(file_path)}: {e}")
    return None

def format_metadata_for_editing(all_songs_metadata):
    """
    Formats the list of metadata dictionaries into a string for Vim editing.
    """
    content = [TEMP_FILE_HEADER]
    for metadata in all_songs_metadata:
        content.append(f"{FILE_PATH_PREFIX}{metadata['filepath']}")
        content.append(METADATA_BLOCK_START)
        for tag_name in EDITABLE_TAGS:
            value = metadata.get(tag_name)
            content.append(f"{tag_name}: {value if value is not None else ''}")
        content.append(METADATA_BLOCK_END)
        content.append("") # Add a blank line for readability
    return "\n".join(content)

def parse_edited_metadata(edited_content_str):
    """
    Parses the string content from Vim back into a list of metadata dictionaries.
    """
    updated_songs_metadata = []
    current_song_info = None
    lines = edited_content_str.splitlines()

    for line in lines:
        line = line.strip()
        if line.startswith(FILE_PATH_PREFIX):
            if current_song_info: # Save previous song if any
                updated_songs_metadata.append(current_song_info)
            current_song_info = {'filepath': line[len(FILE_PATH_PREFIX):].strip()}
        elif line == METADATA_BLOCK_START and current_song_info:
            continue # Just a marker
        elif line == METADATA_BLOCK_END and current_song_info:
            if current_song_info: # Finalize current song
                updated_songs_metadata.append(current_song_info)
                current_song_info = None
        elif ':' in line and current_song_info:
            if line.startswith("#"): # Skip comment lines within metadata block if any
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in EDITABLE_TAGS:
                current_song_info[key] = value if value else None # Store empty as None
    
    if current_song_info: # Catch the last song if file doesn't end with METADATA_BLOCK_END properly
        updated_songs_metadata.append(current_song_info)
        
    return updated_songs_metadata


def find_editor():
    """Finds nvim or vim."""
    editor = shutil.which('nvim')
    if editor:
        return editor
    editor = shutil.which('vim')
    if editor:
        return editor
    return None

def open_editor(temp_file_path):
    """Opens the editor with the temporary file."""
    editor_cmd = find_editor()
    if not editor_cmd:
        print("Error: Could not find 'nvim' or 'vim' in your PATH.")
        print("Please install one of them or ensure it's in your PATH.")
        return False

    try:
        # For Windows, subprocess.run typically handles paths correctly.
        # For Linux/macOS, shell=True might be needed if editor_cmd is just 'vim' and relies on PATH.
        # However, shutil.which returns the full path, so shell=False is safer.
        process = subprocess.run([editor_cmd, temp_file_path], check=False)
        return process.returncode == 0
    except FileNotFoundError:
        print(f"Error: Editor '{editor_cmd}' not found, even after shutil.which.")
        return False
    except Exception as e:
        print(f"Error opening editor: {e}")
        return False


def apply_metadata_changes(updated_songs_metadata):
    """
    Applies the edited metadata back to the audio files and renames them.
    """
    if not updated_songs_metadata:
        print("No changes to apply.")
        return

    print("\nApplying changes...")
    for song_data in updated_songs_metadata:
        original_filepath = song_data.get('filepath') # Store original path for renaming
        if not original_filepath or not os.path.exists(original_filepath):
            print(f"Skipping invalid or missing file: {original_filepath}")
            continue

        current_filepath_for_metadata = original_filepath # Path to use for loading/saving metadata

        try:
            audio = mutagen.File(current_filepath_for_metadata, easy=True)
            if not audio:
                print(f"Could not load audio file for writing: {os.path.basename(current_filepath_for_metadata)}")
                continue
            
            print(f"Updating: {os.path.basename(current_filepath_for_metadata)}")
            metadata_changed = False
            for tag_name in EDITABLE_TAGS:
                new_value = song_data.get(tag_name)
                # Ensure current_value is fetched correctly, especially if it's a list
                current_tag_value_list = audio.get(tag_name)
                current_value = current_tag_value_list[0] if current_tag_value_list else None


                if new_value is None or new_value == '': # User wants to delete/clear the tag
                    if tag_name in audio:
                        del audio[tag_name]
                        print(f"  - Cleared {tag_name}")
                        metadata_changed = True
                elif str(current_value) != str(new_value): # Compare as strings to handle type nuances
                    audio[tag_name] = new_value
                    print(f"  - Set {tag_name}: {new_value}")
                    metadata_changed = True
            
            if metadata_changed:
                audio.save()
                print(f"  Saved metadata changes for {os.path.basename(current_filepath_for_metadata)}")
            else:
                print(f"  No metadata changes detected for {os.path.basename(current_filepath_for_metadata)}")

            # --- Add file renaming logic ---
            new_title = song_data.get('title')
            if new_title and metadata_changed: # Only rename if title exists and metadata was actually saved
                sanitized_title = sanitize_filename(new_title)
                if sanitized_title:
                    original_dir = os.path.dirname(current_filepath_for_metadata)
                    _, original_ext = os.path.splitext(current_filepath_for_metadata)
                    
                    new_filename_base = sanitized_title
                    new_filename = new_filename_base + original_ext
                    new_filepath = os.path.join(original_dir, new_filename)

                    # Ensure we are not trying to rename to the same name (case-insensitive check for safety on Windows)
                    if os.path.normcase(current_filepath_for_metadata) != os.path.normcase(new_filepath):
                        if os.path.exists(new_filepath):
                            print(f"  - Warning: File '{new_filename}' already exists. Skipping rename for '{os.path.basename(current_filepath_for_metadata)}'.")
                        else:
                            try:
                                os.rename(current_filepath_for_metadata, new_filepath)
                                print(f"  - Renamed file to: {new_filename}")
                                # Update filepath in song_data if we were to use it further (not strictly needed here)
                                # song_data['filepath'] = new_filepath 
                            except OSError as e:
                                print(f"  - Error renaming file '{os.path.basename(current_filepath_for_metadata)}' to '{new_filename}': {e}")
                    else:
                        print(f"  - New title '{new_title}' results in the same filename. No rename needed.")

        except mutagen.MutagenError as e:
            print(f"Error saving changes to {os.path.basename(current_filepath_for_metadata)}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving/renaming {os.path.basename(current_filepath_for_metadata)}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <folder_path_with_songs>")
        sys.exit(1)

    folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        print(f"Error: The path '{folder_path}' is not a valid directory.")
        sys.exit(1)

    print(f"Processing songs in folder: {folder_path}")
    
    all_songs_metadata = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(filename)
            if ext.lower() in SUPPORTED_EXTENSIONS:
                print(f"Processing audio file: {filename}")
                metadata = get_metadata(file_path)
                if metadata:
                    all_songs_metadata.append(metadata)
                    # Print initial metadata (optional)
                    # print(f"  Title: {metadata.get('title')}")
                    # print(f"  Artist: {metadata.get('artist')}")
                    # print(f"  Album: {metadata.get('album')}")
                    # print(f"  Track: {metadata.get('tracknumber')}") # Corrected from 'track'
            # else:
            #     print(f"Skipping non-audio file: {filename}") # Can be verbose
    
    if not all_songs_metadata:
        print("No supported audio files found or no metadata could be extracted.")
        sys.exit(0)

    print(f"\nFound {len(all_songs_metadata)} audio file(s) to process.")

    # Prepare data for Vim
    metadata_text_for_editing = format_metadata_for_editing(all_songs_metadata)

    # Create a temporary file
    temp_file_descriptor, temp_file_path = tempfile.mkstemp(suffix=".txt", prefix="vimtag_", text=True)
    try:
        with os.fdopen(temp_file_descriptor, 'w', encoding='utf-8') as tmpfile:
            tmpfile.write(metadata_text_for_editing)
        
        print(f"\nOpening metadata for editing in Vim/Nvim: {temp_file_path}")
        print("Please edit the tags, then save and close the editor to apply changes.")
        
        # Open Vim/Nvim with this data
        if not open_editor(temp_file_path):
            print("Editor was not closed successfully or could not be opened. Aborting.")
            sys.exit(1)

        # Read changes from Vim
        with open(temp_file_path, 'r', encoding='utf-8') as tmpfile:
            edited_content = tmpfile.read()
        
        updated_metadata_list = parse_edited_metadata(edited_content)
        
        if not updated_metadata_list:
            print("No metadata was parsed from the editor. Did you save the file?")
        else:
            # Write changes back to files
            apply_metadata_changes(updated_metadata_list)

    except Exception as e:
        print(f"An error occurred during the editing process: {e}")
    finally:
        # Clean up the temporary file
        print(f"Cleaning up temporary file: {temp_file_path}")
        os.remove(temp_file_path)

    print("\nProcessing complete.")

if __name__ == "__main__":
    main()

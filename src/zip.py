import zipfile
import os

def zip_profile(folder_path, output_dir, extension=".streamDeckProfile"):
    """
    Zip a folder into output_dir with the given extension.
    Clears output_dir before creating the zip.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Base name
    base_name = os.path.basename(folder_path.rstrip("/\\"))
    output_zip = os.path.join(output_dir, base_name + extension)

    # Create the zip
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

    print(f"Folder zipped to: {output_zip}")
    return output_zip
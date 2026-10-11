import zipfile
import os
import shutil

def unzip_profile(profile_file, output_dir):
    """
    Unzip a .streamDeckProfile (or zip) file into output_dir for editing.
    Clears output_dir before extracting.
    """
    # Clear output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Base name for unzipped folder
    base_name, _ = os.path.splitext(os.path.basename(profile_file))
    unzipped_dir = os.path.join(output_dir, base_name)

    # Extract all contents
    with zipfile.ZipFile(profile_file, 'r') as zip_ref:
        zip_ref.extractall(unzipped_dir)

    print(f"Profile unzipped to: {unzipped_dir}")
    return unzipped_dir

unzip_profile("./Lightroom.streamDeckProfile", "./output")
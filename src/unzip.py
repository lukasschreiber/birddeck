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

if __name__ == "__main__":
    import argparse
    from paths import ROOT_DIR, OUTPUT_DIR

    parser = argparse.ArgumentParser(description="Extract a Stream Deck profile.")
    parser.add_argument("profile", nargs="?", type=str,
                        default=str(ROOT_DIR / "examples" / "Lightroom.streamDeckProfile"))
    args = parser.parse_args()
    unzip_profile(args.profile, OUTPUT_DIR / "extracted")

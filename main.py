import csv
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from apkutils2 import APK, ARSCParser

ALL_BRAWLERS_CODENAMES = []
ALL_SKINS_CODENAMES = []


class Mod:
    def __init__(self, apk_path):
        self.apk_path = apk_path
        self.apk_temp_path = self.extract_apk()
        self.apk_name = self.get_app_name()
        self.version = self.get_version_name()
        self.offline = self.check_offline()
        self.new_brawlers = self.check_new_brawlers()
        self.new_skins = self.check_added_skins()
        self.has_custom_sc = self.check_custom_sc()
        self.has_custom_icons = self.check_custom_icons()
        self.has_modified_skins = self.check_modified_skins()
        self.has_new_models = self.check_new_models()
        self.discord_link = ""  # Placeholder, to be filled in manually later
        self.download_link = ""  # Placeholder, to be filled in manually later
        self.creator = ""  # Placeholder, to be filled in manually later
        self.all_brawl_status = ""  # Placeholder, to be filled in manually later
        self.author = ""

    def get_version_name(self):
        try:
            apk = APK(str(self.apk_path))
            manifest = apk.get_manifest()
            version_name = manifest.get('@android:versionName')
            if version_name is None:
                version_name = manifest.get('versionName')
            return version_name
        except Exception as e:
            print(f"Error parsing APK {self.apk_path}: {e}")
            return None

    def get_app_name(self):
        try:

            # If the strings.xml isn't available, parse the resources.arsc file
            arsc_data = None
            with open(self.apk_path, 'rb') as apk_file:
                with zipfile.ZipFile(apk_file, 'r') as z:
                    if 'resources.arsc' in z.namelist():
                        arsc_data = z.read('resources.arsc')

            if arsc_data:
                # Assuming ARSCParser is implemented correctly
                parser = ARSCParser(arsc_data)

                # Get the package name from the manifest
                with open(self.apk_path, 'rb') as apk_file:
                    apk = APK(apk_file)
                    manifest = apk.get_manifest()
                    package_name = manifest.get("@package")

                if package_name:
                    app_name = parser.get_string(package_name, 'app_name')
                    if app_name:
                        return app_name[1]
            return Path(self.apk_path).stem
        except Exception as e:
            print(f"Error extracting app name from APK {self.apk_path}: {e}")
            return Path(self.apk_path).stem

    def extract_apk(self):
        temp_dir = tempfile.mkdtemp()
        try:
            shutil.unpack_archive(self.apk_path, temp_dir, 'zip')
        except Exception as e:
            print(f"Failed to extract APK {self.apk_path}: {e}")
            shutil.rmtree(temp_dir)
            return None
        return temp_dir

    def check_offline(self):
        if os.path.exists(os.path.join(self.apk_temp_path, "assets", "server")):
            return True
        return False

    def check_new_brawlers(self):
        characters_path = os.path.join(self.apk_temp_path, "assets", "csv_logic", "characters.csv")
        all_brawlers = get_first_column_values_for_specific_value(characters_path, "Type", "Hero")
        new_brawlers = 0
        for brawler in all_brawlers:
            if brawler not in ALL_BRAWLERS_CODENAMES:
                new_brawlers += 1
        return new_brawlers

    def cleanup(self):
        if self.apk_temp_path:
            shutil.rmtree(self.apk_temp_path)

    # Placeholder functions to check for custom content
    def check_custom_sc(self):
        return "Unkown"

    def check_custom_icons(self):
        return "Unkown"

    def check_modified_skins(self):
        return "Unkown"

    def check_added_skins(self):
        skin_confs_path = os.path.join(self.apk_temp_path, "assets", "csv_logic", "skin_confs.csv")
        all_brawlers = get_all_values(skin_confs_path, 0)
        new_skins = 0
        for brawler in all_brawlers:
            if brawler not in ALL_SKINS_CODENAMES:
                new_skins += 1
        return new_skins - self.new_brawlers

    def check_new_models(self):
        return "Unkown"


# Function to process APK files and create a CSV database
def process_apks(input_folder, output_csv):
    input_path = Path(input_folder)
    if not input_path.is_dir():
        print(f"Error: The path '{input_folder}' is not a directory or does not exist.")
        return

    # Define CSV header
    csv_header = [
        "apk_name", "apk_path", "version", "offline", "added_skins", "added_brawlers"
    ]

    # Open CSV file for writing
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_header)

        # Iterate over all APK files in the input directory
        for apk_file in input_path.iterdir():
            if apk_file.is_file() and apk_file.suffix.lower() == '.apk':
                print(f"Processing {apk_file.name}...")

                # Create Mod object
                mod = Mod(apk_file)

                # Write data to CSV
                writer.writerow([
                    mod.apk_name, mod.apk_path, mod.version, mod.offline, mod.new_skins, mod.new_brawlers
                ])

                # Clean up temporary files
                mod.cleanup()

                print(f"Processed {apk_file.name} successfully.\n")


# Function to return a list of first column values that have a specific value in a given column
def get_first_column_values_for_specific_value(csv_file, column_name, value):
    result = []
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get(column_name) == value:
                    result.append(row[reader.fieldnames[0]])
    except Exception as e:
        print(f"Error reading CSV file {csv_file}: {e}")
    return result


def get_all_values(csv_file, index=0):
    result = []
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                result.append(row[index])
    except Exception as e:
        print(f"Error reading CSV file {csv_file}: {e}")
    return result


# Main function
def main():
    global ALL_BRAWLERS_CODENAMES, ALL_SKINS_CODENAMES
    # Specify your APK folder path and output CSV path here
    input_folder = r"C:\Dev\Python\modcombiner\all mods\v29 offline"
    output_csv = r"apk_database.csv"
    latest_brawl_stars_apk_path = "latest_brawl_stars_apk"
    ALL_BRAWLERS_CODENAMES = get_first_column_values_for_specific_value(
        os.path.join(latest_brawl_stars_apk_path, "assets", "csv_logic", "characters.csv"), "Type", "Hero")
    ALL_SKINS_CODENAMES = get_all_values(
        os.path.join(latest_brawl_stars_apk_path, "assets", "csv_logic", "skin_confs.csv"), 0)
    # Confirm the path exists
    if not Path(input_folder).exists():
        print(f"The specified folder does not exist: {input_folder}")
        return

    # Process APKs and create CSV
    process_apks(input_folder, output_csv)


if __name__ == "__main__":
    main()

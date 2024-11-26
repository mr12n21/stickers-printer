import os
import xml.etree.ElementTree as ET

SMB_DIR = ""
OUTPUT_DIR = ""
OUTPUT_FILE = ""

def process_xml_files():
    for file_name in os.listdir(SMB_DIR):
        if file_name.endswith(".xml"):
            file_path = os.path.join(SMB_DIR, file_name)
            try:
                #data
                tree = ET.parse(file_path)
                root = tree.getroot()
                #data extraction
                accommodation_type = root.findtext("type")
                code = map_accommodation_type(accommodation_type)
                output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
                with open(output_path, "a") as output_file:
                    output_file.write(f"{code}\n")
                #move to
                archive_path = os.path.join(OUTPUT_DIR, file_name)
                os.rename(file_path, archive_path)
                print(f"Processed and archived: {file_name}")
            except Exception as e:
                print(f"Error processing {file_name}: {e}")

def map_accommodation_type(accommodation_type):
    mapping = {
        #data testing model
        "p1": "A",
        "p2": "K",
        "p3": "M",
    }
    return mapping.get(accommodation_type, "N")
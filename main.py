import tkinter, os, datetime, shutil, random, subprocess
import xml.etree.ElementTree as ET
from tkinter import filedialog
tkinter.Tk().withdraw()

print("Select .RPF file to convert")
rpf_path = tkinter.filedialog.askopenfilename(title="Select RPF file", filetypes=[("RPF files", "*.rpf")])
print(f"\n--- RPF PATH ---\n{rpf_path}")

folder_name = f"rpf-convert_{datetime.datetime.now().strftime('%H-%M-%S')}"
output_path = os.path.join(os.path.dirname(rpf_path), folder_name)
os.mkdir(output_path)
print(f"\n--- SAVE FOLDER ---\n{folder_name}")



print("\n--- START UNPACK ---")
try:
    # separated into two because PowerShell is fucking stupid and doesnt understand basic fucking sense (i spend a little time on this :D)
    call = "cd 'C:/Program Files/gtautil-2.2.7';"
    call2 = f"gtautil extractarchive --input '{rpf_path}' --output '{output_path}'"
    subprocess.run(['powershell', call, call2])
except Exception as e:
    print(f"Something bad happened:\n{e}")

os.chdir(output_path)
root_path = os.getcwd()

print("\n--- TRANSFERRING FILES ---")

data = []
stream = []

for root, dirs, files in os.walk(root_path):
    if files:
        for file in files:
            if file.endswith(".meta"):
                if file.startswith("dlctext") or file.startswith("contentunlocks"):
                    print(f"Found data file: {file} | Deleted - Unneeded")
                else:
                    print(f"Found data file: {file} | Moved to data folder")
                    data.append(os.path.join(root, file))
            if file.endswith((".ytd", ".yft", ".ydr", ".png", ".dds", ".bmp", ".jpg", ".jpeg")):
                print(f"Found stream file: {file} | Moved to stream folder")
                stream.append(os.path.join(root, file))

# done because some devs are stupid and premake the folders
os.mkdir(os.path.join(root_path, "tmp_data"))
os.mkdir(os.path.join(root_path, "tmp_stream"))

for file in data:
    os.rename(file, os.path.join(root_path, "tmp_data", os.path.basename(file)))

for file in stream:
    os.rename(file, os.path.join(root_path, "tmp_stream", os.path.basename(file)))

for root, dirs, files in os.walk(root_path):
    for file in files:
        if not file.endswith((".meta", ".ytd", ".yft", ".ydr", ".png", ".dds", ".bmp", ".jpg", ".jpeg")):
            os.remove(os.path.join(root, file))
    for dir in dirs:
        if dir not in ("tmp_data", "tmp_stream"):
            shutil.rmtree(os.path.join(root, dir))

print("\n--- DELETED ORIGINAL FOLDERS/FILES ---")

os.rename(os.path.join(root_path, "tmp_data"), os.path.join(root_path, "data"))
os.rename(os.path.join(root_path, "tmp_stream"), os.path.join(root_path, "stream"))

vehicle_name = ET.parse(os.path.join(root_path, "data", "vehicles.meta")).getroot().find("InitDatas").find("Item").find("modelName").text

print(f"\nSuccessfully converted '{vehicle_name}' to FiveM ready")

print(f"\nCurrent vehicle name: '{vehicle_name}'")
change_name = input("Do you want to change the vehicle's name? (Y/n) ")
if change_name.lower() == "y":
    print("\n--- NAME CHANGE ---")
    new_name = input("Enter a new name for the vehicle (Will change all necessary metas and stream files): ")
    game_name = input("Enter the game name (eg. 'zep's Porsche'): ")

    modkit = False
    kitnum = str(random.randrange(1000000, 25000000, 5))
    kitname = f"{kitnum}_{new_name}_modkit"

    warnings = []

    # data files
    for root, dirs, files in os.walk(os.path.join(root_path, "data")):
        for file in files:
            f_root = ET.parse(os.path.join(root_path, "data", file)).getroot()

            if f_root.tag == "CVehicleModelInfo__InitDataList":
                item = f_root.find("InitDatas").find("Item")

                item.find("modelName").text = new_name
                item.find("txdName").text = new_name
                item.find("handlingId").text = new_name
                item.find("gameName").text = game_name
            if f_root.tag == "CVehicleModelInfoVarGlobal":
                if f_root.find("Kits").find("Item").find("kitName").text != "0_default_modkit":
                    f_root.find("Kits").find("Item").find("kitName").text = kitname
                    f_root.find("Kits").find("Item").find("id").attrib['value'] = kitnum
                    modkit = True
            if f_root.tag == "CVehicleModelInfoVariation":
                f_root.find("variationData").find("Item").find("modelName").text = new_name
                if modkit:
                    f_root.find("variationData").find("Item").find("kits").find("Item").text = kitname
            if f_root.tag == "CHandlingDataMgr":
                f_root.find("HandlingData").find("Item").find("handlingName").text = new_name
                if float(f_root.find("HandlingData").find("Item").find("fMass").attrib['value']) > 5000:
                    warnings.append("!!! WARNING: The mass of this vehicle is abnormally high (>5000) !!!")
                if "CSpecialFlightHandlingData" in f_root.find("HandlingData").find("Item").find("SubHandlingData").findall("Item"):
                    warnings.append("!!!WARNING: This vehicle has special flight handling !!!")

            # gta is picky so i write it in binary mode
            with open(os.path.join(root, file), "wb") as f:
                f.write(ET.tostring(f_root, encoding="utf-8"))
                f.close()

    # stream files
    for root, dirs, files in os.walk(os.path.join(root_path, "stream")):
        for file in files:
            f_name = file.split(".")[0]
            if f_name.startswith(vehicle_name):
                if len(f_name) != len(vehicle_name):
                    if f_name.endswith("_hi"):
                        try:
                            os.rename(os.path.join(root, file), os.path.join(root, file.replace(vehicle_name, new_name)))
                        except:
                            pass
                    elif f_name.endswith("+hi"):
                        try:
                            os.rename(os.path.join(root, file), os.path.join(root, file.replace(vehicle_name, new_name)))
                        except:
                            pass
                else:
                    os.rename(os.path.join(root, file), os.path.join(root, file.replace(vehicle_name, new_name)))
                        
                        
    if warnings == []:
        print("\nNo warnings\n")
    else:
        print("\n{}\n".format("\n".join(warnings))) # no escape characters in f-string )-;

    input(f"Successfully converted '{vehicle_name}' to '{new_name}'! Press enter to exit...")

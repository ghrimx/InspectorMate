import json

input_File = r"C:\Users\debru\Documents\GitHub\InspectorMate\output_20251017_220032415.json"
try:
    with open(input_File, 'r', encoding="utf-8") as file:
        json_data = json.load(file)
except Exception as e:
    print(f"Cannot parse data into dict using json. Error={e}")

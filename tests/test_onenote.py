import json

input_File = r"C:\Users\debru\AppData\Local\Programs\InspectorMate\onenote_output.json"
with open(input_File, 'r', encoding="utf-8") as file:
    json_data = json.load(file)

print(json_data)
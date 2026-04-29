import json
import os
import re

# define file name and standard string sets
FILENAME = 'scenarios_replaced.json'
REQUIRED_FIELDS = {
    "scenario_number", 
    "scenario_summary_header", 
    "dialogue_text", 
    "ats_category", 
    "ats_note"
}

def clean_and_replace_data():
    if not os.path.exists(FILENAME):
        print(f"Error: cannot find file {FILENAME}")
        return

    # 1. read data
    try:
        with open(FILENAME, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error - broken JSON file - {e}")
        return

    if not isinstance(data, list):
        print("Error - JSON root struture is not list")
        return

    original_count = len(data)
    cleaned_data = []
    pattern = re.compile(r'Parent', re.IGNORECASE)

    # 2. fiter and replace
    for item in data:
        if isinstance(item, dict):
            current_keys = set(item.keys())
            
            # check if strings fully match
            if current_keys == REQUIRED_FIELDS:
                # do regex replace to content in string type
                for key in item:
                    if isinstance(item[key], str):
                        # Replace Triage Nurse to Nurse
                        item[key] = pattern.sub('Patient', item[key])
                
                cleaned_data.append(item)


    final_count = len(cleaned_data)
    removed_count = original_count - final_count

    # 3. replace file
    with open(FILENAME, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print("-" * 30)
    print(f"Done！")
    print(f"Original sets: {original_count}")
    print(f"Deleted sets: {removed_count} (string unmatch)")
    print(f"Qualified and replaced sets: {final_count}")
    print(f"Output saved to: {FILENAME}")
    print("-" * 30)

if __name__ == "__main__":
    clean_and_replace_data()
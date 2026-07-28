import re

NUMERIC_FIELDS = {
    "score", "theta","b_allele_freq", "coordinate",
    "birth_weight_kg", "weaning_weight_kg", "six_month_weight_kg",
    "fat_thickness_cm", "eye_muscle_area_cm2", "height_at_withers_cm",
    "chest_girth_cm", "shin_circumference_cm", "pre_weaning_gain_kg",
    "post_weaning_gain_kg", "daily_weight_gain_kg"
}

def extract(raw_input, dataset_id, delimiter="", comment=""):
    unix_text = re.sub(r'\r', '', raw_input)
    lines = unix_text.split('\n')
    keys = []
    extracted = []

    for line in lines:
        if not line or (comment and line.startswith(comment)):
            continue

        cols = line.split(delimiter)

        # Fix column names
        if len(keys) == 0:
            keys = [col.lower().strip().replace(" ", "_").replace("-", "_") for col in cols]
            keys = ["sample_id" if key == "sample_name" else key for key in keys]
            print(f"Found columns: {keys}")

        elif len(keys) == len(cols):
            entry = {}
            entry["dataset_id"] = dataset_id

            # numeric fields converted to floats
            for (key, value) in zip(keys, cols):
                if key in NUMERIC_FIELDS:
                    try:
                        entry[key] = float(value)
                    except ValueError:
                        entry[key] = None
                else:
                    entry[key] = value

            # entry.update(dict(zip(keys, cols)))
            extracted.append(entry)

        else:
            print("Warning: line may be incorrect")
            print(line)
        
    print("Successfully read file into dict")

    return extracted
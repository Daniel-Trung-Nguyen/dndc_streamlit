import streamlit as st
import json
from pathlib import Path
from io import BytesIO, StringIO
import base64


def input_config_list(json_data):
    '''
    Extracts and organizes event data from a given JSON file or JSON object. 
    Specifically, this function extracts the 'events' list from the JSON data and identifies unique crop names 
    and other event types. It returns these along with the organized data in a list of dictionaries.

    Parameters:
    ----------
    json_data : str or file-like object
        Either the file path pointing to a JSON file (str) or a file-like object containing JSON data. 
        The JSON data should contain an 'events' list, usually nested under "sites", "fields", and "rotations".

    Returns:
    -------
    data : list of dict
        A list of dictionaries containing the organized events.
        
    crop_names : list of str
        A list of unique crop names extracted from the 'events' data.
        
    other_events : list of str
        A list of unique event types other than "crop", extracted from the 'events' data.
    '''
    
    if isinstance(json_data, str) and json_data.endswith(".json"):
        with open(json_data, 'r') as f:
            json_data = json.load(f)
    elif hasattr(json_data, 'read'):
        json_data = json.load(json_data)
        
    # try:
    # Navigate to the 'events' list
    try:
        events = json_data[0]["sites"][0]['fields'][0]['rotations'][0]['events']
    except:
        events = json_data["sites"][0]['fields'][0]['rotations'][0]['events']
        
    
    crop_names = []
    data = []
    data_full = []
    other_events = []

    # Loop through each event dictionary in the 'events' list
    for event in events:
        event_type = event.get('_event_type', None)

        # Check if this event_type is in the event_dict
        if event_type:
            # Handle "crop" type differently to allow for multiple crop configurations
            if event_type == "crop":
                crop = event.get('name', '')
                if crop not in crop_names:
                    crop_names.append(crop)
                    # pprint(event)
                    data.append(event)
            else:
                if event_type not in other_events:
                    other_events.append(event_type)
                    # pprint(event)
                    data.append(event)
            data_full.append(event) 
               
    crop_names = list(dict.fromkeys(crop_names))
    other_events = list(dict.fromkeys(other_events))
    # print("crop_names:", crop_names)
    # print("other_events:", other_events)
    return data, crop_names, other_events, data_full


def convert_to_event_dict(data):
    """
    Converts a list of dictionaries containing event data into a nested dictionary.
    The nested dictionary organizes events by their '_event_type'.
    For 'crop' events, it further organizes them into a list of dictionaries keyed by the crop name.

    Parameters:
    ----------
    data : list of dict
        A list of dictionaries containing event data.
        
    Returns:
    -------
    event_dict : dict
        A nested dictionary organizing the events by their '_event_type'.
    """
    
    event_dict = {}
    
    for item in data:
        event_type = item.get('_event_type', None)
        if event_type:
            if event_type == 'crop':
                # Handle crop events specially by appending them to a list under the 'crop' key
                if 'crop' not in event_dict:
                    event_dict['crop'] = []
                
                # Copy the event item to avoid modifying the original data
                new_item = item.copy()
                new_item.pop('_event_type', None)  # Remove the '_event_type' key
                
                event_dict['crop'].append(new_item)
            else:
                # For other event types, simply add them to the dictionary
                # Copy the event item to avoid modifying the original data
                new_item = item.copy()
                new_item.pop('_event_type', None)  # Remove the '_event_type' key
                
                event_dict[event_type] = new_item

    return event_dict


def input_config_replacement(event_dict, json_data, json_out=None):
    '''
    Updates the events section of a given JSON data based on a specified event dictionary.
    The function first extracts the 'events' list from the JSON data and then updates it 
    according to the values specified in the event_dict. The updated JSON data is then written 
    to a new file.

    Parameters:
    ----------
    event_dict : dict
        A dictionary containing the events to update.
        Example:
            {
                "crop": [
                    {"name": "grass, perennial, C4, calvin", "tdd": 4000.0},
                    {"name": "grass, perennial, C3, calvin", "tdd": 3000.0}
                ],
                "autoirrigation": {"method": "furrow"}
            }

    json_data : str or file-like object
        Either the file path pointing to a JSON file (str) or a file-like object containing 
        JSON data. The JSON data should contain an 'events' list, usually nested under "sites", 
        "fields", and "rotations".

    json_out : str
        The file path where the updated JSON data will be saved.

    Returns:
    -------
    None
    '''
    if isinstance(json_data, str) and json_data.endswith(".json"):
        with open(json_data, 'r') as f:
            json_data = json.load(f)
    elif hasattr(json_data, 'read'):
        json_data = json.load(json_data)
        
    # Navigate to the 'events' list
    try:
        events = json_data[0]["sites"][0]['fields'][0]['rotations'][0]['events']
    except:
        events = json_data["sites"][0]['fields'][0]['rotations'][0]['events']

    # Loop through each event dictionary in the 'events' list
    for event in events:
        event_type = event.get('_event_type', None)

        # Debug printing
        print(f"Processing event_type: {event_type}")

        # Check if this event_type is in the event_dict
        if event_type and event_dict.get(event_type, None):

            # Handle "crop" type differently to allow for multiple crop configurations
            if event_type == "crop":
                for crop_config in event_dict[event_type]:
                    # Check if the 'name' matches before updating
                    if event.get('name', '') == crop_config.get('name', ''):
                        for key, value in crop_config.items():
                            event[key] = value
                        print(f"Updated event: {key} : {event[key]}")
            else:
                for key, value in event_dict[event_type].items():
                    event[key] = value
                print(f"Updated event: {key} : {event[key]}")

    if json_out: 
        with open(json_out, 'w') as f_out:
            json.dump(json_data, f_out, indent=2)
        
        print(f"Updated JSON saved to {json_out}.")
        return json_out
    
    else:
        return json_data
    
    
def input_config_soil_dict(json_data):
    ''''''
    if isinstance(json_data, str) and json_data.endswith(".json"):
        with open(json_data, 'r') as f:
            json_data = json.load(f)
    elif hasattr(json_data, 'read'):
        json_data = json.load(json_data)
        
    # try:
    # Navigate to the 'soils' list
    try:
        soil_data = json_data[0]["sites"][0]['fields'][0]['soil']
    except:
        soil_data = json_data["sites"][0]['fields'][0]['soil']
        
        
    return soil_data
        
    
def soil_config_replacement(soil_dict, json_data, json_out=None):
    
    if isinstance(json_data, str) and json_data.endswith(".json"):
        with open(json_data, 'r') as f:
            json_data = json.load(f)
    elif hasattr(json_data, 'read'):
        json_data = json.load(json_data)
        
    # try:
    # Navigate to the 'soils' list
    try:
        soil_data = json_data[0]["sites"][0]['fields'][0]['soil']
    except:
        soil_data = json_data["sites"][0]['fields'][0]['soil']
        
    for key in soil_data.keys():
        if key in soil_dict:
            soil_data[key] = soil_dict[key]
            
    if json_out: 
        # Write the updated JSON data to a new file
        with open(json_out, 'w') as f_out:
            json.dump(json_data, f_out, indent=2)

        print(f"Updated JSON saved to {json_out}.")
        return json_out
    else:
        return json_data
    
def find_first_last_years(crop_events):
    """
    Identifies the first and last years among a list of crop events.

    Parameters:
    ----------
    crop_events : list of dict
        A list of dictionaries containing crop event data. 
        Each dictionary should have 'start_date' and 'end_date' keys,
        which are dictionaries containing 'year', 'month', and 'day'.

    Returns:
    -------
    first_year : int
        The earliest start year among all crop events.
    
    last_year : int
        The latest end year among all crop events.
    """
    first_year = float('inf')  # Initialize to a large value
    last_year = float('-inf')  # Initialize to a small value
    
    for event in crop_events:
        start_date = event.get('start_date', {})
        end_date = event.get('end_date', {})
        print(start_date, end_date)
        
        start_year = start_date.get('year', None)
        end_year = end_date.get('year', None)
        
        if start_year is not None:
            first_year = min(first_year, start_year)
        if end_year is not None:
            last_year = max(last_year, end_year)
            
    return first_year, last_year


def generate_autofertilization_event(json_data, json_out, first_year, last_year):
    '''
    Config-based generation of auto-fert event.
    Automatically generates dates list based on the first and last years of the crop events.
    
    Parameters:
    - json_data: The input JSON data containing event configurations.
    - json_out: The output JSON file name where the updated configuration will be saved.
    - first_year: The first year of the crop events.
    - last_year: The last year of the crop events.
    '''
    if isinstance(json_data, str) and json_data.endswith(".json"):
        with open(json_data, 'r') as f:
            json_data = json.load(f)
    elif hasattr(json_data, 'read'):
        json_data = json.load(json_data)
        
    # Automatically generate dates list based on the first_year and last_year
    dates = [[f"{year}-01-01", f"{year}-12-30"] for year in range(first_year, last_year + 1)]
    
    # Navigate to the 'events' list
    try:
        events = json_data[0]["sites"][0]['fields'][0]['rotations'][0]['events']
    except:
        events = json_data["sites"][0]['fields'][0]['rotations'][0]['events']
        
    for date in dates:
        start_date, end_date = date
        year_s, month_s, day_s = start_date.split("-")
        year_e, month_e, day_e = end_date.split("-")
        auto_fert = {
                "_event_type": "alt_fertilizer",
                "method": "auto-fertilizer",
                "start_date": {"year": int(year_s), "month": int(month_s), "day": int(day_s)},
                "end_date": {"year": int(year_e), "month": int(month_e), "day": int(day_e)}
                }
        events.append(auto_fert)
        
    # Write the updated JSON data to a new file
    with open(json_out, 'w') as f_out:
        json.dump(json_data, f_out, indent=2)

    print(f"Updated JSON saved to {json_out}.")
    return json_out


def generate_download_link(file_path, download_filename):
    with open(file_path, "rb") as f:
        bytes = f.read()
        b64 = base64.b64encode(bytes).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{download_filename}">Download JSON File</a>'
        return href   
    
    

    
    
    
# # Sample data
# data = [
#     {
#         '_event_type': 'crop',
#         'name': 'grass, perennial, C3, calvin',
#         'cn_grain': 26.0,
#         'cn_leaf': 26.0,
#         'cn_root': 37.0,
#         'cn_stem': 26.0,
#         'frac_grain': 0.01,
#         'frac_leaf': 0.27,
#         'frac_root': 0.45,
#         'frac_stem': 0.27,
#         'id': 12,
#         'is_herbaceous_perennial': True,
#         'is_perennial_crop': True,
#         'is_root_crop': False,
#         'is_transplant': 0,
#         'land_use': 'rotation_meadow',
#         'max_biomass': 10825.0,
#         'n_fixation_index': 1.0,
#         'optimum_temperature': 21.0,
#         'reductions': [],
#         'tdd': 1200.0,
#         'vascularity_index': 0.0,
#         'water_demand': 200.0
#     },
#     {
#         '_event_type': 'autoirrigation',
#         'depth': 0.0,
#         'index': 1.0,
#         'method': 'drip'
#     },
#     {
#         '_event_type': 'alt_fertilizer',
#         'method': 'auto-fertilizer'
#     }
# ]

def normalize_to_bool(value):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)

# Function to display soil widgets
def display_soil_widgets(data):
    
    st.sidebar.subheader("Soil")
    for key, value in data.items():
        if isinstance(value, float) or isinstance(value, int):
            data[key] = st.sidebar.number_input(f"{key}", value=value)
            
        if isinstance(value, bool):
            data[key] = st.sidebar.checkbox(f"{key}", value=value)
            
        elif isinstance(value, str):
            if value.lower() in ("true", "false", True, False):
                normalized_value = normalize_to_bool(value)
                data[key] = st.sidebar.checkbox(f"{key}", value=normalized_value)
            else:
                data[key] = st.sidebar.text_input(f"{key}", value=value)
        
        
# Function to display event widgets
def display_widgets(event_type, data, unique_id=""):
    
    st.sidebar.subheader(event_type)
    for item in data:
        if item['_event_type'] == event_type:
            
            unique_key_suffix = f"_{unique_id}" if unique_id else ""
            
            if event_type == 'crop':
                item['name'] = st.sidebar.text_input(f'name{unique_key_suffix}', value=item['name'])
                # Special handling for crop fractions
                frac_keys = ['frac_grain', 'frac_leaf', 'frac_root', 'frac_stem']
                fracs = {key: item[key] for key in frac_keys}
                total_frac = sum(fracs.values())

                # Adjust the fractions if they do not sum up to 1
                if total_frac != 1:
                    for key in frac_keys:
                        fracs[key] = fracs[key] / total_frac
                
                # Display sliders and update values
                for key in frac_keys:
                    new_value = st.sidebar.slider(f"{key}{unique_key_suffix}", 0.0, 1.0, fracs[key])
                    delta = new_value - fracs[key]
                    if delta != 0:
                        for other_key in frac_keys:
                            if other_key != key:
                                fracs[other_key] -= delta / 3
                    fracs[key] = new_value
                # Update original data
                for key in frac_keys:
                    item[key] = fracs[key]
                    
                # Handling for other event types
                for key, value in item.items():
                    if not "frac_" in str(key) and key != '_event_type' and key != 'name':
                        if isinstance(value, float):
                            if value==0:
                                max_value=1.0 
                            else: max_value=value * 3
                            item[key] = st.sidebar.slider(f"{key}{unique_key_suffix}", 0.0, max_value, value)
                        elif isinstance(value, int):
                            if str(value).lower() in ("true", "false", True, False):
                                normalized_value = normalize_to_bool(value)
                                item[key] = st.sidebar.checkbox(f"{key}{unique_key_suffix}", value=normalized_value)
                            else:
                                item[key] = st.sidebar.number_input(f"{key}{unique_key_suffix}", value=value)
                        elif isinstance(value,bool):
                            item[key] = st.sidebar.checkbox(f"{key}{unique_key_suffix}", value=value)
                        elif isinstance(value, str):
                            if value.lower() in ("true", "false", True, False):
                                normalized_value = normalize_to_bool(value)
                                item[key] = st.sidebar.checkbox(f"{key}{unique_key_suffix}", value=normalized_value)
                            else:
                                item[key] = st.sidebar.text_input(f"{key}{unique_key_suffix}", value=value)

            else:
                # Handling for other event types
                for key, value in item.items():
                    if key != '_event_type':
                        if isinstance(value, float):
                            if "depth" in str(key):
                                item[key] = st.sidebar.slider(f"{key}{unique_key_suffix}", 0.0, 200.0, value)
                            else:
                                if value==0:
                                    max_value=1.0
                                else: max_value=value * 3
                                item[key] = st.sidebar.slider(f"{key}{unique_key_suffix}", 0.0, max_value, value)
                        elif isinstance(value, int): 
                            if str(value).lower() in ("true", "false", True, False):
                                normalized_value = normalize_to_bool(value)
                                item[key] = st.sidebar.checkbox(f"{key}{unique_key_suffix}", value=normalized_value)
                            else:
                                item[key] = st.sidebar.number_input(f"{key}{unique_key_suffix}", value=value)
                        elif isinstance(value,bool):
                            item[key] = st.sidebar.checkbox(f"{key}{unique_key_suffix}", value=value)
                        elif isinstance(value, str):
                            if value.lower() in ("true", "false", True, False):
                                normalized_value = normalize_to_bool(value)
                                item[key] = st.sidebar.checkbox(f"{key}{unique_key_suffix}", value=normalized_value)
                            else:
                                item[key] = st.sidebar.text_input(f"{key}{unique_key_suffix}", value=value)


# Streamlit app
st.title("Modifying DNDC input config files")
st.write("Download an example config here: https://bit.ly/3QuR7z2")

uploaded_file = st.file_uploader("Choose a JSON file", type="json")

# Create two columns using beta_columns
col1, col2 = st.columns(2)

if uploaded_file is not None:
    # Reset the file's position to the beginning
    uploaded_file.seek(0)
    # Read the uploaded file
    data, crop_names, other_events, data_full = input_config_list(uploaded_file)
    uploaded_file.seek(0)
    soil_data = input_config_soil_dict(uploaded_file)
    
    data_ori = data.copy()
    soil_data_ori = soil_data.copy()
    
    with col1:
        st.write("Management Events (original):")
        st.write(convert_to_event_dict(data_ori))
        st.write("Soil (original):")
        st.write(soil_data)
    
    
    # Add the checkbox to the sidebar or main area
    add_auto_fert = st.sidebar.checkbox('Add Auto-Fertilization Event')
    # Display widgets (use your existing display_widgets function)
    for i, crop_name in enumerate(crop_names):
        crop_data = [item for item in data if item['_event_type'] == 'crop' and item['name'] == crop_name]
        display_widgets('crop', crop_data, unique_id=f"{i}")

    for i, event_type in enumerate(other_events):
        other_data = [item for item in data if item['_event_type'] == event_type]
        display_widgets(event_type, other_data, unique_id=f"{i}")
        
        
    display_soil_widgets(soil_data)
        
    # st.write(data)
    
    event_dict = convert_to_event_dict(data)
    with col2:
        st.write("Management Events:")
        st.write(event_dict)
        st.write("Soil:")
        st.write(soil_data)
    
    # Add a button to trigger JSON file update
    if st.button("Update JSON File"):
        # Reset the file's position to the beginning again before re-reading it
        uploaded_file.seek(0)
        saved_file_path = input_config_replacement(event_dict, uploaded_file)
        
        saved_file_path = soil_config_replacement(soil_data, saved_file_path, "updated_config.json")
        
        if add_auto_fert:
            first_year, last_year = find_first_last_years(data_full)
            saved_file_path = generate_autofertilization_event(saved_file_path, "updated_config.json", first_year, last_year)
        
        # Generate download link
        if Path(saved_file_path).exists():
            download_link = generate_download_link(saved_file_path, "updated_config.json")
            st.markdown(download_link, unsafe_allow_html=True)
    
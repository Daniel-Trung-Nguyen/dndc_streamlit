# Importing required libraries
import streamlit as st
import pandas as pd
import json
import plotly.express as px
import re

import matplotlib.pyplot as plt
import io
import base64


# Defining the utility functions
def convert_json_to_dfs_updated(json_data):
    dfs = {}
    for category, category_data in json_data.items():
        try:
            # Special handling for 'crops' category which has nested dictionaries
            if category == 'crops':
                dfs[category] = {}
                for crop_key, crop_data in category_data.items():
                    columns = crop_data['columns']
                    data = crop_data['data']
                    dfs[category][crop_key] = pd.DataFrame(data, columns=columns)
            else:
                # Extract columns and data for each category
                columns = category_data['columns']
                data = category_data['data']
                
                # Create DataFrame for each category
                dfs[category] = pd.DataFrame(data, columns=columns)
        except KeyError as e:
            print(f"KeyError: {e} not found in category {category}")
        except Exception as e:
            print(f"An error occurred while processing category {category}: {e}")
    return dfs

def return_output_df(dataframes, column, **kwargs):
    # min_date = kwargs.get('min_date', False)
    # max_date = kwargs.get('max_date', False)
    
    ## Streamlit return Python date objects, which cannot be directly compared to Pandas Timestamp objects.
    # need to convert the date objects to Timestamp objects for the comparison to work as expected.
    min_date = pd.Timestamp(kwargs.get('min_date', '1900-01-01'))  # Convert to Timestamp
    max_date = pd.Timestamp(kwargs.get('max_date', '3000-01-01'))  # Convert to Timestamp
    
    df_= dataframes[column]
    df_['Date'] = pd.to_datetime(df_['Year'].astype(str) + df_['Day'].astype(str), format='%Y%j')
    if min_date and max_date:
        df_ = df_[(df_['Date'] >= min_date) & (df_['Date'] <= max_date)]
    return df_

def sanitize_filename(filename):
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    
    # Remove any characters that are not alphanumeric, underscores, or periods
    filename = re.sub(r'[^\w\.-]', '', filename)
    
    return filename

def annotate_seasons_high(ax, year, y_position):
    seasons = {
        'Winter': ('-01-01', '-03-20'),
        'Spring': ('-03-21', '-06-20'),
        'Summer': ('-06-21', '-09-22'),
        'Autumn': ('-09-23', '-12-31')
    }
    for season, (start, end) in seasons.items():
        start_date = pd.Timestamp(f"{year}{start}")
        end_date = pd.Timestamp(f"{year}{end}")
        midpoint_date = start_date + (end_date - start_date) // 2  # Calculating midpoint date
        ax.annotate(season, xy=(midpoint_date, y_position), xytext=(0, 0),
                    textcoords='offset points', ha='center', va='center', fontsize=12, color='grey')

# Initialize variables to avoid scope-related issues
categories = []
selected_parameters = {}
selected_all_parameters = []
clear_button = st.sidebar.button("Clear Dashboard")  # Clear button

# Initialize Streamlit App
st.title("DNDC Model Output Dashboard")
st.write("Download an example config here: https://bit.ly/3sgno3k")

# Sidebar for File Upload and Management
st.sidebar.title("File Upload")
uploaded_file = st.sidebar.file_uploader("Upload a JSON file", type=["json"])


# Read JSON Data
json_data = None
if uploaded_file:
    json_data = json.load(uploaded_file)

# Parameter Selection UI
if json_data:
    
    try:
        dataframes = convert_json_to_dfs_updated(json_data)
    except Exception as e:
        st.sidebar.warning(f"An error occurred while processing the file: {e}")
    
    
    # Add checkbox for plotting all parameters on a single subplot
    plot_all_in_one = st.sidebar.checkbox("Plot all parameters in one subplot")
    
    if not plot_all_in_one:
        n_cols = st.sidebar.slider("Number of Columns for Subplot", min_value=1, max_value=5, value=3)  # User-defined number of columns
        
    # Add a checkbox for plotting by category or by list of all parameters
    plot_by_category = st.sidebar.checkbox("Plot by category", value=True)
    
    
    if dataframes:
        
        # Find the global minimum and maximum dates across all dataframes
        # global_min_date = pd.Timestamp('1970-01-01')
        # global_max_date = pd.Timestamp('2050-01-01')
        global_min_date = pd.Timestamp('3000-01-01')
        global_max_date = pd.Timestamp('1900-01-01')

        for category, df in dataframes.items():
            if category != 'crops':
                try:
                    # print("HELLO",category)
                    temp_df = df.copy()
                    temp_df['Date'] = pd.to_datetime(temp_df['Year'].astype(str) + temp_df['Day'].astype(str), format='%Y%j')
                    min_date = temp_df['Date'].min()
                    max_date = temp_df['Date'].max()
                except:
                    pass
            else:
                for crop_name, crop_df in df.items():
                    temp_df = crop_df.copy()
                    temp_df['Date'] = pd.to_datetime(temp_df['Year'].astype(str) + temp_df['Day'].astype(str), format='%Y%j')
                    min_date = temp_df['Date'].min()
                    max_date = temp_df['Date'].max()

            global_min_date = min(global_min_date, min_date)
            global_max_date = max(global_max_date, max_date)
            # print(f"Global min date: {global_min_date}", f"Global max date: {global_max_date}")

        # Use the min and max dates to populate the date_input fields
        start_date = st.sidebar.date_input('Start date', min_value=global_min_date, max_value=global_max_date, value=global_min_date)
        end_date = st.sidebar.date_input('End date', min_value=global_min_date, max_value=global_max_date, value=global_max_date)

        # Validate the date range
        if start_date > end_date:
            st.sidebar.warning('End date must fall after start date.')
        
        
        if plot_by_category:
            if clear_button:
                categories = []
                selected_parameters = {}
                selected_all_parameters = []
                category = st.sidebar.selectbox("Select Category", list(dataframes.keys()))
            else:
                category = st.sidebar.selectbox("Select Category", list(dataframes.keys()))
                if category not in categories:
                    categories.append(category)
                
                if category != 'crops':
                    parameters = list(dataframes[category].columns)
                    selected_parameters[category] = st.sidebar.multiselect("Select Parameters", parameters)

                else:
                    parameters = list(dataframes[category].keys())
                    selected_crop = st.sidebar.selectbox("Select Crop", parameters)
                    crop_parameters = list(dataframes[category][selected_crop].columns)
                    selected_parameters[category] = st.sidebar.multiselect("Select Crop Parameters", crop_parameters)
        else:
            if clear_button:
                categories = []
                selected_parameters = {}
                selected_all_parameters = []
            else:
                # Prepare a list of all parameters across all categories if not plotting by category
                all_parameters = []
                for cat, dfs in dataframes.items():
                    if cat != 'crops':
                        all_parameters.extend(list(dfs.columns))
                    else:
                        for crop, df in dfs.items():
                            all_parameters.extend(list(df.columns))
                all_parameters = sorted(set(all_parameters))  # Remove duplicates and sort
                selected_all_parameters = st.sidebar.multiselect("Select Parameters from All Categories", all_parameters)

        # Data Visualization
        if categories:
            for cat in categories:
                params = selected_parameters.get(cat, [])
                st.header(f"Category: {cat}")
        else:
            params = selected_all_parameters
            st.header("Plotting by Selected Parameters")
            
        if params:
            if plot_all_in_one:
                # Plot all parameters on a single subplot
                fig, ax = plt.subplots(figsize=(15, 7))
                
                if plot_by_category:
                    if cat != "crops":
                        df = return_output_df(dataframes, cat, min_date=start_date, max_date=end_date)
                    else:
                        selected_crop_df = dataframes[cat].get(selected_crop, pd.DataFrame())
                        df = return_output_df({'crops': selected_crop_df}, 'crops', min_date=start_date, max_date=end_date)

                    for param in params:
                        ax.plot(df['Date'], df[param], label=param, linewidth=2)
                else:
                    for param in params:
                        for cat, dfs in dataframes.items():
                            if cat != 'crops':
                                if param in dfs.columns:
                                    df = return_output_df(dataframes, cat, min_date=start_date, max_date=end_date)
                                    ax.plot(df['Date'], df[param], label=f"{param} ({cat})", linewidth=2)
                            else:
                                for crop, df in dfs.items():
                                    if param in df.columns:
                                        df = return_output_df({'crops': df}, 'crops', min_date=start_date, max_date=end_date)
                                        ax.plot(df['Date'], df[param], label=f"{param} ({crop})", linewidth=2)
                    
                ax.legend(fontsize=16)
                ax.set_xlabel('Date', fontsize=18)
                ax.set_ylabel('Value', fontsize=18)
                # ax.set_title(param, fontsize=20)
                ax.tick_params(axis='x', labelsize=16)
                ax.tick_params(axis='y', labelsize=16)
                ax.grid(True, linestyle='--', linewidth=0.2, color='gray')
                
            else:
                n = len(params)
                # print(f"Number of params: {n}")  # Debugging
                n_rows = int(n / n_cols) + (n % n_cols > 0)  # Calculate required rows
                
                if n > 0:
                    fig, axs = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows), squeeze=False)
                    
                    
                    for i, param in enumerate(params):
                        row = i // n_cols
                        col = i % n_cols
                        ax = axs[row, col]
                        
                        if plot_by_category:
                        
                            if cat != "crops":
                                df = return_output_df(dataframes, cat, min_date=start_date, max_date=end_date)
                            else:
                                # Use the selected_crop variable to get the correct DataFrame
                                selected_crop_df = dataframes[cat].get(selected_crop, pd.DataFrame())
                                df = return_output_df({'crops': selected_crop_df}, 'crops', min_date=start_date, max_date=end_date)
                            
                            # print(f"DataFrame head for {param}:")  # Debugging
                            # print(df.head())  # Debugging
                            
                            ax.plot(df['Date'], df[param], color='red')
                            
                        else:
                            for cat, dfs in dataframes.items():
                                if cat != 'crops':
                                    if param in dfs.columns:
                                        df = return_output_df(dataframes, cat, min_date=start_date, max_date=end_date)
                                        ax.plot(df['Date'], df[param], label=f"{param} ({cat})", color='red')
                                else:
                                    for crop, df in dfs.items():
                                        if param in df.columns:
                                            df = return_output_df({'crops': df}, 'crops', min_date=start_date, max_date=end_date)
                                            ax.plot(df['Date'], df[param], label=f"{param} ({crop})", color='red')
                                            
                        ax.set_title(param, fontsize=18)
                        ax.set_xlabel('Date', fontsize=16)
                        ax.set_ylabel(param, fontsize=16)
                        ax.tick_params(axis='x', labelsize=14)
                        ax.tick_params(axis='y', labelsize=14)
                        ax.grid(True, linestyle='--', linewidth=0.2, color='gray')
                        if n_cols >= 3:
                            ax.tick_params(axis='x', rotation=90)
                        
                         
            plt.tight_layout()
            st.pyplot(fig)
            
            # Generate download link for the plot
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="{cat}.png">Download Plot</a>'
            st.markdown(href, unsafe_allow_html=True)
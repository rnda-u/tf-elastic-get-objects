import json
from datetime import datetime
import argparse
import re # Import the regular expression module

# --- Configuration Parameters ---
# Name of the JSON file containing the Elasticsearch index data
FILE_NAME = './data.json'
# Number of the latest indexes to retrieve for each index base name
NUM_LATEST_INDEXES_PER_BASE_NAME = 2 # Renamed for clarity
# Criteria for the status icon
REQUIRED_INDEX_MODE = "logsdb"
REQUIRED_HOST_NAME_FIELD_TYPE = "keyword"
# Status icons
STATUS_ICON_ALL_MATCH = "✅😁"
STATUS_ICON_PARTIAL_MATCH = "⚠️"
STATUS_ICON_NO_MATCH = "❌😮"
# --- End Configuration Parameters ---

def get_readable_date(timestamp_ms_str):
    """
    Converts a Unix timestamp string (in milliseconds) to a human-readable date and time string.

    Args:
        timestamp_ms_str (str): The Unix timestamp in milliseconds as a string.

    Returns:
        str: The formatted date string (YYYY-MM-DD HH:MM:SS) or "Invalid Date" if conversion fails.
    """
    try:
        creation_timestamp_ms = int(timestamp_ms_str)
        # Convert milliseconds to seconds for datetime.fromtimestamp
        creation_date_readable = datetime.fromtimestamp(creation_timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        creation_date_readable = "Invalid Date"
    return creation_date_readable

def extract_index_base_name(index_name):
    """
    Extracts the base name of an Elasticsearch index by removing the
    trailing date and sequence number (e.g., '-YYYY.MM.DD-NNNNNN').

    Args:
        index_name (str): The full index name.

    Returns:
        str: The extracted base name or the original name if pattern not found.
    """
    # Regex to match trailing -YYYY.MM.DD-NNNNNN (or -YYYY.MM.DD-NNNNNN.subname)
    # This pattern should be robust enough for common ILM index naming conventions
    match = re.search(r'-\d{4}\.\d{2}\.\d{2}-\d{6}(?:-\d+)?$', index_name)
    if match:
        return index_name[:match.start()]
    return index_name # Return original if no date/sequence pattern found

def load_data_from_json(file_path):
    """
    Loads JSON data from a specified file path.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        raise
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON.")
        raise

def get_latest_indexes_by_base_name(elastic_indices_data, num_latest):
    """
    Processes Elasticsearch index data to first group by 'base name'
    (extracted from index_name) and then select the 'num_latest' created
    for each base name, sorted by creation date.
    Each selected index dictionary is augmented with its 'original_index_pattern'.

    Args:
        elastic_indices_data (list): The 'value' list from Elasticsearch_indices.
        num_latest (int): The number of latest indexes to retrieve per base name.

    Returns:
        dict: A dictionary where keys are index base names and values are lists
              of the latest 'num_latest' index dictionaries, each including
              the 'original_index_pattern'.
    """
    indexes_by_base_name = {}

    for item in elastic_indices_data:
        current_index_pattern = item.get("index_pattern") # Get the index pattern here
        indexes_list_from_pattern = item.get("indexes", [])

        if not current_index_pattern:
            continue

        for index in indexes_list_from_pattern:
            index_name = index.get("index_name")
            creation_date_str = index.get("index_creation_date")

            if not index_name or not creation_date_str:
                # Skip invalid index entries
                continue

            base_name = extract_index_base_name(index_name)
            
            # Ensure creation_date is valid for sorting
            if not str(creation_date_str).isdigit():
                continue # Skip if creation date is not a valid number

            # Make a copy of the index dictionary and add the original index_pattern
            index_copy = index.copy()
            index_copy['original_index_pattern'] = current_index_pattern 

            if base_name not in indexes_by_base_name:
                indexes_by_base_name[base_name] = []
            
            indexes_by_base_name[base_name].append(index_copy) # Append the modified copy

    final_selection = {}
    for base_name, indexes in indexes_by_base_name.items():
        # Sort each group by index_creation_date in descending order
        sorted_indexes = sorted(
            indexes, key=lambda x: int(x["index_creation_date"]), reverse=True
        )
        # Get the 'num_latest' entries for this base name
        final_selection[base_name] = sorted_indexes[:num_latest]

    return final_selection

def analyze_index_details(processed_indexes_by_base_name, required_mode, required_host_type,
                          all_match_icon, partial_match_icon, no_match_icon):
    """
    Analyzes index details to determine a status icon based on index_mode
    and host_name_fieldsType. Groups results by the original index pattern.

    Args:
        processed_indexes_by_base_name (dict): Dictionary of processed indexes per base name,
                                                each index including 'original_index_pattern'.
        required_mode (str): The required value for 'index_mode' for a full match.
        required_host_type (str): The required value for 'host_name_fieldsType' for a full match.
        all_match_icon (str): Icon for when both conditions are met.
        partial_match_icon (str): Icon for when one condition is met.
        no_match_icon (str): Icon for when neither condition is met.

    Returns:
        dict: A dictionary with original index patterns as keys and lists of analyzed
              index details (including status) as values.
    """
    # The output will now be grouped by original_index_pattern
    grouped_details_by_original_pattern = {} 

    for base_name, indexes_list_for_base_name in processed_indexes_by_base_name.items():
        for index in indexes_list_for_base_name:
            # Retrieve the original index_pattern from the augmented index dictionary
            original_index_pattern = index.get('original_index_pattern', 'Unknown_Pattern') 
            
            index_name = index.get("index_name", "N/A")
            index_mode = index.get("index_mode", "N/A")
            host_name_fieldsType = index.get("host_name_fieldsType", "N/A")
            
            status_icon = ""
            mode_matches = (index_mode == required_mode)
            host_type_matches = (host_name_fieldsType == required_host_type)

            if mode_matches and host_type_matches:
                status_icon = all_match_icon
            elif mode_matches or host_type_matches:
                status_icon = partial_match_icon
            else:
                status_icon = no_match_icon

            # Append to the list corresponding to the original_index_pattern
            if original_index_pattern not in grouped_details_by_original_pattern:
                grouped_details_by_original_pattern[original_index_pattern] = []
            
            grouped_details_by_original_pattern[original_index_pattern].append(
                {
                    "index_name": index_name,
                    "index_mode": index_mode,
                    "host_name_fieldsType": host_name_fieldsType,
                    "status": status_icon,
                }
            )
    return grouped_details_by_original_pattern

def print_raw_latest_indexes_by_base_name(processed_data_input):
    """Prints a summary of the latest indexes per base name with raw & readable creation dates."""
    print(f"--- Latest {NUM_LATEST_INDEXES_PER_BASE_NAME} Indexes per Index Base Name (Raw & Readable Creation Date) ---")
    
    if not processed_data_input:
        print("   (No base names with indexes found.)")
        return

    for base_name, indexes in processed_data_input.items():
        print(f"\n Base Name: {base_name}")
        if not indexes:
            print("   (No latest indexes found for this base name)")
            continue
        for idx in indexes:
            raw_date = idx.get('index_creation_date', 'N/A')
            readable_date = get_readable_date(raw_date)
            # Accessing original_index_pattern if needed for this output, otherwise can omit
            original_pattern = idx.get('original_index_pattern', 'N/A')
            print(f"   - Index Name: {idx.get('index_name', 'N/A')}, Original Pattern: {original_pattern}, Creation Date: {readable_date}")

# Renamed the function for clarity
def print_formatted_tables_by_pattern(grouped_details_input):
    """Prints formatted tables of index details, separated by original index pattern."""
    print("\n--- Tables of Index Details with Status Icons (Separated by Original Index Pattern) ---") # Adjusted title

    if not grouped_details_input:
        print("No indexes were processed or selected to display.")
        return

    # Define column widths for consistent formatting
    COL_WIDTHS = {
        "Index Name": 90,
        "Index Mode": 15,
        "Host Name Fields Type": 25,
        "Status": 8
    }
    
    # Calculate total line length for the separator
    header_line = (
        f"{'Index Name':<{COL_WIDTHS['Index Name']}} | "
        f"{'Index Mode':<{COL_WIDTHS['Index Mode']}} | "
        f"{'Host Name Fields Type':<{COL_WIDTHS['Host Name Fields Type']}} | "
        f"{'Status':<{COL_WIDTHS['Status']}}"
    )
    separator_length = len(header_line)


    # Iterate by original index pattern now
    for pattern, details_list in grouped_details_input.items(): # 'pattern' is now the original_index_pattern
        print(f"\n--- Original Index Pattern: {pattern} ---") # Changed from Base Name to Original Index Pattern
        if details_list:
            # Print header for each sub-table
            print(header_line)
            print("-" * separator_length)
            # Print data for the current sub-table
            for row in details_list:
                print(
                    f"{row['index_name']:<{COL_WIDTHS['Index Name']}} | "
                    f"{row['index_mode']:<{COL_WIDTHS['Index Mode']}} | "
                    f"{row['host_name_fieldsType']:<{COL_WIDTHS['Host Name Fields Type']}} | "
                    f"{row['status']:<{COL_WIDTHS['Status']}}"
                )
        else:
            print(f"  No selected indexes for this original index pattern.") # Changed text

# --- Main Execution Flow ---
if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(
        description="Process Elasticsearch index data and display status."
    )

    # Add the argument for showing raw dates
    parser.add_argument(
        '--show-raw-dates',
        '-r',
        action='store_true',
        help="Display the summary of latest indexes including raw and readable creation dates."
    )

    # Parse the arguments
    args = parser.parse_args()

    try:
        json_data = load_data_from_json(FILE_NAME)
        elastic_indices_value = json_data.get("Elasticsearch_indices", {}).get("value", [])

        # Step 1: Get latest indexes by base name, carrying original_index_pattern
        processed_indexes_by_base_name = get_latest_indexes_by_base_name(elastic_indices_value, NUM_LATEST_INDEXES_PER_BASE_NAME)
        
        # Conditionally execute print_raw_latest_indexes_by_base_name
        if args.show_raw_dates:
            print_raw_latest_indexes_by_base_name(processed_indexes_by_base_name)
        else:
            print("--- Skipping raw index creation date summary (use -r or --show-raw-dates to enable) ---")

        # Step 2: Analyze details and group them by original_index_pattern for final tables
        analyzed_data_grouped_by_pattern = analyze_index_details(
            processed_indexes_by_base_name,
            REQUIRED_INDEX_MODE,
            REQUIRED_HOST_NAME_FIELD_TYPE,
            STATUS_ICON_ALL_MATCH,
            STATUS_ICON_PARTIAL_MATCH,
            STATUS_ICON_NO_MATCH
        )
        
        # Step 3: Print the final formatted tables, now grouped by original_index_pattern
        print_formatted_tables_by_pattern(analyzed_data_grouped_by_pattern)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1) 
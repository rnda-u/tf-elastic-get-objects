import json
from datetime import datetime
import argparse # Import the argparse module

# --- Configuration Parameters ---
# Name of the JSON file containing the Elasticsearch index data
FILE_NAME = './data.json'
# Number of the latest indexes to retrieve for each index pattern
NUM_LATEST_INDEXES = 5
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

def get_latest_indexes_per_pattern(elastic_indices_data, num_indexes):
    """
    Processes Elasticsearch index data to get the latest 'num_indexes'
    created for each index pattern, sorted by creation date.

    Args:
        elastic_indices_data (list): The 'value' list from Elasticsearch_indices.
        num_indexes (int): The number of latest indexes to retrieve.

    Returns:
        dict: A dictionary where keys are index patterns and values are lists
              of the latest 'num_indexes' index dictionaries.
    """
    processed_data = {}
    for item in elastic_indices_data:
        index_pattern = item.get("index_pattern")
        indexes = item.get("indexes", [])

        if not index_pattern: # Skip if index_pattern is missing
            continue

        # Sort indexes by index_creation_date in descending order
        # Filter out indexes with invalid creation dates for sorting
        valid_indexes = [idx for idx in indexes if idx.get("index_creation_date") is not None and str(idx["index_creation_date"]).isdigit()]
        sorted_indexes = sorted(
            valid_indexes, key=lambda x: int(x["index_creation_date"]), reverse=True
        )

        # Get the 'num_indexes' latest entries
        processed_data[index_pattern] = sorted_indexes[:num_indexes]
    return processed_data

def analyze_index_details(processed_indexes_by_pattern, required_mode, required_host_type,
                          all_match_icon, partial_match_icon, no_match_icon):
    """
    Analyzes index details to determine a status icon based on index_mode
    and host_name_fieldsType.

    Args:
        processed_indexes_by_pattern (dict): Dictionary of processed indexes per pattern.
        required_mode (str): The required value for 'index_mode' for a full match.
        required_host_type (str): The required value for 'host_name_fieldsType' for a full match.
        all_match_icon (str): Icon for when both conditions are met.
        partial_match_icon (str): Icon for when one condition is met.
        no_match_icon (str): Icon for when neither condition is met.

    Returns:
        dict: A dictionary with index patterns as keys and lists of analyzed
              index details (including status) as values.
    """
    grouped_index_details = {}
    for index_pattern, indexes in processed_indexes_by_pattern.items():
        grouped_index_details[index_pattern] = []
        for index in indexes:
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

            grouped_index_details[index_pattern].append(
                {
                    "index_name": index_name,
                    "index_mode": index_mode,
                    "host_name_fieldsType": host_name_fieldsType,
                    "status": status_icon,
                }
            )
    return grouped_index_details

def print_raw_latest_indexes(processed_data_input):
    """Prints a summary of the latest indexes per pattern with raw & readable creation dates."""
    print("--- Latest Indexes per Index Pattern (Raw & Readable Creation Date) ---")
    for pattern, indexes in processed_data_input.items():
        print(f"\n Index Pattern: {pattern}")
        if not indexes:
            print("   (No latest indexes found for this pattern)")
            continue
        for idx in indexes:
            raw_date = idx.get('index_creation_date', 'N/A')
            readable_date = get_readable_date(raw_date)
            print(f"   - Index Name: {idx.get('index_name', 'N/A')}, Creation  Date: {readable_date}")

def print_formatted_tables(grouped_details_input):
    """Prints formatted tables of index details, separated by index pattern."""
    print("\n--- Tables of Index Details with Status Icons (Separated by Index Pattern) ---")

    if not grouped_details_input:
        print("No indexes were processed or selected to display.")
        return

    # Define column widths for consistent formatting
    COL_WIDTHS = {
        "Index Name": 70,
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


    for pattern, details_list in grouped_details_input.items():
        print(f"\n--- Index Pattern: {pattern} ---")
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
            print(f"  No selected indexes for this pattern.")

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
        action='store_true',  # This means the argument is a flag; it's True if present, False otherwise
        help="Display the summary of latest indexes including raw and readable creation dates."
    )

    # Parse the arguments
    args = parser.parse_args()

    try:
        json_data = load_data_from_json(FILE_NAME)
        elastic_indices_value = json_data.get("Elasticsearch_indices", {}).get("value", [])

        processed_indexes = get_latest_indexes_per_pattern(elastic_indices_value, NUM_LATEST_INDEXES)
        
        # Conditionally execute print_raw_latest_indexes
        if args.show_raw_dates:
            print("--- Skipping raw index creation date summary (use -r or --show-raw-dates to enable) ---")
            print_raw_latest_indexes(processed_indexes)



        analyzed_data = analyze_index_details(
            processed_indexes,
            REQUIRED_INDEX_MODE,
            REQUIRED_HOST_NAME_FIELD_TYPE,
            STATUS_ICON_ALL_MATCH,
            STATUS_ICON_PARTIAL_MATCH,
            STATUS_ICON_NO_MATCH
        )
        
        print_formatted_tables(analyzed_data)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Errors already handled and printed by the called functions, just exit.
        # You can add more specific logging here if needed.
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)
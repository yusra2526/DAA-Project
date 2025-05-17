import os
import pickle
import csv
import shutil

from network import Network
with open("network.bin", "rb") as file:
    G:Network = pickle.load(file)

colors = {

    "baby" : "pink",
    "kid" : "yellow",
    "young_adult" : "blue",
    "adult" : "green",
    "old" : "white"


}

all_edges = set()

for family in G.families:
    for i in family:
        for j in family:
            all_edges.add((i,j,"family"))

for friend_group in G.friend_groups:
    for i in friend_group:
        for j in friend_group:
            all_edges.add((i,j,"friend"))

for community in G.communities:
    for i in community:
        for j in community:
            all_edges.add((i,j,"work"))


def remove_empty_rows_from_csv(input_filepath: str, output_filepath: str = None,
                               has_header: bool = True, delimiter: str = ',',
                               quotechar: str = '"') -> bool:
    """
    Removes empty rows from a CSV file.
    An empty row is defined as a row where all cells are either empty strings
    or contain only whitespace.

    Args:
        input_filepath (str): Path to the input CSV file.
        output_filepath (str, optional): Path to save the cleaned CSV file.
            If None, the input file will be modified in-place (safely via a temp file).
            Defaults to None.
        has_header (bool): Whether the CSV file has a header row.
            If True, the header is preserved. Defaults to True.
        delimiter (str): The delimiter used in the CSV file. Defaults to ','.
        quotechar (str): The quote character used in the CSV file. Defaults to '"'.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    if not os.path.exists(input_filepath):
        print(f"Error: Input file '{input_filepath}' not found.")
        return False

    is_in_place_modification = output_filepath is None or \
                               os.path.abspath(input_filepath) == os.path.abspath(output_filepath)

    temp_filepath = ""
    effective_output_path = ""

    if is_in_place_modification:
        # Create a temporary file name in the same directory as the input file
        input_dir = os.path.dirname(input_filepath)
        base_name = os.path.basename(input_filepath)
        name, ext = os.path.splitext(base_name)
        # Ensure temp_filepath is unique enough or handle potential collisions
        temp_filepath = os.path.join(input_dir, f"{name}_csv_clean_temp{ext}")
        effective_output_path = temp_filepath
    else:
        effective_output_path = output_filepath
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(effective_output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                print(f"Error creating directory '{output_dir}': {e}")
                return False

    rows_written = 0
    empty_rows_skipped = 0

    try:
        with open(input_filepath, 'r', newline='', encoding='utf-8-sig') as infile, \
                open(effective_output_path, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile, delimiter=delimiter, quotechar=quotechar)
            writer = csv.writer(outfile, delimiter=delimiter, quotechar=quotechar)
            if has_header:
                try:
                    header = next(reader)
                    writer.writerow(header)
                    rows_written += 1
                except StopIteration:
                    # File is empty or effectively empty
                    print(f"Warning: File '{input_filepath}' is empty or no header found.")
                    # If in-place, ensure the original (empty) file is preserved or an empty temp is removed
                    if is_in_place_modification and os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                    return True  # Successful in the sense that an empty output is correct for empty input

            for row in reader:
                # Check if all cells in the row are empty or contain only whitespace
                is_empty = True
                if not row:  # Handle completely blank lines that csv.reader might return as []
                    is_empty = True
                else:
                    for cell in row:
                        if cell is not None and cell.strip() != "":
                            is_empty = False
                            break

                if is_empty:
                    empty_rows_skipped += 1
                else:
                    writer.writerow(row)
                    rows_written += 1

        if is_in_place_modification:
            # If any rows were written to the temp file, replace original.
            # If no rows were written (e.g. only header and then empty rows),
            # the temp file might be just a header or empty.
            if rows_written > 0 or (has_header and rows_written == 1 and empty_rows_skipped > 0):
                shutil.move(temp_filepath, input_filepath)
            elif os.path.exists(temp_filepath):  # Temp file was created but is effectively empty or same as input
                os.remove(temp_filepath)

        print(f"Successfully processed '{input_filepath}'.")
        print(f"  Rows written: {rows_written}")
        print(f"  Empty rows skipped: {empty_rows_skipped}")
        if not is_in_place_modification:
            print(f"  Cleaned data saved to '{output_filepath}'.")
        else:
            print(f"  File '{input_filepath}' modified in-place.")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        # Clean up temporary file if it exists and an error occurred
        if is_in_place_modification and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                print(f"Temporary file '{temp_filepath}' removed due to error.")
            except OSError as e_del:
                print(f"Error removing temporary file '{temp_filepath}': {e_del}")
        return False

remove_empty_rows_from_csv("edges.csv","clean_edges.csv",has_header=False, delimiter=";")



import os
import csv

def main():
    """Split CSV files by day"""
    # Paths for input and output
    input_directory = "csv_raw"
    output_directory = "csv"
    
    print("Splitting CSV files by day...")

    # If the output folder does not exist, create it
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Dictionary for temporarily storing all rows, grouped by date
    # Example: daily_data['20240317'] = [row1, row2, ...]
    daily_data = {}
    header = None  # Header is stored once

    # Iterate over all files in the input directory
    if os.path.exists(input_directory):
        for filename in os.listdir(input_directory):
            if filename.endswith(".csv"):
                full_path = os.path.join(input_directory, filename)
                print(f"Processing file: {full_path}")
                
                with open(full_path, "r", encoding="utf-8", newline="") as csvfile:
                    reader = csv.DictReader(csvfile)

                    # Set the header only once (assuming it is the same in all files)
                    if header is None:
                        header = reader.fieldnames

                    for row in reader:
                        # Example: "2024-03-17T23:00:26.480Z" --> "2024-03-17"
                        # Then remove the hyphens for the output format 20240317.csv
                        date_str_iso = row["time"].split("T")[0]  # "YYYY-MM-DD"
                        date_str = date_str_iso.replace("-", "")  # "YYYYMMDD"
                        
                        if date_str not in daily_data:
                            daily_data[date_str] = []
                        daily_data[date_str].append(row)
    else:
        print(f"Warning: Input directory '{input_directory}' does not exist.")

    # Now write a separate CSV file for each found date according to the "YYYYMMDD.csv" schema
    for date_str, rows in daily_data.items():
        output_file = os.path.join(output_directory, f"{date_str}.csv")
        print(f"Creating file for {date_str}: {output_file}")
        with open(output_file, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    print("Done! All files have been split by date (in the YYYYMMDD.csv format) and saved in the 'csv' folder.")
    return True

if __name__ == "__main__":
    main()

import os
import csv

# Pfade für Ein- und Ausgabe
input_directory = "csv_raw"
output_directory = "csv"

# Falls der Ausgabeordner nicht existiert, legen wir ihn an
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Dictionary zur Zwischenspeicherung aller Zeilen, gruppiert nach Datum
# Beispiel: daily_data['20240317'] = [row1, row2, ...]
daily_data = {}
header = None  # Header wird einmalig gespeichert

# Durchlaufe alle Dateien im Eingabeverzeichnis
for filename in os.listdir(input_directory):
    if filename.endswith(".csv"):
        full_path = os.path.join(input_directory, filename)
        print(f"Verarbeite Datei: {full_path}")
        
        with open(full_path, "r", encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            # Header nur einmalig setzen (wir gehen davon aus, dass er in allen Dateien gleich ist)
            if header is None:
                header = reader.fieldnames

            for row in reader:
                # Beispiel: "2024-03-17T23:00:26.480Z" --> "2024-03-17"
                # Anschließend entfernen wir die Bindestriche für das Ausgabeformat 20240317.csv
                date_str_iso = row["time"].split("T")[0]  # "YYYY-MM-DD"
                date_str = date_str_iso.replace("-", "")  # "YYYYMMDD"
                
                if date_str not in daily_data:
                    daily_data[date_str] = []
                daily_data[date_str].append(row)

# Nun schreiben wir für jedes gefundene Datum eine eigene CSV-Datei nach dem Schema "YYYYMMDD.csv"
for date_str, rows in daily_data.items():
    output_file = os.path.join(output_directory, f"{date_str}.csv")
    print(f"Erstelle Datei für {date_str}: {output_file}")
    with open(output_file, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

print("Fertig! Alle Dateien wurden nach Datum (im Format YYYYMMDD.csv) aufgesplittet und im Ordner 'csv' abgelegt.")

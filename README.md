# Location Visualisation

Folder structure

```
├── all
├── basisdaten
├── csv
├── cumulative
├── cumulative visualisation
├── fast
├── gps
├── locations
├── output
├── points
├── points_yearly
├── shapefile_cumulative
├── shapefile_yearly
├── slow
├── venv
├── visualizations
├── visualizations_geopandas
├── visualizations_with_dates
```

## Scripts:

- `extract_csv_files.py` extracts the data from `/gps` and `/locations` into csv, creating on csv file with geolocations per day, preferebly just a copy from the csv in a zip in gps, opnly if this does not exists, going to the other sources. At the end there should be a csv file with a bunch o geo locations in csv for each day, with a yyymmdd.csv naming scheme like this:

```
time,lat,lon,elevation,accuracy,bearing,speed,satellites,provider,hdop,vdop,pdop,geoidheight,ageofdgpsdata,dgpsid,activity,battery,annotation,timestamp_ms,time_offset,distance,starttimestamp_ms,profile_name,battery_charging
2024-03-19T23:12:40.600Z,48.1861084,11.5593367,561.6000366210938,,,,,network,,,,,,,,,,,,,,,
```

- `calculate_speed_and_filter.py` takes the created csv files and calculates the spüeed between two points. It the creates four geojson files, on is a line between all the points of a day in the folder `/all`, one only contains lines, if the speed, between those points ist above 10 km/h in `/fast`, the next one only contains line sbetween points below 10 km/h `/slow` and last but not least in `/points` are points very 500 meters along the lines with a speed below 10 km/h.

- `cumulative_points.py` takes the points from `/points` and creates a cumulative points file in `/cumulative` with a naming scheme like this `20200319_points.geojson`. These are all points up to that date. Should there be a day, for which no location file was present, there is still a cumulative one. So from now on every date from the start date is covered.

- `combine_pionts_yearly.py` takes the points from _points (which is only points for distances traveled with less then 10 km/h) and creates a cumulative file for each year where 
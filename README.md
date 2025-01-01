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
├── static
├── venv
├── visualizations
├── visualizations_geopandas
├── visualizations_with_dates
```

## Data Colection

Using [GPSLogger for Android](https://gpslogger.app/) (avaliable for fdroid) collecting CSV files with geo locations, which are uploaded into the `/gps` folder. (The `/locations` folder contains data from the now mostly defunct google location history) 

## Scripts:

- `extract_csv_files.py` extracts the data from `/gps` and `/locations` into csv, creating on csv file with geolocations per day, preferebly just a copy from the csv in a zip in gps, opnly if this does not exists, going to the other sources. At the end there should be a csv file with a bunch o geo locations in csv for each day, with a yyymmdd.csv naming scheme like this:

```
time,lat,lon,elevation,accuracy,bearing,speed,satellites,provider,hdop,vdop,pdop,geoidheight,ageofdgpsdata,dgpsid,activity,battery,annotation,timestamp_ms,time_offset,distance,starttimestamp_ms,profile_name,battery_charging
2024-03-19T23:12:40.600Z,48.1861084,11.5593367,561.6000366210938,,,,,network,,,,,,,,,,,,,,,
```

- `calculate_speed_and_filter.py` takes the created csv files and calculates the spüeed between two points. It the creates four geojson files, on is a line between all the points of a day in the folder `/all`, one only contains lines, if the speed, between those points ist above 10 km/h in `/fast`, the next one only contains line sbetween points below 10 km/h `/slow` and last but not least in `/points` are points very 500 meters along the lines with a speed below 10 km/h.

- `cumulative_points.py` takes the points from `/points` and creates a cumulative points file in `/cumulative` with a naming scheme like this `20200319_points.geojson`. These are all points up to that date. Should there be a day, for which no location file was present, there is still a cumulative one. So from now on every date from the start date is covered.

- `combine_pionts_yearly.py` takes the points from _points (which is only points for distances traveled with less then 10 km/h) and creates a file for each year.

- `visualize_points_with_counts.py` creates shapefiles for the yearly points created with `combine_pionts_yearly.py`.

- `visualize_cumulative_points_with_counts.py` now takes the files created in `cumulative_points.py` and creates a shapefile with the counts of the points in each polygon. It creates on shapefile for each day.

- `visualize_points_geopandas.py` takes the shape files created in `visualize_cumulative_points_with_counts.py` and creates a .png using background data from the folder `/basisdaten` for each day.

![](https://raw.githubusercontent.com/TVLuke/location-history/refs/heads/main/static/20230601_visualization.png)

- `visualize_points_geopandas_yearly.py` creates a yearly visualisation, and an aditional file that writs the name on it.

- `create_cropped_images.py` creates cropped images (square and vertical) of the images created by `visualize_points_geopandas.py`.

- `create_video_from_images.py` creates a copy of each of the png created by `visualize_points_geopandas.py` and adds the date to the lower right corner (`/visualizations_with_dates`). All these images are then combined into a .mp4 file.
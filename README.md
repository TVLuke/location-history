# Travel-Lapse

## Data Collection

Using [GPSLogger for Android](https://gpslogger.app/) (available on F-Droid) to collect CSV files with geo-locations, which are uploaded into the `/gps` folder. (The `/locations` folder contains data from the now mostly defunct Google Location History.)

## Scripts

The scripts form a kind of pipeline, each creating files required for the next script.

There is a script called `run_all_scripts.py` which runs all the other scripts. Ideally, this just works.

All scripts have an individual `overwrite` variable, which by default is set to `False`. It controls whether files are recreated or if only files are created that do not yet exist.

### Folder Structure

Not sure all scripts create the folders they need... hopefully. Anyway, the structure is rather flat, like this:

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
    ├── droid
    ├── fantasque
    ├── jetbrains
    ├── mono
├── venv
├── visualizations
├── visualizations_geopandas
├── visualizations_square
├── visualizations_square_with_dates
├── visualizations_vertical
├── visualizations_vertical_with_dates
├── visualizations_with_dates
├── visualizations_with_years
├── visualizations_yearly_geopandas
All the Python files are in the root.
```

- `extract_csv_files.py` extracts the data from `/gps` and `/locations` into CSV files, creating one CSV file with geo-locations per day. Preferably, it uses a copy from the CSV in a zip file in `/gps`. Only if this does not exist does it go to other sources. At the end, there should be a CSV file with a bunch of geo-locations for each day, using a `yyyymmdd.csv` naming scheme like this:


```
time,lat,lon,elevation,accuracy,bearing,speed,satellites,provider,hdop,vdop,pdop,geoidheight,ageofdgpsdata,dgpsid,activity,battery,annotation,timestamp_ms,time_offset,distance,starttimestamp_ms,profile_name,battery_charging
2024-03-19T23:12:40.600Z,48.1861084,11.5593367,561.6000366210938,,,,,network,,,,,,,,,,,,,,,
```


- `calculate_speed_and_filter.py` takes the created CSV files and calculates the speed between two points. It then creates four GeoJSON files: one is a line between all the points of a day in the folder `/all`, one only contains lines if the speed between those points is above 10 km/h (`/fast`), the next one only contains lines between points below 10 km/h (`/slow`), and last but not least, `/points` contains points every 500 meters along the lines with a speed below 10 km/h.

- `cumulative_points.py` takes the points from `/points` and creates a cumulative points file in `/cumulative` with a naming scheme like this: `20200319_points.geojson`. These include all points up to that date. Even if no location file exists for a day, a cumulative one is still present. From now on, every date from the start date is covered.

- `combine_points_yearly.py` takes the points from `/points` (which only include points for distances traveled at less than 10 km/h) and creates a file for each year.

- `visualize_points_with_counts.py` creates shapefiles for the yearly points created with `combine_points_yearly.py`.

- `visualize_cumulative_points_with_counts.py` takes the files created in `cumulative_points.py` and creates a shapefile with the counts of the points in each polygon. It creates one shapefile for each day.

- `visualize_points_geopandas.py` takes the shapefiles created in `visualize_cumulative_points_with_counts.py` and creates a `.png` image using background data from the `/basisdaten` folder for each day.

![](https://raw.githubusercontent.com/TVLuke/location-history/refs/heads/main/static/20230601_visualization.png)

- `visualize_points_geopandas_yearly.py` creates a yearly visualization and an additional file that writes the name on it.

- `create_cropped_images.py` creates cropped images (square and vertical) of the images created by `visualize_points_geopandas.py`.

- `create_video_from_images.py` creates a copy of each of the `.png` files created by `visualize_points_geopandas.py` and adds the date to the lower right corner (`/visualizations_with_dates`). It then also crops these into square and vertical images and adds the date to those as well. All these images are then combined into three `.mp4` files (16:9 4K, vertical, and square video).

Example: https://www.youtube.com/watch?v=zHYTjOnBznY

## Note on Use of LLMs

This code was created using, among other tools, LLM tools like ChatGPT.
# Travel-Lapse

## Data Collection

Using [GPSLogger for Android](https://gpslogger.app/) (available on F-Droid) to collect CSV files with geo-locations. Create daily zip files, which are uploaded into the `/gps` folder. (The `/locations` folder contains data from the now mostly defunct Google Location History.)

## Scripts

The scripts form a kind of pipeline, each creating files required for the next script.

There is a script called `run_all_scripts.py` which runs all the other scripts. Ideally, this just works.

All scripts have an individual `overwrite` variable, which by default is set to `False`. It controls whether files are recreated or if only files are created that do not yet exist.

### Folder Structure

Not sure all scripts create the folders they need... hopefully. Anyway, the structure looks like this:

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
```
All the Python files are in the root.

#### prepare data

To start the process there needs to be CSV Files, with the location track for a day, in the `/csv` Folder, with a naming pattern like `yyyymmdd.csv`. These scripts might help you create them.

- `extract_csv_files.py` extracts the data from `/gps` and `/locations` into CSV files, creating one CSV file with geo-locations per day. Preferably, it uses a copy from the CSV in a zip file in `/gps`. Only if this does not exist does it go to other sources. At the end, there should be a CSV file with a bunch of geo-locations for each day, using a `yyyymmdd.csv` naming scheme like this:
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

```
time,lat,lon,elevation,accuracy,bearing,speed,satellites,provider,hdop,vdop,pdop,geoidheight,ageofdgpsdata,dgpsid,activity,battery,annotation,timestamp_ms,time_offset,distance,starttimestamp_ms,profile_name,battery_charging
2024-03-19T23:12:40.600Z,48.1861084,11.5593367,561.6000366210938,,,,,network,,,,,,,,,,,,,,,
```

- `split_csv_by_day.py` is an alternative to the script above. It takes CSV files in the format described above from the folder `/csv_raw` and splits same into one file per day into `/csv`. This might be helpful if your CSV data is organized monthly.

#### create images and videos
- `calculate_speed_and_filter.py` takes the created CSV files and calculates the speed between two points. It then creates four GeoJSON files: one is a line between all the points of a day in the folder `/all`, one only contains lines if the speed between those points is above 10 km/h (`/fast`), the next one only contains lines between points below 10 km/h (`/slow`), and last but not least, `/points` contains points every 500 meters along the lines with a speed below 10 km/h.
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

- `cumulative_points.py` takes the points from `/points` and creates a cumulative points file in `/cumulative` with a naming scheme like this: `20200319_points.geojson`. These include all points up to that date. Even if no location file exists for a day, a cumulative one is still present. From now on, every date from the start date is covered. **You need to set the start date in the header of this file!**
    - Variables: `start_date` sets the Date from which calculation is done. Must be set like `datetime(2020, 1, 1)`
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

- `combine_points_yearly.py` takes the points from `/points` (which only include points for distances traveled at less than 10 km/h) and creates a file for each year.
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

- `visualize_points_with_counts.py` creates shapefiles for the yearly points created with `combine_points_yearly.py`.
    - Variables: `onlygermany` if Set to `True` only german "Gemeinden" are used, otherwise a european Local Area Units NUTS file is used from http://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/local-administrative-units
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

- `visualize_cumulative_points_with_counts.py` takes the files created in `cumulative_points.py` and creates a shapefile with the counts of the points in each polygon. It creates one shapefile for each day.
    - Variables: `onlygermany` if Set to `True` only german "Gemeinden" are used, otherwise a european Local Area Units NUTS file is used from http://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/local-administrative-units
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

- `visualize_points_geopandas.py` takes the shapefiles created in `visualize_cumulative_points_with_counts.py` and creates a `.png` image using background data from the `/basisdaten` folder for each day. **You need to set the start date in the header of this file!**
    - Variables: `start_date` sets the Date from which calculation is done. Set as String `YYYY-MM-DD`.
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

![](https://raw.githubusercontent.com/TVLuke/location-history/refs/heads/main/static/20230601_visualization.png)

- `visualize_points_geopandas_yearly.py` creates a yearly visualization and an additional file that writes the name on it.
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

- `create_cropped_images.py` creates cropped images (square and vertical) of the images created by `visualize_points_geopandas.py`.

- `create_video_from_images.py` creates a copy of each of the `.png` files created by `visualize_points_geopandas.py` and adds the date to the lower right corner (`/visualizations_with_dates`). It then also crops these into square and vertical images and adds the date to those as well. All these images are then combined into three `.mp4` files (16:9 4K, vertical, and square video).
    - Variables: `overwrite` if Set to `True` already created files are overwritten, otherwise not.

Example: https://www.youtube.com/watch?v=zHYTjOnBznY

## Source Files
- "basisdaten/LAU_RG_01M_2023_3035.shp" from https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/local-administrative-units the data may not be used for commercial puposes. https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units DE: © EuroGeographics bezüglich der Verwaltungsgrenzen 

## Note on Use of LLMs

This code was created using, among other tools, LLM tools like ChatGPT.

# San Jose Deployment Data

This repo contains tooling to manage the transformation of planning and design data of a terragraph deployment. It contains data and a Python framework for storing and manipulating deployment data. Number of files has no impact on the script. Arbitrarily, the tool could consume 1000 files and aggregate/consolidate the data.


##Data Input
There are three input formats this tooling supports. This tooling allows a user to visualize and consume arbitrary site and link data in aggregate. The tooling can consume an arbitrary number of the above formatted text files and output in a standardized output.

1. .csv files[(Comma Separated Delimiter Format)](https://en.wikipedia.org/wiki/CSV): contain a list of attributes of sites(lat/long mandatory).

2. .gv files[(Graph Viz Format)](https://en.wikipedia.org/wiki/DOT_(graph_description_language)): contain an association of sites.

3. .geojson/json[(GeoJSON format)](https://en.wikipedia.org/wiki/GeoJSON): can contain any geospasial data.


###CSV Input File Details
The csv format currently only supports site data. That data can have any arbitrary name and is defined by the horizontal column names.

**site_id** column
This field is used to uniquely identify a site. If two data records have the same side_id, the associated data is assumed to belong to the same site.

**latitude** column
This filed is optional, but defaults to 0.0 if no file ever provides a valid value.

**longitude** column
This field is optional, but defaults to 0.0 if no file ever provides a valid value.

**data_weight** column
This field is optional and controls the aggregation behavior of the tool. The value can be any integer(positive or negative). A higher value is weighted more than a lower value(e.g. 100 is weighted more heavily than a 70). If the field is not provided, the default weight of a record is 0.

**bill_of_materials** column
This field is optional and defines the devices that will be installed on the sites - separated by spaces. For example: "CN odroid" has two devices in the BOM. "DN DN DN odroid" has 2 secondary and one primary DN in the BOM.

NOTE: **latitude**  and **longitude** need to be defined at least once for a site to properly render on a map. If they are not referenced in any file, the site will show up on the equator / Prime meridian (i.e. latitude of 0.0 and longitude of 0.0)

CSV file naming has no impact on the script.

EXAMPLE FORMAT
```
site_id,   latitude,       longitude,       data_weight,    description,     other_data1
12M541,    37.33251834,    -121.8836879,    34,             S 4TH ST 345,    Some value
```

###GV Input File Details

All connections in gv files relate to a **site_id** defined in other files.  

EXAMPL FORMAT
```
graph example_format {

// Some note about a link
12L198 -- 12L197

}
```
The above example asserts that site 12L198 has a link to 12L197. For this example to properly associate the data, both 12L198 and 12L197 must be a defined site_id in at least one file. The tooling will provide feedback if any site is not known for links defined in the .gv file.

###GeoJSON Input File Details
This is not well build and will likely break because error checking is not very robust for this format. Recommend not using this unless you are certain that the


##Data Output
The tool outputs several files in various formats into an export directory. Within that directory, files will be exported to a date specific directory(e.g. files would be placed in "exports/01-02-2017/"" for an export on January 1st).

The file output is:
1. **design_layout.geojson** Is all aggregated sites that are connected by links in geojson format. It can be rendered or consumed by any service that supports the format. [GeoJSON.io](http://geojson.io/) is one such visualization platform.

2. **design_layout.kml** Is all sites that are connected by links in kml format. This is further grouped by .gv file within the kml document. [Google Earth](https://www.google.com/earth/) is one such visualization platform.

3. **summary.txt** Is analysis, statics and calculation results of the input files.



## Installing The  Tooling:
1. Install python(2.7 only due to some library dependencies)
```
brew install python

      or

sudo apt-get install python
```

2. Download the github folder and change to that directory
```
git clone https://github.com/THADEUSH123/design-transformer.git

cd design-transformer
```

3. Install the python package
```
python setup.py install
```

## Running the tool
From any folder with relevant files, run
```
data_transformer
```

## Development
More data format converters and file manipulation scripts are coming.

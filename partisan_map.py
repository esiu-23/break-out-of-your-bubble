import geopandas as gpd
import pandas as pd

from bokeh.io import show
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          CustomJS, CustomJSFilter, 
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.plotting import figure
import json

# Read in shapefile and examine data
county_files = gpd.read_file('data/tl_2020_us_county.shp')
#county_files.head()

# Read in elections data and examine data
elections = pd.read_csv('data/elections.csv')
#elections.head()
elections_2016 = elections[ elections["year"] == 2016]

# Convert GEOIDs column to match same numbering format as fips in the elections file
geoids = county_files['GEOID'].tolist()
stripped_ids = [ids.lstrip("0") for ids in geoids]
county_files["stripped_geoids"] = stripped_ids
county_files['stripped_geoids'] = county_files['stripped_geoids'].astype("int64")
#county_files.head()

# Merge shapefile with elections data
partisan_counties = county_files.merge(elections_2016, left_on = "stripped_geoids", right_on = "fips")
#partisan_counties.head()

partisan_counties["perc_red"] = partisan_counties["rvotes"] / (partisan_counties["rvotes"] + partisan_counties["dvotes"] )
partisan_counties["perc_blue"] = partisan_counties["dvotes"] / (partisan_counties["rvotes"] + partisan_counties["dvotes"] )

#partisan_counties.head()

# Define color palettes
palette = brewer['RdBu'][10]

# Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 1)

# Define custom tick labels for color bar.
tick_labels = {"0.0": "0%", "0.1": "10%", "0.2": "20%", "0.3": "30%",
"0.4": "40%", "0.5": "50%", "0.6": "60%", "0.7": "70%", "0.8": "80%", 
"0.9": "90%", "1.0": "100%"}

# Create color bar.
color_bar = ColorBar(color_mapper = color_mapper, 
                     label_standoff = 10,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0), 
                     orientation = "horizontal",
                     major_label_overrides = tick_labels)

### SINGLE STATE EXAMPLE
# alaska = county_files[county_files['STATEFP'] == '02']
# ak_source = GeoJSONDataSource(geojson = alaska.to_json())

# p = figure(title = 'Alaska by political party affiliation (2016)', 
#            plot_height = 60,
#            plot_width = 120)
# p.xgrid.grid_line_color = None
# p.ygrid.grid_line_color = None

# states = p.patches("xs","ys", source = ak_source,
#                    fill_color = {"field" :'perc_red',
#                                  "transform" : color_mapper},
#                    line_color = "black", 
#                    line_width = 0.25, 
#                    fill_alpha = 1)

# p.add_tools(HoverTool(renderers = [states],
#                       tooltips = [('% Republican Votes','@perc_red'),
#                                 ('% Democratic Votes','@perc_blue')]))

# Make a slider object to toggle the month shown
# slider = Slider(title = "Year",
#                 start = 1984, end = 2016,
#                 step = 4, value = 2016)

# ColumnDataSource(ak_source)

# # This callback triggers the filter when the slider changes
# callback = CustomJS(args = dict(source=ak_source), 
#                     code = """source.change.emit();""")
# slider.js_on_change('value', callback)
# # Creates custom filter that selects the rows of the month based on the value in the slider
# custom_filter = CustomJSFilter(args = dict(slider = slider, 
#                                            source = ak_source), 
#                                code = """
# var indices = [];
# // iterate through rows of data source and see if each satisfies some constraint
# for (var i = 0; i < source.get_length(); i++){
#  if (source.data[‘Year’][i] == slider.value){
#  indices.push(true);
#  } else {
#  indices.push(false);
#  }
# }
# return indices;
# """)
# # Uses custom_filter to determine which set of sites are visible
# view = CDSView(source = ak_source, filters = [custom_filter])


# Create figure object.
geosource = GeoJSONDataSource(geojson = partisan_counties.to_json())
p = figure(title = 'Map of the US by political party affiliation (2016)', 
           plot_height = 600,
           plot_width = 2000,
           toolbar_location = 'below',
           tools = "pan,wheel_zoom,box_zoom,reset")
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

states = p.patches("xs","ys", source = geosource,
                   fill_color = {"field" :'perc_red',
                                 "transform" : color_mapper},
                   line_color = "black", 
                   line_width = 0.25, 
                   fill_alpha = 1)

p.add_tools(HoverTool(renderers = [states],
                      tooltips = [('% Republican Votes','@perc_red'),
                                ('% Democratic Votes','@perc_blue')]))

show(p)
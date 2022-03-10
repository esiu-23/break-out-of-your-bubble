import json
import traceback
import sys
import csv
import os

import geopandas as gpd
import pandas as pd

from functools import reduce
from operator import and_

from django.shortcuts import render
from django import forms

from bokeh.models import (ColorBar, GeoJSONDataSource, HoverTool,
                          LinearColorMapper)
from bokeh.palettes import brewer
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import INLINE

from access_db import find_counties

NOPREF_STR = 'No preference'
RES_DIR = os.path.join(os.path.dirname(__file__), '..', 'res')

COLUMN_NAMES = dict(
    nat="% Naturalized Citizens",
    lim_eng="% with Limited English",
    low_ed="Low Ed Attain",
    below_pov="% Below poverty line",
    med_rent="Median rent",
    uninsured="% Uninsured",
    county_name="County name",
    state_name="State name",
    racial_dem="Racial demography"
)


def _valid_result(res):
    """Validate results returned by find_counties."""
    (HEADER, RESULTS) = [0, 1]
    ok = (isinstance(res, (tuple, list)) and
          len(res) == 2 and
          isinstance(res[HEADER], (tuple, list)) and
          isinstance(res[RESULTS], (tuple, list)))
    if not ok:
        return False

    n = len(res[HEADER])

    def _valid_row(row):
        return isinstance(row, (tuple, list)) and len(row) == n
    return reduce(and_, (_valid_row(x) for x in res[RESULTS]), True)


def _load_column(filename, col=0):
    """Load single column from csv file."""
    with open(filename) as f:
        col = list(zip(*csv.reader(f)))[0]
        return list(col)


def _load_res_column(filename, col=0):
    """Load column from resource directory."""
    return _load_column(os.path.join(RES_DIR, filename), col=col)


def _build_dropdown(options):
    """Convert a list to (value, caption) tuples."""
    return [(x, x) if x is not None else ('', NOPREF_STR) for x in options]


# Update with county drop down
STATES = _build_dropdown([None] + _load_res_column('state_list.csv'))
COUNTIES = _build_dropdown([None] + _load_res_column('county_list.csv'))
DEMOS = _build_dropdown(_load_res_column('demos_list.csv'))

# Update with all of our demographics & suggestion text
class SearchForm(forms.Form):
    
    state = forms.ChoiceField(
        label='State',
        choices=STATES,
        help_text= 'Select the state you currently live in', 
        required=True)
    
    county = forms.ChoiceField(
        label='County', 
        choices=COUNTIES, 
        help_text= 'Select the county you currently live in', 
        required=True)
    
    dissimilarity = forms.FloatField(
        required=True, 
        widget=forms.TextInput(attrs={'type': 'number','min': '0','max':'100','step':'0.01'}), 
        label="Dissimilarity Range \n (+/- %))",
        help_text='Choose your appetite for demographic dissimilarity: \n e.g., 5 means +/- 5%')

    demographics = forms.MultipleChoiceField(label='Demographics',
                                     choices=DEMOS,
                                     widget=forms.CheckboxSelectMultiple,
                                     required=True)
    
    show_args = forms.BooleanField(label='Show args_to_ui',
                                    required=False)

def home(request):
    context = {}
    res = None
    if request.method == 'GET':
        # create a form instance and populate it with data from the request:
        form = SearchForm(request.GET)
        # check whether it's valid:
        if form.is_valid():

            # Convert form data to an args dictionary for find_counties
            args = {}
            
            args['dissimilarity'] = form.cleaned_data['dissimilarity']
            args['demographics'] = form.cleaned_data['demographics']
            
            args['state'] = form.cleaned_data['state']
            args['county'] = form.cleaned_data['county']

            if form.cleaned_data['show_args']:
                context['args'] = 'args_to_ui = ' + json.dumps(args, indent=2)

            try:
                res = find_counties(args)
            except Exception as e:
                print('Exception caught')
                bt = traceback.format_exception(*sys.exc_info()[:3])
                context['err'] = """
                An exception was thrown in find_counties:
                <pre>{}
{}</pre>
                """.format(e, '\n'.join(bt))

                res = None
    else:
        form = SearchForm()

    # Handle different responses of res
    if res is None:
        context['result'] = None
    elif isinstance(res, str):
        context['result'] = None
        context['err'] = res
        result = None
    elif not _valid_result(res):
        context['result'] = None
        context['err'] = ('Return of find_counties has the wrong data type. '
                          'Should be a tuple of length 4 with one string and '
                          'three lists.')
    else:
        columns, result = res

        # Wrap in tuple if result is not already
        if result and isinstance(result[0], str):
            result = [(r,) for r in result]

        context['result'] = result
        context['num_results'] = len(result)
        context['columns'] = [COLUMN_NAMES.get(col, col) for col in columns]

    context['form'] = form

# ### EMBED BOKEH PLOT

#     # Read in shapefile and examine data
#     county_files = gpd.read_file('data/tl_2020_us_county.shp')

#     # Read in elections data and examine data
#     elections = pd.read_csv('data/elections.csv')
#     elections_2016 = elections[ elections["year"] == 2016]

#     # Convert GEOIDs column to match same numbering format as fips in the elections file
#     geoids = county_files['GEOID'].tolist()
#     stripped_ids = [ids.lstrip("0") for ids in geoids]
#     county_files["stripped_geoids"] = stripped_ids
#     county_files['stripped_geoids'] = county_files['stripped_geoids'].astype("int64")
#     county_files['STATEFP'] = county_files['STATEFP'].astype("int64")
#     contiguous = county_files[county_files.STATEFP != 15]

#     # Merge shapefile with elections data
#     partisan_counties = contiguous.merge(elections_2016, left_on = "stripped_geoids", right_on = "fips")
#     partisan_counties["perc_red"] = (partisan_counties["rvotes"] / (partisan_counties["rvotes"] + partisan_counties["dvotes"] )) * 100
#     partisan_counties["perc_blue"] = (partisan_counties["dvotes"] / (partisan_counties["rvotes"] + partisan_counties["dvotes"] )) * 100

#     geosource = GeoJSONDataSource(geojson = partisan_counties.to_json())

#     # Define color palettes
#     palette = brewer['RdBu'][10]

#     # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
#     color_mapper = LinearColorMapper(palette = palette, low = 0, high = 100)

#     # Define custom tick labels for color bar.
#     tick_labels = {"0.0": "0%", "0.1": "10%", "0.2": "20%", "0.3": "30%",
#     "0.4": "40%", "0.5": "50%", "0.6": "60%", "0.7": "70%", "0.8": "80%", 
#     "0.9": "90%", "1.0": "100%"}

#     # Create color bar.
#     color_bar = ColorBar(color_mapper = color_mapper, 
#                         label_standoff = 10,
#                         width = 500, height = 20,
#                         border_line_color = None,
#                         location = (0,0), 
#                         orientation = "horizontal",
#                         major_label_overrides = tick_labels)

#     # Create figure object.
#     p = figure(title = 'Map of the US by political party affiliation (2016)', 
#             plot_height = 400,
#             plot_width = 600, 
#             toolbar_location = 'below',
#             tools = "pan,wheel_zoom,box_zoom,reset")
#     p.xgrid.grid_line_color = None
#     p.ygrid.grid_line_color = None

#     # Render counties
#     counties = p.patches("xs","ys", source = geosource,
#                     fill_color = {"field" :'perc_red',
#                                     "transform" : color_mapper},
#                     line_color = "black", 
#                     line_width = 0.25, 
#                     fill_alpha = 1)

#     # Add hover tool
#     p.add_tools(HoverTool(renderers = [counties],
#                         tooltips = [("County", '@NAMELSAD'),
#                                         ('Year', "@year"), 
#                                         ('% Republican Votes','@perc_red'),
#                                     ('% Democratic Votes','@perc_blue')]))   

#     #Store components 
#     script, div = components(p)

#     context['script'] = script
#     context['div'] = div
#     context['resources'] = INLINE.render
    
    return render(request, 'index.html', context)
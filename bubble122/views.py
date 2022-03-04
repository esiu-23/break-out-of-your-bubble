# from django.shortcuts import render
# from django.http import HttpResponse

# # Create your views here.
# # Request handler

# ###This is where you are going to build most of the UI code.
# ### Look into the various tools that were used on PA3 UI and translate them
# ### Need to figure out the SQL connection

# def interact(request):
#     '''
#     '''

#     return HttpResponse('bubble up pup')

import json
import traceback
import sys
import csv
import os

import geopandas as gpd
import pandas as pd

from functools import reduce
from operator import and_

from django.shortcuts import render, render_to_response
from django import forms

from bokeh.io import show
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          CustomJS, CustomJSFilter, 
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.plotting import figure
from bokeh.embed import components

from access_db import find_counties

NOPREF_STR = 'No preference'
RES_DIR = os.path.join(os.path.dirname(__file__), '..', 'res')

## Update our column names 
COLUMN_NAMES = dict(
    nat="naturalized",
    lim_eng="limited_english",
    low_ed="low_ed_attain",
    below_pov="below_poverty",
    med_rent="median_rent",
    uninsured="uninsured",
    county_name="county_name",
    state_name="state_name",
    racial_dem="racial_demography"
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
STATES = _build_dropdown([None] + _load_res_column('state_names.csv'))
COUNTIES = _build_dropdown([None] + _load_res_column('county_names.csv'))


class IntegerRange(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (forms.IntegerField(),
                  forms.IntegerField())
        super(IntegerRange, self).__init__(fields=fields,
                                           *args, **kwargs)

    def compress(self, data_list):
        if data_list and (data_list[0] is None or data_list[1] is None):
            raise forms.ValidationError('Must specify both lower and upper '
                                        'bound, or leave both blank.')

        return data_list


class DissimilarityRange(IntegerRange):
    def compress(self, data_list):
        super(DissimilarityRange, self).compress(data_list)
        for v in data_list:
            if not -100 <= v <= 100:
                raise forms.ValidationError(
                    'Dissimilarity range must be -100 and 100.')
        if data_list and (data_list[1] < data_list[0]):
            raise forms.ValidationError(
                'Lower bound must not exceed upper bound.')
        return data_list

# Update with all of our demographics & suggestion text
class SearchForm(forms.Form):
    
    state = forms.ChoiceField(label='State', choices=STATES, required=True)
    county = forms.ChoiceField(label='County', choices=COUNTIES, required=True)
    
    dissimilarity = DissimilarityRange(
        label='Dissimilarity Range (lower/upper)',
        help_text="Choose how dissimilar a county can be from yours (e.g., entering 10 would mean \
            we would surface all counties whose demographics vary within +/- 10'%' \
                from the county you currently live in.",
        widget=forms.widgets.NumberInput,
        required=True)
    
    demographics = forms.MultipleChoiceField(label='Demographics',
                                     choices=COLUMN_NAMES,
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
            
            dissimilarity = form.cleaned_data['dissimilarity']
            args['dissimilarity'] = dissimilarity

            demographics = forms.cleaned_data['demographics']
            args['demographics'] = demographics

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

### EMBED BOKEH PLOT

# def index(request):

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
#     #county_files.head()

#     # Merge shapefile with elections data
#     partisan_counties = county_files.merge(elections_2016, left_on = "stripped_geoids", right_on = "fips")
#     partisan_counties["perc_red"] = partisan_counties["rvotes"] / (partisan_counties["rvotes"] + partisan_counties["dvotes"] )

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
#             plot_height = 600,
#             plot_width = 1200, 
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
   
#    #Store components 
#     script, div = components(plot)

#     #Feed them to the Django template. Use render instead of render_to_response
#     return render_to_response( 'bokeh/index.html',
#             {'script' : script , 'div' : div} )


    ## OLD return statement
    return render(request, 'index.html', context)
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

from functools import reduce
from operator import and_

from django.shortcuts import render
from django import forms

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
    """Validate results returned by find_courses."""
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
        super(EnrollmentRange, self).compress(data_list)
        for v in data_list:
            if not 1 <= v <= 100:
                raise forms.ValidationError(
                    'Dissimilarity range must be 1 and 100.)
        if data_list and (data_list[1] < data_list[0]):
            raise forms.ValidationError(
                'Lower bound must not exceed upper bound.')
        return data_list

# May or may not need range widget depending on what entries we let people put in
RANGE_WIDGET = forms.widgets.MultiWidget(widgets=(forms.widgets.NumberInput,
                                                  forms.widgets.NumberInput))

# Update with all of our demographics & suggestion text
class SearchForm(forms.Form):
    
    state = forms.ChoiceField(label='State', choices=STATES, required=True)
    county = forms.ChoiceField(label='County', choices=COUNTIES, required=True)
    
    dissimilarity = DissimilarityRange(
        label='Dissimilarity Range (lower/upper)',
        help_text='e.g. 1 and 10',
        widget=RANGE_WIDGET,
        required=True)
    
    demographics = forms.MultipleChoiceField(label='Demographics',
                                     choices=COLUMN_NAMES,
                                     widget=forms.CheckboxSelectMultiple,
                                     required=True)
    # show_args = forms.BooleanField(label='Show args_to_ui',
    #                                required=False)

def home(request):
    context = {}
    res = None
    if request.method == 'GET':
        # create a form instance and populate it with data from the request:
        form = SearchForm(request.GET)
        # check whether it's valid:
        if form.is_valid():

            ## We don't need this step, we can just put in the SQL query.
            
            # Convert form data to an args dictionary for find_courses
            args = {}

            if enroll:
                args['enrollment'] = (enroll[0], enroll[1])
            time = form.cleaned_data['time']
            if time:
                args['time_start'] = time[0]
                args['time_end'] = time[1]

            days = form.cleaned_data['days']
            if days:
                args['day'] = days
            dept = form.cleaned_data['dept']
            if dept:
                args['dept'] = dept

            time_and_building = form.cleaned_data['time_and_building']
            if time_and_building:
                args['walking_time'] = time_and_building[0]
                args['building_code'] = time_and_building[1]

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
    return render(request, 'index.html', context)
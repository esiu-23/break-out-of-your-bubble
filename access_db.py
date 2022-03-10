'''
MSCAPP 122 Final Project
Cole von Glahn
'''

import pandas as pd
import sqlite3
import os

# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'bubble_tables.db')


ACS_KEYS = set(["naturalized", "limited_english", "low_ed_attain", 
                "below_poverty", "median_rent", "uninsured"])
CENSUS_KEYS = set(["white", "black", "native", "asian", "pacific", "other"])

def find_counties(user_inputs):
    '''
    '''
    threshold = user_inputs['dissimilarity'] / 100
    conn = sqlite3.connect("bubble_tables.db")
    curse = conn.cursor()

    if not bool(user_inputs.keys()):
        return []

    select_stmt, acs, census = build_select(user_inputs)

    from_stmt = build_from(acs, census)

    param_dict = get_original(user_inputs, from_stmt, curse, threshold)

    where_statement, params = build_where(user_inputs, param_dict, acs, census)

    query = select_stmt + from_stmt + where_statement

    rv = curse.execute(query, params).fetchall()

    output = ideology_sort(rv)

    conn.close

    return output

def ideology_sort(demo_group):
    '''
    '''
    original = demo_group[0]

    dvotes = original[2]
    rvotes = original[3]
    all_votes = dvotes + rvotes
    perc_dem = dvotes / all_votes
    perc_rep = rvotes / all_votes

    o_rebuild = []
    for element in original:
        o_rebuild.append(element)
    o_rebuild.insert(4, perc_dem)
    o_rebuild.insert(5, perc_rep)

    full_original = tuple(o_rebuild)   

    output = []
    for match in demo_group[1:]:
        rebuild= []
        dvotes = match[2]
        rvotes = match[3]
        all_votes = dvotes + rvotes
        perc_dem = dvotes / all_votes
        perc_rep = rvotes / all_votes
        perc_diff = abs(perc_dem - full_original[4])
        for element in match:
            rebuild.append(element)
        rebuild.insert(4, perc_dem)
        rebuild.insert(5, perc_rep)
        rebuild.insert(6, perc_diff)
        tuple(rebuild)
        output.append(rebuild)
    
    output = sorted(output, key = lambda x: x[6], reverse = True)
    output.insert(0, full_original)

    return output

    


    # add to the return tuples %red, %blue, %diff_from_original
    # sort by %diff descending
    # pop last element and insert at index 0
    


def get_original(user_inputs, f_state, cursor, threshold):
    '''
    '''

    home_state = user_inputs['state']
    home_county = user_inputs['county']
    param_dict = {}

    
    w_state = f''' WHERE elections.state = "{home_state}"
                  AND elections.county = "{home_county}"
                  AND elections.year = 2016'''

    for arg, val in user_inputs.items():
        select_dict = {}
        if isinstance(val, bool) and val:
            select_dict[arg] = 0
            s_state, acs, census = build_select(select_dict, False)
            f_state = build_from(acs, census)
            query = s_state + f_state + w_state
            values = cursor.execute(query).fetchall()
            if arg != "median_rent":
                bot_range = max(values[0][2] - threshold, 0)
                top_range = min(values[0][2] + threshold, 1)
            else:
                diff = values[0][2] * threshold
                bot_range = max(values[0][2] - diff, 0)
                top_range = values[0][2] + diff
            param_dict[arg] = (bot_range, top_range)
    

    return (param_dict)


def build_select(user_inputs, base = True):
    '''
    '''
    query_extension = ''
    join_acs = False
    join_census = False
    if base:
        base_fragment = '''SELECT elections.state, elections.county, elections.dvotes, elections.rvotes'''
    else:
        base_fragment = "SELECT elections.state, elections.county"

    # parameterize to defend against injection
    for key in user_inputs:
        if key in ACS_KEYS:
            query_extension += f", acs.{key}"
            join_acs = True
        if key in CENSUS_KEYS:
            query_extension += f", census.{key}"
            join_census = True
    
    select_stmt = base_fragment + query_extension

    return (select_stmt, join_acs, join_census)


def build_from(acs, census):
    '''
    '''
    
    from_stmt = " FROM elections "
    if acs:
        from_stmt += "JOIN acs ON elections.fips = acs.fips"
    if census:
        from_stmt += " JOIN census ON elections.fips = census.fips"

    return from_stmt


def build_where(user_inputs, param_dict, acs, census):
    '''
    '''
    ## How do you want to handle median rent?
    ## Implement the +- either in here or in a dedicated helper to here


    pieces = []
    params = []
    base_query = " WHERE elections.year = 2012 "
    where_dict = {
        "naturalized": "acs.naturalized BETWEEN ? AND ?",
        "limited_english": "acs.limited_english BETWEEN ? AND ?",
        "low_ed_attain": "acs.low_ed_attain BETWEEN ? AND ?",
        "below_poverty": "acs.below_poverty BETWEEN ? AND ?",
        "median_rent": "acs.median_rent BETWEEN ? AND ?",
        "uninsured": "acs.uninsured BETWEEN ? AND ?",

        "white": "census.white BETWEEN ? AND ?",
        "black": "census.black BETWEEN ? AND ?",
        "native": "census.native BETWEEN ? AND ?",
        "asian": "census.asian BETWEEN ? AND ?",
        "pacific": "census.pacific BETWEEN ? AND ?",
        "other": "census.other BETWEEN ? AND ?"
    }

    for arg, val in user_inputs.items():
        if arg == "state" or arg == "county":
            continue
        if isinstance(val, bool) and val:
            params.append(param_dict[arg][0])
            params.append(param_dict[arg][1])
            pieces.append(where_dict[arg])

    conditions = "AND " + " AND ".join(pieces)
    where_stmt = base_query + conditions
    return (where_stmt, params)


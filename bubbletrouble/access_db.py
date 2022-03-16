'''
MSCAPP 122 Final Project
Cole von Glahn, Evelyn Siu, Carolyn Vilter
'''

import sqlite3
import os

#filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'bubble_tables.db')


ACS_KEYS = set(["naturalized", "limited_english", "low_ed_attain",
                "below_poverty", "median_rent", "uninsured"])
CENSUS_KEYS = set(["white", "black", "native", "asian", "pacific", "other"])

INPUT_TRANSLATION = {
        "% Naturalized Citizens": "naturalized",
        "% with Limited English": "limited_english",
        "% Low Ed Attain": "low_ed_attain",
        "% Below poverty line": "below_poverty",
        "Median rent": "median_rent",
        "% Uninsured": "uninsured",
        "% White": "white",
        "% Black": "black",
        "% Native American": "native",
        "% Asian": "asian",
        "% Pacific Islander": "pacific",
        "% Other": "other"
}

def find_counties(user_inputs):
    '''
    Compares the political ideology and demographic characteristics of U.S.
    counties to the given county of interest. Determines similarities within
    a user-defined threshold and returns the demographically similar counties
    in descending order of political dissimilarity.

    args:
        user_inputs (dict): A dictionary containing the starting county,
            characteristics of interest, and dissimilarity tolerance.

    outputs:
        hdr (list): Columns associated with the characteristics of interest.
        output (list of tuples): Contains collected counties within threshold,
            sorted by dissimilarity.
    '''
    # Connect to database
    conn = sqlite3.connect("bubble_tables.db")
    curse = conn.cursor()

    # Store dissimilarity tolerance
    threshold = user_inputs['dissimilarity']

    # Translate UI headings into SQL columns
    translated = []
    for demo in user_inputs['demographics']:
        translated.append(INPUT_TRANSLATION[demo])
    user_inputs['demographics'] = translated

    # Build db queries and collect foundational information.
    select_stmt, acs, census = build_select(user_inputs)
    from_stmt = build_from(acs, census)
    param_dict, original_row = get_original(user_inputs, curse, threshold)
    where_statement, params = build_where(user_inputs, param_dict)

    query = select_stmt + from_stmt + where_statement

    # Query for similar counties.
    demo_group = curse.execute(query, params).fetchall()

    # Sort counties by ideological difference and prepare headers for output.
    output = ideology_sort(demo_group, original_row)
    hdr = get_header(curse)

    conn.close()

    return (hdr, output)


def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)

    Adapted from code provided for CS122 PA3 Prof. Lamont Samuels.
    '''
    header = []

    for i in cursor.description:
        s = i[0]
        if "." in s:
            s = s[s.find(".")+1:]
        header.append(s)

    # Insert values calculated after SQL query execution
    header.insert(4,"% Difference in Voting Behavior")
    header.insert(5,"% Dem Voters")
    header.insert(6,"% Rep Voters")

    return header


def build_select(user_inputs, base = True):
    '''
    Builds the SELECT clause of a SQL query dependent on user input.

    Args:
        user_inputs (dict): A dictionary containing the starting county,
            characteristics of interest, and dissimilarity tolerance.
        base (bool): Sorts query requests between internal need and output.

    Outputs:
        select_stmt (string): The SELECT clause
        join_census (bool): Whether or not to join the census table
        join_acs (bool): Whether or not to join the acs table
    '''

    query_extension = ''
    join_acs = False
    join_census = False

    if base:
        # Constructs select statement for output query.
        base_fragment = '''SELECT elections.state, elections.county,
            elections.dvotes, elections.rvotes'''
        for arg in user_inputs['demographics']:
            # Adds and flags for ACS demographics
            if arg in ACS_KEYS:
                query_extension += f", acs.{arg}"
                join_acs = True
            # Adds and flags for census demographics
            if arg in CENSUS_KEYS:
                query_extension += f", census.{arg}"
                join_census = True
    else:
        # Constructs select statement for internal query.
        base_fragment = "SELECT elections.state, elections.county"
        for arg in user_inputs:
            # Adds and flags for ACS demographics
            if arg in ACS_KEYS:
                query_extension += f", acs.{arg}"
                join_acs = True
            # Adds and flags for census demographics
            if arg in CENSUS_KEYS:
                query_extension += f", census.{arg}"
                join_census = True

    # Completes select statement with generated pieces
    select_stmt = base_fragment + query_extension

    return (select_stmt, join_acs, join_census)


def build_from(acs, census):
    '''
    Builds the FROM clause for SQL query based on requested demographics.

    Args:
        join_census (bool): Whether or not to join the census table
        join_acs (bool): Whether or not to join the acs table

    Outputs:
        from_stmt (string): The FROM clause
    '''

    from_stmt = " FROM elections "
    if acs:
        from_stmt += "JOIN acs ON elections.fips = acs.fips"
    if census:
        from_stmt += " JOIN census ON elections.fips = census.fips"

    return from_stmt


def build_where(user_inputs, param_dict):
    '''
    Builds the WHERE clause for SQL query based on requested demographics.

    Args:
        user_inputs (dict): A dictionary containing the starting county,
            characteristics of interest, and dissimilarity tolerance.
        param_dict (dict): Contains the calculated values for the original
                county for comparison.
        Outputs:
            where_stmt (string): The WHERE clause for SQL query.
            params (list): The parameters for use by .execute.fetchall()

    '''

    pieces = []
    params = []
    base_query = " WHERE elections.year = 2016 "

    # The mapping of input demographics to WHERE clause portions.
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

    # Attaches individual statements and saves for later execution parameters.
    for arg in user_inputs['demographics']:
        params.append(param_dict[arg][0])
        params.append(param_dict[arg][1])
        pieces.append(where_dict[arg])

    # Combines individual statements.
    if len(pieces) > 0:
        conditions = "AND " + " AND ".join(pieces)
    else:
        conditions = ''

    # Constructs query out of pieces.
    where_stmt = base_query + conditions

    return (where_stmt, params)


def get_original(user_inputs, cursor, threshold):
    '''
    Collects information on original county for later comparison and ordering.

    Args:
        user_inputs (dict): A dictionary containing the starting county,
            characteristics of interest, and dissimilarity tolerance.
        cursor (Cursor): Database cursor object.
        threshold (float): The user's dissimilarity tolerance.

    Outputs:
        param_dict (dict): Contains the calculated values for the original
                county for comparison.
        values (list): The identifying values of the original county.
    '''

    # Collect county identifiers
    home_state = user_inputs['state']
    home_county = user_inputs['county']
    param_dict = {}

    # WHERE clause for internal query
    w_state = f''' WHERE elections.state = "{home_state}"
                  AND elections.county = "{home_county}"
                  AND elections.year = 2016'''

    # query individual pieces of county information
    for arg in user_inputs['demographics']:
        select_dict = {}
        select_dict[arg] = None
        s_state, acs, census = build_select(select_dict, False)
        f_state = build_from(acs, census)
        query = s_state + f_state + w_state
        values = cursor.execute(query).fetchall()

        # Calculate ranges for fields of percents expressed as decimals.
        if arg != "median_rent":
            bot_range = max(values[0][2] - threshold, 0)
            top_range = values[0][2] + threshold
        # Calculate ranges for fields of integer values.
        else:
            diff = values[0][2] * (threshold / 100)
            bot_range = max(values[0][2] - diff, 0)
            top_range = values[0][2] + diff

        # Output ranges for parameterization.
        param_dict[arg] = (bot_range, top_range)

    return (param_dict, values)


def ideology_sort(demo_group, original_row):
    '''
    Compares original county to DB of counties on elections and
    demographics selecting those within the user's tolerance range.

    Args:
        demo_group (list): The matched counties.
        original_row (tuple): Information on the original county.
    '''
    # Store original county information.
    home_state = original_row[0][0]
    home_county = original_row[0][1]

    # Find the original county entry.
    for val in demo_group:
        if val[0] == home_state and val[1] == home_county:
            original = val
            break

    # Process comparison information for original county.
    o_dvotes = original[2]
    o_rvotes = original[3]
    o_all_votes = o_dvotes + o_rvotes
    o_perc_dem = (o_dvotes / o_all_votes)

    # Add output information to matched counties
    output = []
    for match in demo_group:
        rebuild= []

        # Collect voter data
        dvotes = match[2]
        rvotes = match[3]
        all_votes = dvotes + rvotes

        # Process voter information
        perc_dem = dvotes / all_votes
        perc_rep = rvotes / all_votes
        perc_diff = abs(perc_dem - o_perc_dem)

        # Rebuild tuples for output with calculated information.
        for element in match:
            rebuild.append(element)
        rebuild.insert(4, round(perc_diff * 100, 2))
        rebuild.insert(5, round(perc_dem * 100, 2))
        rebuild.insert(6, round(perc_rep * 100, 2))
        tuple(rebuild)
        output.append(rebuild)

    # Sort output list by descending ideological dissimilarity
    # compared to original county
    output = sorted(output, key = lambda x: x[4], reverse = True)

    # Find original county and move to the top
    for i, row in enumerate(list(reversed(output))):
        if row[0] == home_state and row[1] == home_county:
            home_position = -i - 1
            top_row = []
            for element in row:
                top_row.append(element)
            break

    # Identify, repack, and topdeck original county. Remove duplicate.
    top_row[4] = "COUNTY OF INTEREST"
    tuple(top_row)
    output.insert(0, top_row)
    output.pop(home_position)

    return output

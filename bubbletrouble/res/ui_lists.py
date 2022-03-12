import sqlite3
import csv


def generate_lists():

    ###  Replace with name of our database
    connection = sqlite3.connect('../bubble_tables.db')
    c = connection.cursor()

    # get lists of unique values from sql database
    state = c.execute('''SELECT DISTINCT state FROM elections''').fetchall()
    county = c.execute('''SELECT DISTINCT county FROM elections''').fetchall()
    
    # Making the county list (drop-down) more usable:
    for i, _ in enumerate(county):  # de-tuple
        county[i] = county[i][0]            
    county = set(county)  # use set to deduplicate
    county = list(county)  # back to list
    county.sort()  # alphabetize
    county.remove('county')  # remove the header

    connection.close()


    ### Update for our files we want to generate

    # write lists of unique values to file
    f = open('state_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for i, row in enumerate(state):
        if i!=0:   # don't write out the header row
            w.writerow(row)
    f.close()

    f = open('county_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for row in county:
        w.writerow({row})
    f.close()

generate_lists()
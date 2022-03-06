import sqlite3
import csv


def generate_lists():

    ###  Replace with name of our database
    connection = sqlite3.connect('../../bubble_tables.db')
    c = connection.cursor()

    # get lists of unique values from sql database
    state = c.execute('''SELECT DISTINCT state_name FROM acs''').fetchall()
    county = c.execute('''SELECT DISTINCT county_name FROM acs''').fetchall()

    connection.close()


    ### Update for our files we want to generate

    # write lists of unique values to file
    f = open('state_list.csv', 'wb')
    w = csv.writer(f, delimiter="|")
    for row in state:
        w.writerow(row)
    f.close()

    f = open('county_list.csv', 'wb')
    w = csv.writer(f, delimiter="|")
    for row in county:
        w.writerow(row)
    f.close()

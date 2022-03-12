import sqlite3
import csv


def generate_lists():

    ###  Replace with name of our database
    connection = sqlite3.connect('../bubble_tables.db')
    c = connection.cursor()
    # print(c)

    # get lists of unique values from sql database
    state = c.execute('''SELECT DISTINCT state FROM elections''').fetchall()
    county = c.execute('''SELECT DISTINCT county FROM elections''').fetchall()
    
    connection.close()


    ### Update for our files we want to generate

    # write lists of unique values to file
    f = open('state_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for i, row in enumerate(state):
        if i!=0:
            w.writerow(row)
    f.close()

    f = open('county_list.csv', 'w')
    w = csv.writer(f, delimiter="|")
    for i, row in enumerate(county):
        if i!=0:
            w.writerow(row)
    f.close()

generate_lists()
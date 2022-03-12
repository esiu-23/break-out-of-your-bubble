# proj-bubble-trouble
# CS 122 Project team: Evelyn Siu, Cole von Glahn, Carolyn Vilter

Setup steps:

1. Set up a virtual environment with the necessary packages by running bubbletrouble/install.sh.

2. The shapefiles are too large to store on Github, so before running the application, download them from Box:
    - cd into the "bubbletrouble" directory.
    - Run "python3 shapefiles.py". Using "shapefiles.sh", it will automatically wget the necessary shapefiles from Box and place them in the "data" directory for you.
    - Wget seems to be less reliable on macs. If it has issues, the shapefiles can be found here: https://uchicago.box.com/s/davisunnxu751qs8plajhkmlj4jd5eby.
    - All other data files are saved on github - no setup necessary before running the application.

3. Start the application by running "python3 manage.py runserver" in the terminal inside the "bubbletrouble" directory and following the link to your browser.


Data notes:
- We have 3 sources of data: election data (supplied by a Harris professor), shapefiles (downloaded online), and demographic data (drawn from an API).
- The shapefiles must be downloaded to the user's directory before the application can be run - see step 2 above.
- The other files are ready to use. But for grading purposes:
    - The API component takes place in bubbletrouble/demographics.py using a package called CensusData. For your reference, running "python3 demographics.py" inside the "bubbletrouble" directory will re-pull the ACS and Census demographic data, clean it, and output it on top of the existing "acs_demos.csv" and "census_demos.csv" files already in the "data" directory.
    - Running "python3 elections.csv" inside the "bubbletrouble" directory will wget the election data from Box using "elections.sh", clean it, and output it on top of the existing "elections.csv" files already in the "data" directory.

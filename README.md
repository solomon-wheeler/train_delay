# train_delay 
# Description
This program uses the Historical Service performance API, provided by National Rail enquiries to get data on timetable services in between two Stations, and then gets data on the actual times these services have run at. It then outputs these to a html file, which opens in your browser.

# What do I need to get it working?
To use this program you need an account with National rail open data, which you can get from here www.opendata.nationalrail.co.uk
You then need to put your username/email and password into the program. You also need to have the following python libraries installed:
requests,
json,
sys,
webbrowser,
os,
plotly.express,
pandas.
You can get all of these using PIP.

# What does it actually do?
First the user inputs the stations, and times they would like services for, these are then sent to the HSP api, which returns services that match the data the user inputted, the user can then choose some of these services to get more infomation on, or you can get more infromation on all of them.
Each  individual service on a day has a unique identifier (called an "rid"), the program gets data on each individual service, and finds the actual time of departure from the first station and the actual time of arrival at the destination station. The program then uses this data to create all of the metrics, such as delay and percent delayed. It then turns this data into the html code for a table, and outputs this to a template file, which is then opened in the users browser.

#More Info
You can find more information as well as an example output on my website - https://solomon-wheeler.github.io/#progamming

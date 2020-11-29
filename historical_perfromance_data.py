# # You need these details to acesss the hsp API, you can get an account from here: www.opendata.nationalrail.co.uk. Username will be your email for this API
username = "solly.wheeler@gmail.com"  # todo store attiributes
password = ""
headers = {"Content-Type": "application/json"}  # todo create collection of objects

import requests
import json
import sys
import webbrowser
import \
    os
import plotly.express as plotly
import pandas
from requests.auth import \
    HTTPBasicAuth


# used to delete files made by the program once done
def cleanup(file_to_delete):
    os.remove(file_to_delete)


# This returns the average amount of services found for each schedule time before and the one currently being done
def average_for_rids(total_rids_list, total_services_current):
    services_done_before_total = 0
    number_of_services_before = 0
    for services_done_before in total_rids_list:
        services_done_before_total += services_done_before
        number_of_services_before += 1
    total_for_all_services = services_done_before_total + total_services_current
    return total_for_all_services / (number_of_services_before + 1)


# This creates the html code for the scatter plot of delays, using plotly express
def create_scatter(delays_data, scheduled_time):
    number_of_each_delay = [[this_one, delays_data.count(this_one)] for this_one in set(delays_data)]
    size = []  # Todo this is a bit of a bodge, could be made better?
    for x in number_of_each_delay:  # THis
        size.append(5)  # ANd his
    this_data = pandas.DataFrame(number_of_each_delay, columns=['Delay(Minutes)', 'Number of occurrences'])
    title = "Scatter plot of train delay occurunces for " + str(scheduled_time)
    print(title)
    fig = plotly.scatter(this_data, x="Delay(Minutes)", y="Number of occurrences", size=size,
                         title=title)
    html_for_this_service = fig.to_html(fig, full_html=False, include_plotlyjs="cdn", include_mathjax=False)
    html_for_this_service = [html_for_this_service]
    return html_for_this_service


# This allows for the user to search for stations using there actual name, and returns there CRS CODE
def to_crs(crs_code_in):
    if crs_code_in.isupper() is True and len(crs_code_in) == 3:  # this causes failure if crs code is not in caps??
        return crs_code_in
    low_crscodein = crs_code_in.lower()
    if low_crscodein == "reading":  # This is because reading always returns reading west, even when you don't put this in
        return "RDG"

    parameters_crs = {
        "station": low_crscodein}  ####this is not working because API has been depreacted, need to update to a new API :((
    url_crs = "https://api.departureboard.io/api/v2.0/getStationBasicInfo/"
    r = requests.get(url=url_crs, params=parameters_crs)
    print(r)
    crsdata = r.json()
    print(crsdata)
    try:
        return crsdata[0]['crsCode']
    except IndexError:
        return to_crs(str(input("There were no results found for that station name please try again, and check for "
                                "any typos.")))  # Recursion in case the user inputs invalid data


# This takes the average delay for a service and returns the colour
# todo make colours change based upon data
class website():
    def __init__(self):
        self.lines_to_add = []
        self.tag = "edit me"
        self.template_name = "table"
        self.output_name = "OPENME"
        self.files_made = []
    def line_to_HTML(self,schedule_time, average, operator, total_services, cancelled, average_desti,
                     journey_time,
                     percent_delayed_service):  # Could make this so that colour gradient is based on services, so really
        print(average)
        # unreilaible lines arent just all red, colour graident?
        colour_arival_delay = self.delay_colour(average)
        colour_destination_delay = self.delay_colour(average_desti)

        # todo make below into function?
        self.lines_to_add.append( '<tr><td> ' + str(schedule_time) + '</td><td bgcolor= ' + str(colour_arival_delay) + ' > ' + str(
            average) + '</td> <td> ' + str(operator) + '</td> <td> ' + str(total_services) + '</td><td>' + str(
            cancelled) + '</td><td bgcolor=' + str(colour_destination_delay) + '>' + str(
            average_desti) + '</td><td>' + str(journey_time) + '</td><td>' + str(
            percent_delayed_service) + '</td><td><a href = ' + str(
            services_to_examine) + '.html' + '> More info </a> </td></tr>')
    def delay_colour(self,average_delay):
        try:
            if average_delay <= 0:  # SHould be int vales from average or 0
                colour = "green"
            elif 1 <= average_delay < 3:
                colour = "#FFC300"
            elif 3 <= average_delay < 5:
                colour = "#FF5733"
            elif 5 <= average_delay <= 10:
                colour = "#C70039"
            else:
                colour = "#581845"
        except TypeError:
            colour = "#959292"
        return colour

    def add_to_file(self):
        with open((str(self.template_name) + ".html"), 'r') as file:
            data = file.readlines()
        position = 0
        for x in data:
            if str(self.tag) in x:  # Will find last one in file
                edit_start = int(position)
                break
            position += 1
        data[edit_start] = ""  # Get's rid of the edit me tag
        for x in self.lines_to_add:  # todo add thing here just incase the edit me tag isnt found
            data.insert(edit_start, (x + "\n"))
        with open((str(self.output_name) + ".html"), 'w') as file:
            file.writelines(data)
        self.files_made.append(str(self.output_name) + ".html")
    def open_website(self):
        print("Outputting this data to a file which is about to open, more information pages are still loading")
        webbrowser.open('file://' + os.path.realpath(
            "OPENME.html"))  # Use this so that it will still work when this project is moved to a different
        # computer, or to a differtn place on system
        print(
            "If the file didn't open, open the file named OPENME.html which has been created in the directory the "
            "python file is in, using a browser")
    def get_files_made(self):
        return self.files_made
# This function takes the scheduled time (should be one value) and a list of the actual times, it compares them and returns a list of how delayed each service was.
def delay(schedule_time, ThisTime):
    hours_schedule = int(schedule_time[:2])
    minutes = int(schedule_time[-2:])
    comb_schedule = (hours_schedule * 60) + minutes
    try:
        hours_actual = int(ThisTime[:2])
    except ValueError:
        delay = "X"
    else:
        minutes_actual = int(ThisTime[-2:])
        comb_actual = (hours_actual * 60) + minutes_actual
        delay = comb_actual - comb_schedule
        if delay < -720 and hours_schedule > hours_actual:  # This is incase the delay takes the time over the day marker, wont work if train is early by 12 hours, or if delayed by 19 hours
            comb_actual += 1440  # add all the hours from the day to the delay time
            delay = comb_actual - comb_schedule
            print(
                "THe code thinks that one of the delays took the train time over the date marker, if this didnt "
                "happen then there has been an error")
        elif delay < -720 and hours_actual > hours_schedule:  # This is incase the delay takes the time over the day marker, wont work if train is early by 12 hours, or if delayed by 19 hours
            comb_schedule += 1440  # add all the hours from the day to the delay time
            delay = comb_actual - comb_schedule
            print(
                "THe code thinks that one of the delays took the train time over the date marker, if this didnt "
                "happen then there has been an error")
    return delay




class Stations(): #todo need a new name for this class
    def __init__(self):
        self.payload = None
        self.data = None

    # Creates the payload to be sent to the HSP api

    def create_payload(self):  # Date = YYYY-MM-DD Time = HHMM

        start_time = str(input("The earliest time you would like services from, in the form HHMM e.g 0700"))
        end_time = str(input("The Latest time you would like services from, in the form HHMM e.g 0700"))
        start_date = "2020-01-01"  # todo add user input for these at some point, but for now dont want too much data to handle
        end_date = "2020-03-12"
        which_days = str(input("Would you like (W)eekdays, (SA)turday or (SU)nday?"))
        if which_days == "W":
            days = "WEEKDAY"
        elif which_days == "SA":
            days = "SATURDAY"
        else:  # Add something here in case they input the wrong value
            days = "SUNDAY"
        print(
            "Getting the data, this might take a while depending on the how long your time period is and how often trains are")
        payload = {"from_loc": start, "to_loc": destination, "from_time": start_time, "to_time": end_time,
                   "from_date": start_date, "to_date": end_date, "days": days}

        self.payload = json.dumps(payload)

    # Gets the data from the the api and saves it in self.data
    def source_data(self):
        url = "https://hsp-prod.rockshore.net/api/v1/serviceMetrics"
        self.data = requests.post(url, auth=HTTPBasicAuth(username, password),
                                  headers=headers, data=self.payload)
        print(self.data)
        self.data = json.loads(self.data.text)  # could change this to .json()?

    def get_json_data(self):
        return self.data

    def get_station_data(self):  # These aren't actually in this class but are in main which feels wrong.
        return self.start, self.destination


####not added to rewrite yet #####
    # Takes the data about what services are available and allows the user to choose which ones they want more detailed infromation on

   # def each_timetabeled_info(self, services_to_examine):
#
#
 #       # todo beneath should have it's own function within website class
        self.files_made.append(add_to_file(self.add_line, "edit me", "table", "OPENME"))
  #      print("Outputting this data to a file which is about to open, more information pages are still loading")
   #     webbrowser.open('file://' + os.path.realpath(
        #    "OPENME.html"))  # Use this so that it will still work when this project is moved to a different
    #    # computer, or to a differtn place on system
     #   print(
       #     "If the file didn't open, open the file named OPENME.html which has been created in the directory the "
      #      "python file is in, using a browser")
       # x = 0
        #for currently_adding in services_to_examine:  # Goes through each service the user has selected and creates then saves the scatter chart for that
         #   delay_for_currently_adding = self.all_delays[x]
          #  this_div = create_scatter(delay_for_currently_adding, self.times[int(currently_adding)])
           # self.files_made.append(add_to_file(this_div, "edit me", "more_data_template", currently_adding))
           # amount_done += 1
           # x += 1
       # print("More information pages have all loaded")



class overall_service():
    def __init__(self, this_service_id, this_start_time, this_end_time, number_found, rids_found, this_operator):
        self.individaul_id = this_service_id
        self.start_time = this_start_time
        self.desti_time = this_end_time
        self.num_rids = number_found
        self.individual_rid_list = rids_found
        self.operator = this_operator
        self.individual_services = []
        self.journey_time = delay(this_start_time, this_end_time)
        self.average_delay_value_start = None
        self.average_delay_value_end =None
        self.amount_cancelled = None
        self.percent_delayed = None

    def get_start_time(self):
        return self.start_time

    def get_individual_id(self):
        return self.individaul_id
    def get_summary(self):
        return (self.start_time, self.average_delay_value_start, self.operator, self.num_rids, self.amount_cancelled, self.average_delay_value_end,self.journey_time, self.percent_delayed)

    def add_individual_services_skeleton(self):
        for this_indi_train in self.individual_rid_list:
            self.individual_services.append(individual_service(this_indi_train))

    def add_indi_service_data(self):
        StartDelays =[]
        EndDelays = []
        for this_indi_train in self.individual_services:
            this_indi_train.format_data()
            this_indi_train.delays(self.start_time, self.desti_time)
            delay_info = this_indi_train.get_delays()
            StartDelays.append(delay_info[0])
            EndDelays.append(delay_info[1])
        start_delay_cancelled = self.average_delay(StartDelays)
        self.average_delay_value_start = start_delay_cancelled[0]
        self.amount_cancelled = start_delay_cancelled[1]
        self.percent_delayed = start_delay_cancelled[2]
        self.average_delay_value_end = self.average_delay(EndDelays)[0]

    def average_delay(self,all_delays):  # this takes a list of each delay and works out the average, not including days where the train was cancelled
        total = 0
        sample_size = 0
        cancelled = 0
        total_industry_delayed = 0 #todo allow user to set value for this??
        for this_delay in all_delays:
            if this_delay != "X":
                total += this_delay
                if int(this_delay) >= tolerance or int(this_delay) <= (tolerance * -1):
                    total_industry_delayed += 1
            else:
                cancelled += 1

            sample_size += 1
        try:
            this_average_delay_value = int(total / sample_size)
        except ZeroDivisionError:
            print("We have no data for this service in the time period you selected")
            this_average_delay_value = "No data"
        try:
            cancelled = int((cancelled / (sample_size + cancelled)) * 100)
        except ZeroDivisionError:
            cancelled = "no data"
        try:
            percent_delayed = int((total_industry_delayed / (sample_size)) * 100)
        except ZeroDivisionError:
            cancelled = "no data"
        return(this_average_delay_value,cancelled,percent_delayed)

class individual_service():
    def __init__(self, this_rid):
        self.rid = this_rid
        self.data = json.loads((requests.post("https://hsp-prod.rockshore.net/api/v1/serviceDetails",
                                              auth=HTTPBasicAuth(username, password),
                                              headers=headers,
                                              data=json.dumps({"rid": this_rid})).text))
        self.start_actual_time = None
        self.destination_time = None
        self.delay_at_start = None
        self.delay_at_desti = None

    def format_data(self):
        for stop in self.data['serviceAttributesDetails']['locations']:
            location = stop['location']
            if start in location:
                self.actual_time = stop['actual_td']  # Add date here to make it more pretty when being outputted
            elif destination in location:
                self.destination_time = stop['actual_ta']

    def delays(self, start_time, end_time):
        self.delay_at_start = delay(start_time, self.actual_time)
        self.delay_at_desti = delay(end_time, self.destination_time)
    def get_delays(self):
        return(self.delay_at_start,self.delay_at_desti)


### main
print("This service is Powered By national rail enquiries, more info can be found at www.nationalrail.co.uk")
start = to_crs(str(input("Name or CRS code of start station")))
destination = to_crs(str(input("Name or CRS code of the destination station")))

first_station = Stations()
first_station.create_payload()  # This is creating the payload to be sent to the API, taking basic information from the user and using this to create the payload
first_station.source_data()  # This queires the api for the overview data (info on number of jounries found at certain times, but not delay info for each individaul service
first_station.get_json_data()
html_output = website()
##intitalising variables##
tolerance = 1
invalid_times = []
services_found = 0
###

all_services = []
invalid_service_ids = []
for x in first_station.get_json_data()[
    'Services']:  # split into two one creating list, one letting the user choose information
    num_rids = int((x['serviceAttributesMetrics']['matched_services']))
    if num_rids < 2:
        invalid_service_ids.append(services_found)
        invalid_times.append(x['serviceAttributesMetrics']['gbtt_ptd'])
    else:
        ##   self.time_to_overall.append(services_found)   havent added this in becasuse im not sure what it does
        all_services.append(overall_service(services_found, x['serviceAttributesMetrics']['gbtt_ptd'], x['serviceAttributesMetrics']['gbtt_pta'], num_rids, x['serviceAttributesMetrics']['rids'], x['serviceAttributesMetrics']['toc_code']))
        services_found += 1

if len(invalid_service_ids) != 0:
    print("The following times were skipped because there wasn't enough data on them: ", invalid_times)
print("Which service would you like the data on?")
for this_service in all_services:
    print(this_service.get_individual_id(), this_service.get_start_time())
service_choice = str(
    input(
        "Input a single number for info on just that, numbers with commas in between them for multiple "
        "services or input ALL for information on all of them"))
services_to_examine = []
if service_choice != "ALL":
    services_chosen = service_choice.split(",")
    for all_services_found in all_services:
        if str(all_services_found.get_individual_id()) not in services_chosen:
            all_services.pop(
                all_services_found.get_individual_id())  # todo not sure if clases are gertting deleted here so might need to deleete them first to make it more memory efficent
for x in all_services:
    x.add_individual_services_skeleton()
    x.add_indi_service_data()
    html_output.line_to_HTML(x.get_summary()[0],x.get_summary()[1],x.get_summary()[2],x.get_summary()[3],x.get_summary()[4],x.get_summary()[5],x.get_summary()[6],x.get_summary()[7])
html_output.add_to_file()
html_output.open_website()
input(
    "The program will delete the files it has made (except templates) once you're done, just input anything and the "
    "program will delete the files then stop")
for currently_deleting in html_output.get_files_made():
    cleanup(currently_deleting)
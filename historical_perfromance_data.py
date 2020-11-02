# # You need these details to acesss the hsp API, you can get an account from here: www.opendata.nationalrail.co.uk. Username will be your email for this API
username = "solly.wheeler@gmail.com"
password = ""
headers = {"Content-Type": "application/json"}

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
    if crs_code_in.isupper() is True and len(crs_code_in) == 3:
        return crs_code_in
    low_crscodein = crs_code_in.lower()
    if low_crscodein == "reading":  # This is because reading always returns reading west, even when you don't put this in
        return "RDG"

    parameters_crs = {"station": low_crscodein}
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
def delay_colour(average_delay):
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


# Takes all the data for a scheduled time and turns it into html that can be added to the overall file
def line_to_HTML(schedule_time, average, operator, total_services, cancelled, average_desti,
                 journey_time,
                 percent_delayed_service,
                 services_to_examine):  # Could make this so that colour gradient is based on services, so really
    # unreilaible lines arent just all red, colour graident?
    colour_arival_delay = delay_colour(average)
    colour_destination_delay = delay_colour(average_desti)

    # todo make below into function?
    return '<tr><td> ' + str(schedule_time) + '</td><td bgcolor= ' + str(colour_arival_delay) + ' > ' + str(
        average) + '</td> <td> ' + str(operator) + '</td> <td> ' + str(total_services) + '</td><td>' + str(
        cancelled) + '</td><td bgcolor=' + str(colour_destination_delay) + '>' + str(
        average_desti) + '</td><td>' + str(journey_time) + '</td><td>' + str(
        percent_delayed_service) + '</td><td><a href = ' + str(
        services_to_examine) + '.html' + '> More info </a> </td></tr>'


# This function takes the scheduled time (should be one value) and a list of the actual times, it compares them and returns a list of how delayed each service was.
def delay(schedule_time, actual_times):
    hours_schedule = int(schedule_time[:2])
    minutes = int(schedule_time[-2:])
    comb_schedule = (hours_schedule * 60) + minutes
    delays = []
    for ThisTime in actual_times:
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
        delays.append(delay)
    return delays


def average_delay(
        delays):  # this takes a list of each delay and works out the average, not including days where the train was cancelled
    total = 0
    sample_size = 0
    cancelled = 0
    for ThisDelay in delays:
        if ThisDelay != "X":
            total += ThisDelay
        else:
            cancelled += 1
        sample_size += 1

    try:
        average_delay_value = int(total / sample_size)
    except ZeroDivisionError:
        print("We have no data for this service in the time period you selected")
        average_delay_value = "No data"
    try:
        cancelled = int((cancelled / (sample_size + cancelled)) * 100)
    except ZeroDivisionError:
        cancelled = "no data"
    return average_delay_value, cancelled


# Any train not arriving within 1 minute of its scheduled time is now counted as delayed, shows data for this
# todo  change it so the user can say what they define as late and store this in a user classs
def percent_delayed(delays):
    sample_size = 0
    total_industry_delayed = 0
    for ThisDelay in delays:
        if ThisDelay != "X":
            if ThisDelay >= 1 or ThisDelay <= -1:
                total_industry_delayed += 1
        sample_size += 1
    if sample_size != 0:
        return int((total_industry_delayed / sample_size) * 100)
    else:
        return "no Data"


# This takes all of the html lines created and adds them to the template file, before saving this as the output file
def add_to_file(lines_to_add, tag, template_name, output_name):
    with open((str(template_name) + ".html"), 'r') as file:
        data = file.readlines()
    position = 0
    for x in data:
        if str(tag) in x:  # Will find last one in file
            edit_start = int(position)
            break
        position += 1
    data[edit_start] = ""  # Get's rid of the edit me tag
    for x in lines_to_add:  # todo add thing here just incase the edit me tag isnt found
        data.insert(edit_start, (x + "\n"))
    with open((str(output_name) + ".html"), 'w') as file:
        file.writelines(data)
    return str(output_name) + ".html"


class Stations():
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
        self.data = json.loads(self.data.text)

    def get_json_data(self):
        return self.data

    def get_station_data(self):
        return self.start, self.destination


class Timetable():  # todo need a new class for actual train data within this class and make the relationship between choose_service and get detilated information less reliant on overall class
    def __init__(self, input_data):
        self.data = input_data  # Not sure whether parsing the value in is the correect way to do this or wether I should use inheritance todo
        self.add_line = []
        self.all_delays = []
        self.files_made = []
        self.times = []
        self.arrival_times = []
        self.time_to_overall = []

    # Takes the data about what services are available and allows the user to choose which ones they want more detailed infromation on
    def choose_service(
            self):
        invalid_times = []
        valid_services = 0
        services_found = 0
        for x in self.data['Services']:
            num_rids = len(x['serviceAttributesMetrics']['rids'])
            if num_rids == 1:
                invalid_times.append(x['serviceAttributesMetrics']['gbtt_ptd'])
            else:
                self.times.append(x['serviceAttributesMetrics']['gbtt_ptd'])
                self.time_to_overall.append(services_found)
                self.arrival_times.append(x['serviceAttributesMetrics']['gbtt_pta'])
                valid_services += 1
            services_found += 1

        if len(invalid_times) != 0:
            print("The following times were skipped because there wasn't enough data on them: ", invalid_times)
        print("Which service would you like the data on?")
        for services_done in range(len(self.times)):
            print(services_done, self.times[services_done])

        service_choice = str(
            input(
                "Input a single number for info on just that, numbers with commas in between them for mutiple "
                "services or input ALL for information on all of them"))
        services_to_examine = []
        if service_choice == "ALL":
            for services_to_add in range(len(self.times)):
                services_to_examine.append(services_to_add)
        else:
            services_to_examine = service_choice.split(",")
        self.each_timetabeled_info(services_to_examine)

    def each_timetabeled_info(self, services_to_examine):
        total_number_of_services = len(services_to_examine)
        done_services = 0
        total_rids_list = []
        for currently_examining in services_to_examine:  # Goes through each service the user has selected
            schedule_time = self.times[int(currently_examining)]
            arrival_time = self.arrival_times[int(currently_examining)]
            overall_examine = self.time_to_overall[int(
                currently_examining)]  # the overall data includes all of the services, including ones that haven't
            # been presented to the user due to lack of data so this changes the value to the overall value,
            # including all servoces
            rids = self.data['Services'][int(overall_examine)]['serviceAttributesMetrics']['rids']
            operator = self.data['Services'][int(overall_examine)]['serviceAttributesMetrics']['toc_code']
            data_for_percent = self.each_individaul_service_info(rids, schedule_time, operator, arrival_time,
                                                                 total_number_of_services, done_services,
                                                                 total_rids_list,
                                                                 currently_examining)
            done_services += data_for_percent[0]
            total_rids_list.append(data_for_percent[1])
        amount_done = 0

        # todo beneath should have it's own function within website class
        self.files_made.append(add_to_file(self.add_line, "edit me", "table", "OPENME"))
        print("Outputting this data to a file which is about to open, more information pages are still loading")
        webbrowser.open('file://' + os.path.realpath(
            "OPENME.html"))  # Use this so that it will still work when this project is moved to a different
        # computer, or to a differtn place on system
        print(
            "If the file didn't open, open the file named OPENME.html which has been created in the directory the "
            "python file is in, using a browser")
        x = 0
        for currently_adding in services_to_examine:  # Goes through each service the user has selected and creates then saves the scatter chart for that
            delay_for_currently_adding = self.all_delays[x]
            this_div = create_scatter(delay_for_currently_adding, self.times[int(currently_adding)])
            self.files_made.append(add_to_file(this_div, "edit me", "more_data_template", currently_adding))
            amount_done += 1
            x += 1
        print("More information pages have all loaded")

    # Gets more detailed informaiton on each rid(primary key for a service on a specific day)
    #todo splits this into mutiple fucntions and add classes
    def each_individaul_service_info(self, rids, schedule_time, operator, arrival_time, total_number_of_services,
                                     done_services,
                                     total_rids_list
                                     , currently_examining):
        actual_times = []
        destination_times = []
        total_services_current = len(rids)
        average = average_for_rids(total_rids_list, total_services_current)
        new_services = 0
        for x in rids:
            new_services += 1
            percent_done = int(((done_services + new_services) / (average * total_number_of_services) * 100))
            sys.stdout.write('\r')
            sys.stdout.write(str(percent_done) + "%" + "   ")
            sys.stdout.flush()
            url = "https://hsp-prod.rockshore.net/api/v1/serviceDetails"
            payload = json.dumps({"rid": x})  # Might no work, may need to have seperate value? We'll see
            data = requests.post(url, auth=HTTPBasicAuth(username, password),
                                 headers=headers,
                                 data=payload)
            data = json.loads(data.text)
            # print(json.dumps(data,indent=5, sort_keys=True))
            for stop in data['serviceAttributesDetails']['locations']:
                location = stop['location']
                if start in location:
                    actual_times.append(stop['actual_td'])  # Add date here to make it more pretty when being outputted
                elif destination in location:
                    destination_times.append(
                        stop['actual_ta'])  # Use time of arrival not depature for end stop
        # Below turns all of the raw data into more user friendly data, then saves the html table of this data
        destination_time = [arrival_time]
        journey_time = delay(schedule_time, destination_time)
        delays = delay(schedule_time, actual_times)
        desti_delays = delay(arrival_time, destination_times)
        self.all_delays.append(delays)
        print(delays)
        print(schedule_time)
        percent_delayed_service = percent_delayed(delays)
        average_and_cancelled = average_delay(delays)  # for start
        average = average_and_cancelled[0]
        cancelled = average_and_cancelled[1]
        average_and_cancelled_desti = average_delay(desti_delays)  # For destination
        average_desti = average_and_cancelled_desti[0]
        self.add_line.append(
            line_to_HTML(schedule_time, average, operator, total_services_current, cancelled, average_desti,
                         journey_time, percent_delayed_service, currently_examining))
        return new_services, total_services_current


# main
print("This service is Powered By national rail enquiries, more info can be found at www.nationalrail.co.uk")
start = to_crs(str(input("Name or CRS code of start station")))
destination = to_crs(str(input("Name or CRS code of the destination station")))  # THinks this is done twice if thers an error
first_station = Stations()
first_station.create_payload() #This is creating the payload to be sent to the API, taking basic information from the user and using this to create the payload
first_station.source_data() #This queires the api for the overview data (ifo on number of jounries found at certain times, but not delay info for each individaul service
timetable_for_journey = Timetable(first_station.get_json_data())
timetable_for_journey.choose_service() #This allows the user to choose the services they want and then gets more detialed information on these
input(
    "The program will delete the files it has made (except templates) once you're done, just input anything and the "
    "program will delete the files then stop")
for currently_deleting in timetable_for_journey.files_made:
    cleanup(currently_deleting)

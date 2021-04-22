headers = {"Content-Type": "application/json"}
from scipy import stats
import requests
import json
import sys
import webbrowser
import os
from pandas import DataFrame
import plotly.express as plotly
from requests.auth import \
    HTTPBasicAuth


def explain_error(code):
    if "403" in code:
        input(
            "The Username and Password inputted where not correct, check the crednetials file has only the username and password after the =, and that you have permission to use the api with your acccount, then input anything once youve fixed it")
    elif "400" in code:
        input(
            "One of the input parameters was no in the correct format, please run the program again and make sure all inputs are only alphanurmerial characters and are valid for your jounrye")
        exit()
    elif "429" in code:
        input(
            "You have been rate limited because you've made too many requests to the api, please wait before trying again")
    elif "503" in code or "500" in code:
        print("Unfortunately there is a problem with the api at the moment, please try again later")
        exit()


# # You need these details to acesss the hsp API, you can get an account from here: www.opendata.nationalrail.co.uk. Username will be your email for this API
def get_api_credentials():
    credentials_file = open("credentials.txt", "r")  # opens file with credentials in
    credentials = []
    for this_line in credentials_file:
        credentials.append((this_line.strip()).split("=")[1])
    if len(credentials) != 2:
        input(
            "THere has been an erorr in the credentials file, please make sure it is in the correct format with nothin except the useraname password after the =, then press anything to continue")
        return get_api_credentials()  # THis will run the program again allowing the user to check the file is correct??
    return credentials[0], credentials[1]


# used to sort a list of values most efficent from tested of merge and heap sort for train times
def quicksort(
        list_to_sort):  # this could be made more efficent by using median train delay across uk instead of just getting the last value
    different = False  # see below for use of this variable at "different == false"
    length = len(list_to_sort)
    if length < 2:  # If length is less than 1 then there are either no values in the list or 1, so no further anaylsis is needed
        return list_to_sort
    lower_list = []
    higher_list = []
    pivot = list_to_sort.pop()  # This get's the last element from the list, to be used as a pivot. this was tested with median of first, mid, last. But last is more efficent on average.
    try:
        pivot = int(pivot)
    except:
        pivot = list_to_sort.pop()

    y = 0
    for this_value in list_to_sort:
        try:
            this_value = int(this_value)
        except:
            list_to_sort.pop(y)
            y += 1
        else:
            if int(this_value) > int(pivot):
                higher_list.append(this_value)
                different = True
            elif this_value == pivot:
                lower_list.append(this_value)
            else:
                lower_list.append(this_value)
                different = True
            y += 1
    if not different:  # This is included because reliable trains will have many low numbers, this means we don't have to recursively go through all and can just return the list of all the same number
        return list_to_sort + [pivot]
    return_val = quicksort(lower_list) + [pivot] + quicksort(higher_list)
    return return_val


# used to delete files made by the program once done
def cleanup(file_to_delete):
    os.remove(file_to_delete)


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


# This allows for the user to search for stations using there actual name, and returns there CRS CODE(which is the a 3 letter unique identifier for each station)
def to_crs(crs_code_in):
    if crs_code_in.isupper() is True and len(crs_code_in) == 3:
        return crs_code_in
    low_crscodein = crs_code_in.lower()
    crs_data = open("NR_media/station_codes.csv", "r")
    options = []
    for line in crs_data:  # cannot use a binary search here because list is ordeered, but user might search for "Waterloo" instead of London Waterloo etc, so just checking by letter's is not possible
        line = line.split(",")
        if low_crscodein in line[0].lower():
            options.append([line[0], line[1].strip()])
    if len(options) == 0:
        print("That station could not be found")
        return to_crs(str(input(
            "Please input the station name again")))  # recursion to allow for the user to input the station name again
    if len(options) == 1:
        return options[0][1]
    num_through = 0
    print("The stations found where:")
    for each_found_station in options:
        print(str(num_through) + " : " + each_found_station[0])
        num_through += 1
    choice = int(input("Please input the number of the correct station"))
    return options[choice][1]


class website():
    def __init__(self, tag, template_name, output_name, ):
        self.lines_to_add = []
        self.tag = tag
        self.template_name = template_name
        self.output_name = output_name
        self.files_made = []

    # takes all of the service metrics found and turns them into a line of a table that can be added to a html file
    def line_to_HTML(self, schedule_time, average, operator, total_services, cancelled, average_desti,
                     journey_time,
                     percent_delayed_service,
                     service_id, percent_within_allowed_time):
        colour_arival_delay = self.delay_colour(average)
        colour_destination_delay = self.delay_colour(average_desti)
        self.lines_to_add.append(
            '<tr><td> ' + str(schedule_time) + '</td><td bgcolor= ' + str(colour_arival_delay) + ' > ' + str(
                average) + '</td> <td> ' + str(operator) + '</td> <td> ' + str(total_services) + '</td><td>' + str(
                cancelled) + '</td><td bgcolor=' + str(colour_destination_delay) + '>' + str(
                average_desti) + '</td><td>' + str(journey_time) + '</td><td>' + str(
                percent_delayed_service) + '</td><td><a href = ' + str(
                service_id) + '.html' + '> More info </a> </td><td>' + str(
                100 - int(percent_within_allowed_time)) + '</td></tr>')  # int here makes the percentage more readable

    def set_line(self, line_to_add):
        self.lines_to_add.append(line_to_add)

    def delay_colour(self, average_delay):  # returns the colour that the delay value in the table will be
        try:
            if average_delay <= 0:
                colour = "#008000"
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

    def add_to_file(self): #adds the lines in self.linse to add to the html file that will be opened for the user
        with open(("Templates/" + (self.template_name) + ".html"), 'r') as file:
            data = file.readlines()
        position = 0
        found = False
        for x in data:
            if str(self.tag) in x:  # Will find last one in file
                edit_start = int(position)
                found = True
                break
            position += 1
        if found == False:
            print("ERRORR: Tag wasn't found in the file, this may mean the file was corrupted or edited.")
            edit_start = 1
        data[edit_start] = ""  # Get's rid of the edit me tag
        for x in self.lines_to_add:
            data.insert(edit_start, (str(x) + "\n"))
        with open((str(self.output_name) + ".html"), 'w') as file:
            file.writelines(data)
        self.files_made.append(str(self.output_name) + ".html")

    def open_website(self):
        print("Outputting this data to a file which is about to open, more information pages are still loading")
        webbrowser.open('file://' + os.path.realpath(
            "OPENME.html"))  # Use this so that it will still work when this project is moved to a different
        # computer, or to a different place on system
        print(
            "If the file didn't open, open the file named OPENME.html which has been created in the directory the "
            "python file is in, using a browser")

    def get_files_made(self):
        return self.files_made


class Journey_Info:
    def __init__(self):
        self.payload = None
        self.data = None

    # Creates the payload to be sent to the HSP api
    def create_payload(self):  # Date = YYYY-MM-DD Time = HHMM

        start_time = str(input("The earliest time you would like services from, in the form HHMM e.g 0700"))
        end_time = str(input("The Latest time you would like services from, in the form HHMM e.g 0700"))
        start_date = str(input("Please input the earliest data you want services on, in the form YYYY-MM-D e.g 2020-04-12"))
        end_date = int(input("Please input the earliest data you want services on, in the form YYYY-MM-D e.g 2020-04-12"))
        which_days = str(input("Would you like (W)eekdays, (SA)turday or (SU)nday?"))
        if which_days == "W":
            days = "WEEKDAY"
        elif which_days == "SA":
            days = "SATURDAY"
        else:
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
        if "200" not in str(self.data.status_code):
            print("There has been an error with that request")
            explain_error(str(self.data.status_code))
            self.source_data()
        self.data = json.loads(self.data.text)

    def get_json_data(self):
        return self.data


class service(): #parent class for services
    def __init__(self, this_start_time, this_end_time):
        self.start_time = this_start_time
        self.destination_time = this_end_time

class overall_service(service): #service child class, stores data on an overall service, e.g the 7:30 to waterloo
    def __init__(self, this_service_id, this_start_time, this_end_time, number_found, rids_found, this_operator,
                 acceptable_connection_time):
        service.__init__(self, this_start_time, this_end_time)

        self.individual_id = this_service_id
        self.num_rids = number_found
        self.individual_rid_list = rids_found
        self.operator = this_operator
        self.individual_services = []
        self.journey_time = delay(this_start_time, this_end_time)
        self.average_delay_value_start = None
        self.average_delay_value_end = None
        self.amount_cancelled = None
        self.percent_delayed = None
        self.start_delays = []
        self.end_delays = []
        self.connection_time = acceptable_connection_time

    def get_start_time(self):
        return self.start_time

    def get_individual_id(self):
        return self.individual_id

    def get_summary(self):
        return (self.start_time, self.average_delay_value_start, self.operator, self.num_rids, self.amount_cancelled,
                self.average_delay_value_end, self.journey_time, self.percent_delayed, self.individual_id,
                self.predict_destination_connection())

    def add_individual_services_skeleton(self): #add's the classes for each individaul service, e.g the 7:30 to Waterllo on 22/04/2021, as well as querying the api within the classes constructor
        amount_done = 1
        for this_indi_train in self.individual_rid_list:
            self.individual_services.append(individual_service(this_indi_train))
            sys.stdout.write('\r')
            sys.stdout.write(str(int((amount_done / self.num_rids) * 100)) + "%")  #used to show how far we are through the data collection procces, because this can take a while on slower networks.
            amount_done += 1
        sys.stdout.write('\r')

    def add_indi_service_data(self): #takes the raw service data and formats it then adds to the class
        for this_indi_train in self.individual_services:
            this_indi_train.format_data() #takes the raw data and formats it to be added to the class
            this_indi_train.delays(self.start_time, self.destination_time)
            delay_info = this_indi_train.get_delays()
            self.start_delays.append(delay_info[0])
            self.end_delays.append(delay_info[1])

    def add_overall_delay_data(self):  #works out the delay data for the trains
        start_delay_cancelled = self.average_delay(self.start_delays)
        self.average_delay_value_start = start_delay_cancelled[0]
        self.amount_cancelled = start_delay_cancelled[1]
        self.percent_delayed = start_delay_cancelled[2]
        self.average_delay_value_end = self.average_delay(self.end_delays)[0]

    def average_delay(self,
                      all_delays):  # This takes a list of each delay and works out the average, not including days where the train was cancelled
        total = 0
        sample_size = 0
        cancelled = 0
        total_industry_delayed = 0
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
        return (this_average_delay_value, cancelled, percent_delayed)

    def create_scatter(self): #this creates a scatter plot from the delay data using plotly
        number_of_each_delay = [[this_one, self.start_delays.count(this_one)] for this_one in set(self.start_delays)]
        size = [5 for i in range(len(number_of_each_delay))]
        this_data = DataFrame(number_of_each_delay, columns=['Delay(Minutes)', 'Number of occurrences'])
        title = "Scatter plot of train delay occurrences for " + str(self.start_time)
        fig = plotly.scatter(this_data, x="Delay(Minutes)", y="Number of occurrences", size=size,
                             title=title)
        html_for_this_service = fig.to_html(fig, full_html=False, include_plotlyjs="cdn", include_mathjax=False)
        # html_for_this_service = [html_for_this_service]
        return html_for_this_service

    def get_percentage_later(self,
                             sorted_list):  # this function takes a sorted list and returns for each value, or group of equal values, the percentage of trains that where **more** delayed than this value.
        time_vals = []
        percentage_afters = []
        length = len(sorted_list)
        for i in range(0, length):
            if i == (length - 1) or sorted_list[i] != sorted_list[i + 1]:
                this_num_percentage_after = ((length - (i + 1)) / length) * 100
                time_vals.append(sorted_list[i])
                percentage_afters.append(this_num_percentage_after)
        return time_vals, percentage_afters

    def predict_destination_connection(
            self):  #predicts the likelihood of your train arriving within the time to make your connection using linear regression from scipy
        sorted_values = quicksort(self.end_delays)
        time_values, percent_later = self.get_percentage_later(sorted_values)
        gradient, y_intercept, fit_value, p, std_err = stats.linregress(time_values, percent_later)
        y = 0
        for x in percent_later:  # He were checking if there is any imperical data, if so we use this because it will be more accurate than linear regression
            y += 1
            if time_values[0] == self.connection_time:
                predicted_chance = percent_later[y]
        else:  # None of the trains in the data set where actually this delayed, so we use linear regression to 'predit' a value
            predicted_chance = gradient * self.connection_time + y_intercept
        if fit_value < 0:
            fit_value = fit_value * - 1  # Doing |val| here to make sure it's always positive. For most of our data set's it will be negative.
        return predicted_chance + fit_value


class individual_service(service):
    def __init__(self, this_rid):
        self.rid = this_rid
        self.data = json.loads((requests.post("https://hsp-prod.rockshore.net/api/v1/serviceDetails",
                                              auth=HTTPBasicAuth(username, password),
                                              headers=headers,
                                              data=json.dumps({"rid": this_rid})).text))
        service.__init__(self, None, None)  # creating variables for actual start and destination time for this service
        self.delay_at_start = None
        self.delay_at_destination = None

    def format_data(self):
        for stop in self.data['serviceAttributesDetails']['locations']:
            location = stop['location']
            if start in location:
                self.actual_time = stop['actual_td']
            elif destination in location:
                self.destination_time = stop['actual_ta']

    def delays(self, start_time, end_time): #works out delay data
        self.delay_at_start = delay(start_time, self.actual_time)
        self.delay_at_destination = delay(end_time, self.destination_time)

    def get_delays(self):
        return (self.delay_at_start, self.delay_at_destination)


### main
username, password = get_api_credentials()

print("This service is Powered By national rail enquiries, more info can be found at www.nationalrail.co.uk")
start = to_crs(str(input("Name or CRS code of start station")))
destination = to_crs(str(input("Name or CRS code of the destination station")))
acceptable_connection_time = int(input(
    "What is the maximum time allowed for your connection (in minutes)"))

This_Journey = Journey_Info()
This_Journey.create_payload()  # This is creating the payload to be sent to the API, taking basic information from the user and using this to create the payload
This_Journey.source_data()  # This queries the api for the overview data (info on number of jounries found at certain times, but not delay info for each individaul service
overall_output = website("edit me", "table", "OPENME")

##intitalising variables##
tolerance = 1
invalid_times = []
services_found = 0
all_services = []
invalid_service_ids = []


for x in This_Journey.get_json_data()[
    'Services']:  # split into two one creating list, one letting the user choose information
    num_rids = int((x['serviceAttributesMetrics']['matched_services']))
    if num_rids < 2:
        invalid_service_ids.append(services_found)
        invalid_times.append(x['serviceAttributesMetrics']['gbtt_ptd'])
    else:
        all_services.append(overall_service(services_found, x['serviceAttributesMetrics']['gbtt_ptd'],
                                            x['serviceAttributesMetrics']['gbtt_pta'], num_rids,
                                            x['serviceAttributesMetrics']['rids'],
                                            x['serviceAttributesMetrics']['toc_code'], acceptable_connection_time))
        services_found += 1

if len(invalid_service_ids) != 0:
    print("The following times were skipped because there wasn't enough data on them: ", invalid_times)

print("Which service would you like the data on?")
for this_service in all_services:
    print(this_service.get_individual_id(), this_service.get_start_time())
service_choice = str(input("Input a single number for info on just that, numbers with commas in between them for "
                           "multiple services or input ALL for information on all of them"))

ids_to_be_removed = []
if service_choice != "ALL": #removes services from the list that the user has not chosen
    popped = 0
    services_chosen = service_choice.split(",")
    for all_services_found in all_services:

        if str(all_services_found.get_individual_id()) not in services_chosen:
            ids_to_be_removed.append(all_services_found.get_individual_id())
    ids_to_be_removed.reverse()  # has to be reversed so that popping items dosen't intefer with the position of other items
    for this_index in ids_to_be_removed:
        all_services.pop(this_index)

for x in all_services: #goes through each of the services the user has chosen and gets information on them
    print("Getting Data on Service" + str(x.get_individual_id()))
    x.add_individual_services_skeleton()
    x.add_indi_service_data()
    x.add_overall_delay_data()
    this_data = x.get_summary()
    overall_output.line_to_HTML(this_data[0], this_data[1], this_data[2], this_data[3], this_data[4], this_data[5],
                                this_data[6], this_data[7], this_data[8], this_data[9])
sys.stdout.flush() #this gets rid of the percentage information being shown when getting data on services
overall_output.add_to_file()
overall_output.open_website()
more_info_pages = []
print("TaDa, it should be done! If the page hasn't opened navigate to the directory this folder is in and open" + str(
    overall_output.get_files_made()) + "The program will now work on the more data sections")
for x in all_services:
    this_more_detail_page = website("edit me", "more_data_template", x.get_individual_id())
    more_info_pages.append(this_more_detail_page)
    this_more_detail_page.set_line(x.create_scatter())
    this_more_detail_page.add_to_file()

input(
    "The program will delete the files it has made (except templates) once you're done, just input anything and the "
    "program will delete the files then stop")

#below deletes files that have been created
for currently_deleting in overall_output.get_files_made():
    cleanup(currently_deleting)
for x in more_info_pages:
    cleanup((x.get_files_made()[0]))

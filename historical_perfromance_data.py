# # You need these details to acesss the hsp API, you can get an account from here: www.opendata.nationalrail.co.uk. Username will be your email for this API
from pandas import DataFrame

headers = {"Content-Type": "application/json"}  # todo move to class atribute

import requests
import json
import sys
import webbrowser
import \
    os
import pandas
import plotly.express as plotly
from requests.auth import \
    HTTPBasicAuth

def explain_error(code):
    if "403" in code:
        input("The Username and Password inputted where not correct, check the crednetials file has only the username and password after the =, and that you have permission to use the api with your acccount, then input anything once youve fixed it")
    elif "400" in code: #this probably could be more helpful
        input("One of the input parameters was no in the correct format, please run the program again and make sure all inputs are only alphanurmerial characters and are valid for your jounrye")
        exit()
    elif "429" in code:
        input("You have been rate limited because you've made too many requests to the api, please wait before trying again")
    elif "503" in code or "500" in code:
        print("Unfortunately there is a problem with the api at the moment, please try again later")
        exit()


def get_api_credentials():
    credentials_file = open("credentials.txt", "r")
    credentials = []
    for this_line in credentials_file:
        credentials.append((this_line.strip()).split("=")[1])
    if len(credentials) != 2:
        input(
            "THere has been an erorr in the credentials file, please make sure it is in the correct format with nothin except the useraname password after the =, then press anything to continue" )  # todo make this slightly more specific to explain why eeror has occured
        return get_api_credentials()   #Is this recusion helpful??
    return credentials[0],credentials[1]


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

# This allows for the user to search for stations using there actual name, and returns there CRS CODE
def to_crs(crs_code_in):
    if crs_code_in.isupper() is True and len(crs_code_in) == 3:  # this causes failure if crs code is not in caps??
        return crs_code_in
    low_crscodein = crs_code_in.lower()
    if low_crscodein == "reading":  # This is because reading always returns reading west, even when you don't put this in
        return "RDG"
    crs_data =  open("NR_media/station_codes.csv", "r")
    options = []
    for line in crs_data: #cannot use a binary search here because list is ordeered, but user might search for "Waterloo" instead of London Waterloo etc, so just checking by letter's is not possible
        line = line.split(",")
        if low_crscodein in line[0].lower():
            options.append([line[0],line[1].strip()])
    if len(options) == 0:
        print("That station could not be found")
        return to_crs(str(input("Please input the station name again")))
    if len(options) == 1:
        return options[0][1]
    num_through = 0
    print("The staition's found where:")
    for each_found_station in options:
        print(str(num_through) + " : " + each_found_station[0])
        num_through += 1
    choice = int(input("Please input the number of the correct station"))
    return options[choice][1]

# This takes the average delay for a service and returns the colour
# todo make colours change based upon data
class website():
    def __init__(self, tag, template_name, output_name, ):
        self.lines_to_add = []
        self.tag = tag
        self.template_name = template_name
        self.output_name = output_name
        self.files_made = []

    def line_to_HTML(self, schedule_time, average, operator, total_services, cancelled, average_desti,
                     journey_time,
                     percent_delayed_service,
                     service_id):  # Could make this so that colour gradient is based on services, so really
        # unreilaible lines arent just all red, colour graident?
        colour_arival_delay = self.delay_colour(average)
        colour_destination_delay = self.delay_colour(average_desti)

        # todo make below into function?
        self.lines_to_add.append(
            '<tr><td> ' + str(schedule_time) + '</td><td bgcolor= ' + str(colour_arival_delay) + ' > ' + str(
                average) + '</td> <td> ' + str(operator) + '</td> <td> ' + str(total_services) + '</td><td>' + str(
                cancelled) + '</td><td bgcolor=' + str(colour_destination_delay) + '>' + str(
                average_desti) + '</td><td>' + str(journey_time) + '</td><td>' + str(
                percent_delayed_service) + '</td><td><a href = ' + str(
                service_id) + '.html' + '> More info </a> </td></tr>')

    def set_line(self, line_to_add):
        self.lines_to_add.append(line_to_add)

    def delay_colour(self, average_delay):
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


class Journey_Info:
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
        #credentials = get_api_credentials()
        self.data = requests.post(url, auth=HTTPBasicAuth(username,password),
                                  headers=headers, data=self.payload)
        if "200" not in str(self.data.status_code):
            print("There has been an error with that request")
            explain_error(str(self.data.status_code))
            self.source_data()
        self.data = json.loads(self.data.text)  # could change this to .json()?

    def get_json_data(self):
        return self.data


class overall_service:
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
        self.average_delay_value_end = None
        self.amount_cancelled = None
        self.percent_delayed = None
        self.StartDelays = []
        self.EndDelays = []

    def get_start_time(self):
        return self.start_time

    def get_individual_id(self):
        return self.individaul_id

    def get_summary(self):
        return (self.start_time, self.average_delay_value_start, self.operator, self.num_rids, self.amount_cancelled,
                self.average_delay_value_end, self.journey_time, self.percent_delayed, self.individaul_id)

    def add_individual_services_skeleton(self):
        amount_done = 1
        for this_indi_train in self.individual_rid_list:
            self.individual_services.append(individual_service(this_indi_train))
            # could put below in its very own function?
            sys.stdout.write('\r')
            sys.stdout.write(str(int((amount_done / self.num_rids) * 100)) + "%")  # str(int) is abit werid
            #sys.stdout.flush()
            amount_done += 1
        sys.stdout.write('\r')

    def add_indi_service_data(self):
        for this_indi_train in self.individual_services:
            this_indi_train.format_data()
            this_indi_train.delays(self.start_time, self.desti_time)
            delay_info = this_indi_train.get_delays()
            self.StartDelays.append(delay_info[0])
            self.EndDelays.append(delay_info[1])

    def add_overall_delay_data(self):
        start_delay_cancelled = self.average_delay(self.StartDelays)
        self.average_delay_value_start = start_delay_cancelled[0]
        self.amount_cancelled = start_delay_cancelled[1]
        self.percent_delayed = start_delay_cancelled[2]
        self.average_delay_value_end = self.average_delay(self.EndDelays)[0]

    def average_delay(self,
                      all_delays):  # this takes a list of each delay and works out the average, not including days where the train was cancelled
        total = 0
        sample_size = 0
        cancelled = 0
        total_industry_delayed = 0  # todo allow user to set value for this??
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
            cancelled = "no data"   #todo check this is the correct value
        return (this_average_delay_value, cancelled, percent_delayed)

    def create_scatter(self):
        number_of_each_delay = [[this_one, self.StartDelays.count(this_one)] for this_one in set(self.StartDelays)]
        size = [5 for i in range(len(number_of_each_delay))]  # Todo this is a bit of a bodge, could be made better?
        this_data = DataFrame(number_of_each_delay, columns=['Delay(Minutes)', 'Number of occurrences'])
        title = "Scatter plot of train delay occurrences for " + str(self.start_time)
        fig = plotly.scatter(this_data, x="Delay(Minutes)", y="Number of occurrences", size=size,
                             title=title)
        html_for_this_service = fig.to_html(fig, full_html=False, include_plotlyjs="cdn", include_mathjax=False)
        html_for_this_service = [html_for_this_service]
        return html_for_this_service


class individual_service:
    def __init__(self, this_rid):
        self.rid = this_rid
        self.data = json.loads((requests.post("https://hsp-prod.rockshore.net/api/v1/serviceDetails",
                                              auth=HTTPBasicAuth(username,password),
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
        return (self.delay_at_start, self.delay_at_desti)


### main
username,password =  get_api_credentials()

print("This service is Powered By national rail enquiries, more info can be found at www.nationalrail.co.uk")
start = to_crs(str(input("Name or CRS code of start station")))
destination = to_crs(str(input("Name or CRS code of the destination station")))

This_Journey = Journey_Info()
This_Journey.create_payload()  # This is creating the payload to be sent to the API, taking basic information from the user and using this to create the payload
This_Journey.source_data()  # This queires the api for the overview data (info on number of jounries found at certain times, but not delay info for each individaul service
overall_output = website("edit me","table","OPENME")

##intitalising variables##
tolerance = 1
invalid_times = []
services_found = 0

###

all_services = []
invalid_service_ids = []
for x in This_Journey.get_json_data()[
    'Services']:  # split into two one creating list, one letting the user choose information
    num_rids = int((x['serviceAttributesMetrics']['matched_services']))
    if num_rids < 2:
        invalid_service_ids.append(services_found)
        invalid_times.append(x['serviceAttributesMetrics']['gbtt_ptd'])
    else:
        ##   self.time_to_overall.append(services_found)   haven't added this in becasuse im not sure what it does
        all_services.append(overall_service(services_found, x['serviceAttributesMetrics']['gbtt_ptd'],
                                            x['serviceAttributesMetrics']['gbtt_pta'], num_rids,
                                            x['serviceAttributesMetrics']['rids'],
                                            x['serviceAttributesMetrics']['toc_code']))
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
if service_choice != "ALL":
    popped = 0
    services_chosen = service_choice.split(",")
    for all_services_found in all_services:
        if str(all_services_found.get_individual_id()) not in services_chosen:
            all_services.pop(
                all_services_found.get_individual_id() - popped)  # todo not sure if clases are gertting deleted here so might need to deleete them first to make it more memory efficent
            popped += 1
for x in all_services:
    print("Getting Data on Service" + str(x.get_individual_id()))
    x.add_individual_services_skeleton()
    x.add_indi_service_data()
    x.add_overall_delay_data()
    this_data = x.get_summary()
    overall_output.line_to_HTML(this_data[0], this_data[1], this_data[2], this_data[3], this_data[4], this_data[5],
                                this_data[6], this_data[7], this_data[8])
sys.stdout.flush()
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
for currently_deleting in overall_output.get_files_made():
    cleanup(currently_deleting)
for x in more_info_pages:
    cleanup((x.get_files_made()[0]))

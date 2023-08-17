import itkdb
import argparse
import requests
import time
import http.client
import datetime
import json
import sys
import numpy as np
import matplotlib.pyplot as plt

# function to convert a formatted date to unix timestamp, this is used to filter warm versus cold tests and pick out the latest date test later in the code. 
 
def convert_to_unix(date_time, format_string):
    dt_object = datetime.datetime.strptime(date_time, format_string)
    unix_timestamp = int(dt_object.timestamp())
    return unix_timestamp

# authenticate itkdb and create an instance of the "Client" class from the itkdb module

code1 = input("ITk Access Code 1?\n")
code2 = input("ITk Access Code 2?\n")

user = itkdb.core.User(code1, code2)
user.authenticate()

if user.is_authenticated():
    print('itkdb login successful!')
else:
    print('Login unsuccessful...')
    sys.exit(1)

print('itkdb authenticate will expire in : '+str(user.expires_in) + ' s')

client=itkdb.Client(user=user)

# create a reauthenticate function to periodically check if expiration is within 5 minutes, and reauthenticate if that is the case

def reauthenticate():
    global user
    if user.is_expired() or user.expires_in < 300:
        print('itkdb login: less than 5 mins left before expires => get new authentication now.')
        user = itkdb.core.User(code1, code2)
        user.authenticate()
        if user.is_authenticated():
            print('itkdb login successful!')
        else:
            print('Login unsuccessful...')
            sys.exit(1)
        client=itkdb.Client(user=user)

# define a dictionary holding information about each test variable: whether it contains an on/off state, whether it differs between warm/cold tests, threshold value, if values should be above or below the threshold (if applicable), and title/xlabel for plot

# note: for test value "HVIIN", the threshold value for the "OFF" state depends on the measurement of the "ON" state and vice versa. this is not implemented in this code, and so for this value a plot without thresholds will be produced 

params = {
    "PADID": {
        "offon": False,
        "warmcold": False,
        "title": "PADID Scan",
        "threshold": 0,
        "threshold_dir": None,
        "xlabel": None
    },
    "RELIABILITY": {
        "offon": False,
        "warmcold": False,
        "title": "Bit Error Reliability",
        "threshold": 1.0,
        "threshold_dir": None,
        "xlabel": None
    },
    "linPOLV": {
        "offon": True,
        "warmcold": False,
        "title": "linPOL Voltage",
        "threshold": [0.25, 1.3],
        "threshold_dir": ["less","more"],
        "xlabel": "Volts"
    },
    "VOUT": {
        "offon": True,
        "warmcold": False,
        "title": "DC/DC Output Voltage",
        "threshold": [0.1, [1.4, 1.65]],
        "threshold_dir": ["less", None],
        "xlabel": "Volts"
    },
    "HVIIN": {
        "offon": True,
        "warmcold": False,
        "title": "High Voltage Current In",
        "threshold": None,
        "threshold_dir": None,
        "xlabel": "Amps"
    },
    "HVIOUT": {
        "offon": True,
        "warmcold": False,
        "title": "High Voltage Current Out",
        "threshold": [2e-6, 0.8e-3],
        "threshold_dir": ["less", "more"],
        "xlabel": "Amps"
    },
    "AMACHVRET": {
        "offon": True,
        "warmcold": False,
        "title": "HVret",
        "threshold": [200, 300],
        "threshold_dir": ["less", "more"],
        "xlabel": "Counts"
    },
    "OFout_value": {
        "offon": True,
        "warmcold": False,
        "title": "OF Voltage Out",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "CALx_value": {
        "offon": True,
        "warmcold": False,
        "title": "CALx Voltage",
        "threshold": [[-0.1, 0.1], [0.75, 1.0]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "CALy_value": {
        "offon": True,
        "warmcold": False,
        "title": "CALy Voltage",
        "threshold": [[-0.1, 0.1], [0.75, 1.0]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "Shuntx_value": {
        "offon": True,
        "warmcold": False,
        "title": "Shuntx Voltage",
        "threshold": [[0.1, 0.3], [0.95, 1.2]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "Shunty_value": {
        "offon": True,
        "warmcold": False,
        "title": "Shunty Voltage",
        "threshold": [[0.1, 0.3], [0.95, 1.2]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "LDx0EN_value": {
        "offon": True,
        "warmcold": False,
        "title": "LDx0EN Voltage",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "LDx1EN_value": {
        "offon": True,
        "warmcold": False,
        "title": "LDx1EN Voltage",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "LDx2EN_value": {
        "offon": True,
        "warmcold": False,
        "title": "LDx2EN Voltage",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "LDy0EN_value": {
        "offon": True,
        "warmcold": False,
        "title": "LDy0EN Voltage",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "LDy1EN_value": {
        "offon": True,
        "warmcold": False,
        "title": "LDy1EN Voltage",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "LDy2EN_value": {
        "offon": True,
        "warmcold": False,
        "title": "LDy2EN Voltage",
        "threshold": [[-0.01, 0.01], [1.0, 1.5]],
        "threshold_dir": [None, None],
        "xlabel": "Volts"
    },
    "AMACNTCX": {
        "offon": False,
        "warmcold": True,
        "title": "NTCx",
        "threshold": [[600, 850], [550, 850]],
        "threshold_dir": None,
        "xlabel": "Counts" 
    },
    "AMACNTCY": {
        "offon": False,
        "warmcold": True,
        "title": "NTCy",
        "threshold": [[600, 850], [550, 850]],
        "threshold_dir": None,
        "xlabel": "Counts" 
    },
    "AMACNTCPB": {
        "offon": False,
        "warmcold": True,
        "title": "NTCpb",
        "threshold": [[600, 1024], [500, 1024]],
        "threshold_dir": None,
        "xlabel": "Counts"
    },
    "AMACCTAT": {
        "offon": False,
        "warmcold": True,
        "title": "CTAT",
        "threshold": [[200, 600], [200, 600]],
        "threshold_dir": None,
        "xlabel": "Counts" 
    },
    "AMACPTAT": {
        "offon": False,
        "warmcold": True,
        "title": "PTAT",
        "threshold": [[500, 900], [500, 900]],
        "threshold_dir": None,
        "xlabel": "Counts"
    },
    "-6% DC/DC Adjust": {
        "offon": False,
        "warmcold": False,
        "title": "-6% DC/DC Adjust",
        "threshold": [-7.67, -5.67],
        "threshold_dir": None,
        "xlabel": "Percent"
    },
    "-13% DC/DC Adjust": {
        "offon": False,
        "warmcold": False,
        "title": "-13% DC/DC Adjust",
        "threshold": [-14.3, -12.3],
        "threshold_dir": None,
        "xlabel": "Percent"
    },
    "+6% DC/DC Adjust": {
        "offon": False,
        "warmcold": False,
        "title": "+6% DC/DC Adjust",
        "threshold": [5.67, 7.67],
        "threshold_dir": None,
        "xlabel": "Percent"
    },
    "EFFICIENCY": {
        "offon": False,
        "warmcold": False,
        "title": "DC/DC Efficiency",
        "threshold": 60,
        "threshold_dir": "more",
        "xlabel": "Percent"
    }

}

# ask the user for test variable of interest, specificying stage, test temperature, and test name beforehand.  

# testing stages are, for example: Die Attachment and Bonding, Thermal Cycling, Burn-In
# if "Thermal Cycling" is chosen, temperature is not asked for, as only a warm test is run during this stage
# for any other stage input, use is prompted to specify either "Warm" or "Cold" to access values within the corresponding tests
# test names are, for example: "Scan PADID", "High Voltage Enable Test", "Toggle Output", "DC/DC Efficiency", etc
# test value names are, for example: "HVIOUT", "LDx2EN_value", "AMACPTAT", etc
# if the chosen test value has an ON/OFF state, the user will be prompted to specify which state
# based on the test variable chosen, choose ON/OFF state, and set title, x-axis, and threshold

stage_name = input("Testing Stage?\n")
if stage_name == "Die Attachment and Bonding":
    stage = "BONDED"
elif stage_name == "Thermal Cycling":
    stage = "THERMAL"
elif stage_name == "Burn-In":
    stage = "BURN_IN"
else:
    print("\nPlease choose a valid testing stage.")
    sys.exit()

if stage != "THERMAL":
    temp = input("Warm/Cold?\n")

test_type = input("Test Name?\n")
    
if test_type != "DC/DC Adjust" and test_type != "DC/DC Efficiency" and test_type != "Scan PADID" and test_type != "Bit Error Rate Test":
    val_name = input("Test Value Name?\n")
    if params[f"{val_name}"]["offon"] == True:
        state = input("OFF/ON?\n")
elif test_type == "DC/DC Adjust":
    percent = input("DC/DC Adjust Percentage?\n")
    if percent == "-13%":
        val_name = "-13% DC/DC Adjust"
    elif percent == "-6%":
        val_name = "-6% DC/DC Adjust"
    elif percent == "+6%":
        val_name = "+6% DC/DC Adjust"
    else:
        print("Please input either '-13%', '-6%', or '+6%'.")
        sys.exit()
elif test_type == "DC/DC Efficiency":
    val_name = "EFFICIENCY"
elif test_type == "Scan PADID":
    val_name = "PADID"
elif test_type == "Bit Error Rate Test":
    val_name = "RELIABILITY"

val_params = params[f"{val_name}"]

if val_params["offon"] == True:
    if state == "OFF":
        if val_params["threshold"] is not None:
            threshold = val_params["threshold"][0]
            if val_params["threshold_dir"][0] is not None:
                threshold_dir = val_params["threshold_dir"][0]
        else:
            threshold = None
        title = f"{val_params['title']}, OFF"
        xlabel = val_params["xlabel"]
    elif state == "ON":
        if val_params["threshold"] is not None:
            threshold = val_params["threshold"][1]
            if val_params["threshold_dir"][1] is not None:
                threshold_dir = val_params["threshold_dir"][1]
        else:
            threshold = None
        title = f"{val_params['title']}, ON"
        xlabel = val_params["xlabel"]
else:
    if val_params["warmcold"] == True:
        if temp == "Warm":
            threshold = val_params["threshold"][0]
            title = val_params["title"]
            xlabel = val_params["xlabel"]
        elif temp == "Cold":
            threshold = val_params["threshold"][1]
            title = val_params["title"]
            xlabel = val_params["xlabel"]
    else:
        threshold = val_params["threshold"]
        threshold_dir = val_params["threshold_dir"]
        title = val_params["title"]
        xlabel = val_params["xlabel"]

# function to plot a list of values in a histogram, displaying the mean, standard deviation, threshold values, and the number of measurements falling outside those thresholds

def hist_plot(vals, binnum, title, xlabel, threshold, outofbounds_ct):
    med = np.median(vals)
    med_sci = '{:.2e}'.format(med)

    stdev = np.std(vals)
    stdev_sci = '{:.2e}'.format(stdev)

    if isinstance(threshold, list):
        plt_range = (threshold[0], threshold[1])
    elif val_name == "PADID" or val_name == "RELIABILITY" or threshold is None:
        plt_range = (min(vals), max(vals))
    elif threshold_dir == "less":
        plt_range = (min(vals), threshold)
    elif threshold_dir == "more":
        plt_range = (threshold, max(vals))

    plt.hist(vals, bins = binnum, range = plt_range,  color = 'steelblue')   
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")

    axis = plt.gca()
    x_min, x_max = axis.get_xlim()
    y_min, y_max = axis.get_ylim()

    x = x_min + 0.1 * (x_max - x_min)
    y_1 = y_min + 0.9 * (y_max - y_min)
    y_2 = y_min + 0.85 * (y_max - y_min)
    y_3 = y_min + 0.80 * (y_max - y_min)
    y_4 = y_min + 0.75 * (y_max - y_min)

    plt.text(x, y_1, f"Med = {med_sci}", fontsize = 10, backgroundcolor = 'white')
    plt.text(x, y_2, rf"$\sigma$ = {stdev_sci}", fontsize = 10, backgroundcolor = 'white')

    if isinstance(threshold, list):
        plt.text(x, y_3, f"Threshold = {threshold[0]} to {threshold[1]}", fontsize = 10, backgroundcolor = 'white')
        plt.axvline(x = threshold[0], linestyle = '--', color = 'gray')
        plt.axvline(x = threshold[1], linestyle = '--', color = 'gray')
    elif threshold is None:
        pass
    else:
        plt.text(x, y_3, f"Threshold = {threshold}", fontsize = 10, backgroundcolor = 'white')
        plt.axvline(x = threshold, linestyle = '--', color = 'gray')
    plt.text(x, y_4, f"# Outside Threshold = {outofbounds_ct}", fontsize = 10, backgroundcolor = 'white')

    plt.show()

# use "get()" method from the "Client" class to receive a list of production Powerboard components

prod_pwb_vals = []

max_retries = 5 
retry_delay = 5

data = {"componentType": ["PWB"], "subproject": ["SB"], "type":["B3"], "pageInfo": {"pageSize": 32}}
reauthenticate()
for attempt in range(1, max_retries + 1):
    try:
        prod_pwbs = client.get("listComponents", json = data)
        break
    except (requests.exceptions.ConnectionError, http.client.RemoteDisconnected) as e:
        print(f"Attempt {attempt}: Connection aborted or remote end closed the connection without response.")
        if attempt < max_retries:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

count1 = 0
count2 = 0
outofbounds_ct = 0

# save the id codes of production Powerboards to a list

list_pwb_code = []
for attempt in range(1, max_retries + 1):
    try:
        for pwb in prod_pwbs:
            if pwb['serialNumber'] is not None and '20USBP05' in pwb['serialNumber']:
                list_pwb_code.append(pwb['code'])
        break
    except (requests.exceptions.ConnectionError, http.client.RemoteDisconnected) as e:
        print(f"Attempt {attempt}: Connection aborted or remote end closed the connection without response.")
        if attempt < max_retries:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

# return a paged object of test run information associated with the component id code

for pwb_code in list_pwb_code:
    count1 += 1
    reauthenticate()
    for attempt in range(1, max_retries + 1):
        try:
            testRuns_bycode = client.get("listTestRunsByComponent", json = {"component": pwb_code, "stage": stage})
            break
        except (requests.exceptions.ConnectionError, http.client.RemoteDisconnected) as e:
            print(f"Attempt {attempt}: Connection aborted or remote end closed the connection without response.")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    print("\n", pwb_code)
    
# using the test id within each paged object, receive a list of all test runs associated with the component as "testRuns". this is in the JSON data format (dictionary)

    testRuns = []
    for testRun in testRuns_bycode:
        reauthenticate()
        for attempt in range(1, max_retries + 1):
            try:
                result = client.get('getTestRunBulk', json = {'testRun':[testRun['id']]})
                break
            except (requests.exceptions.ConnectionError, http.client.RemoteDisconnected) as e:
                print(f"Attempt {attempt}: Connection aborted or remote end closed the connection without response.")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        testRuns.append(result[0])


    if len(testRuns) == 0:
            continue

# filter testRuns by warm/cold. first, find the CTAToffset value within each "Temperatures" test (4 for warm, 9 for cold). find the upload timestamp(s) for the correct CTAToffset value with "stateTs", and find all tests uploaded within 10 minutes of that value. 

    if stage != "THERMAL":
        testRuns_therm = []
        if temp == "Warm":
            testRuns_temp_list = []
            i = 0
            while i < len(testRuns):
                if testRuns[i]['testType']['name'] == "Temperatures":
                    testRuns_temp_list.append(testRuns[i])
                i += 1
            testRuns_temp_warm = []
            i = 0
            while i < len(testRuns_temp_list):
                if testRuns_temp_list[i]['results'][2]['value'] == 4:
                    testRuns_temp_warm.append(testRuns_temp_list[i])
                i += 1
            warm_time_list = []
            i = 0
            while i < len(testRuns_temp_warm):
                warm_time_list.append(convert_to_unix(testRuns_temp_warm[i]['stateTs'].replace('T', ' ').replace('Z',''),"%Y-%m-%d %H:%M:%S.%f"))
                i += 1
            i = 0
            while i < len(testRuns):
                for time in warm_time_list:
                    if abs(convert_to_unix(testRuns[i]['stateTs'].replace('T', ' ').replace('Z', ''), "%Y-%m-%d %H:%M:%S.%f") - time) < 600:
                        testRuns_therm.append(testRuns[i])
                i += 1
        elif temp == "Cold":
            testRuns_temp_list = []
            i = 0
            while i < len(testRuns):
                if testRuns[i]['testType']['name'] == "Temperatures":
                    testRuns_temp_list.append(testRuns[i])
                i += 1
            testRuns_temp_cold = []
            i = 0
            while i < len(testRuns_temp_list):
                if testRuns_temp_list[i]['results'][2]['value'] == 8:
                    testRuns_temp_cold.append(testRuns_temp_list[i])
                i += 1
            cold_time_list = []
            i = 0
            while i < len(testRuns_temp_cold):
                cold_time_list.append(convert_to_unix(testRuns_temp_cold[i]['stateTs'].replace('T', ' ').replace('Z',''),"%Y-%m-%d %H:%M:%S.%f"))
                i += 1
            i = 0
            while i < len(testRuns):
                for time in cold_time_list:
                     if abs(convert_to_unix(testRuns[i]['stateTs'].replace('T', ' ').replace('Z', ''), "%Y-%m-%d %H:%M:%S.%f") - time) < 600:

                        testRuns_therm.append(testRuns[i])
                i += 1
    else:
        testRuns_therm = testRuns

    if len(testRuns_therm) == 0:
        continue

# filter the list of tests by the type of test. if there are more than one tests of the same type at this point, take the latest date test

    testRuns_type = []
    i = 0
    while i < len(testRuns_therm):
        if testRuns_therm[i]['testType']['name'] == test_type:
            testRuns_type.append(testRuns_therm[i])
        i += 1

    if len(testRuns_type) == 0:
        continue
    elif len(testRuns_type) == 1:
        testRuns_type = testRuns_type[0]
    else:
        dates = []
        i = 0
        while i < len(testRuns_type):
            dt = testRuns_type[i]['date']
            dates.append(dt)
            i += 1
        formatted_dates = []
        for date in dates:
            date_format = date.replace('T', ' ').replace('Z','')
            formatted_dates.append(date_format)
        unix_dates = []
        for date in formatted_dates:
            unix_dates.append(convert_to_unix(date, "%Y-%m-%d %H:%M:%S.%f"))
        latest_date = max(unix_dates)
        latest_index = unix_dates.index(latest_date)
        testRuns_type = testRuns_type[latest_index]

    if len(testRuns_type) == 0:
        continue

# find the value of interest, and decide whether it lies within the threshold or not        
  
    if val_name == "-13% DC/DC Adjust" or val_name == "-6% DC/DC Adjust" or val_name == "+6% DC/DC Adjust":
        val_name = "VOUT"

    val = []
    i = 0
    while i < len(testRuns_type['results']):
        if testRuns_type['results'][i]['name'] == val_name:
           val.append(testRuns_type['results'][i]['value'])
           break
        i += 1

    val = val[0]

    if val_params["offon"] == True: 
        if state == "OFF":
            if val_name == "linPOLV":
                val = val[1]
            else:
                val = val[0] 
        elif state == "ON":
            if val_name == "linPOLV":
                val = val[0]
            else:
                val = val[1]
    elif test_type == "DC/DC Efficiency":
        val = val[10] * 100
    elif test_type == "DC/DC Adjust":
        if percent == "-13%":
            val = (testRuns_type['results'][2]['value'][2] / testRuns_type['results'][2]['value'][0] - 1) * 100
        elif percent == "-6%":
            val = (testRuns_type['results'][2]['value'][1] / testRuns_type['results'][2]['value'][0] - 1) * 100
        elif percent == "+6%":
            val = (testRuns_type['results'][2]['value'][3] / testRuns_type['results'][2]['value'][0] - 1) * 100
        else:
            pass
    
    count2 += 1

    if isinstance(threshold, list):
        if val < threshold[0] or val > threshold[1]:
            outofbounds_ct += 1
    elif threshold is None:
        pass
    else:
        if threshold_dir == "less":
            if val > threshold:
                outofbounds_ct += 1
        elif threshold_dir == "more":
            if val < threshold:
                outofbounds_ct += 1
        else:
            if val != threshold:
                outofbounds_ct += 1

    print(val, "\n",  count1, count2, outofbounds_ct)
    prod_pwb_vals.append(val)
    reauthenticate()
    if count2 == 25:
        hist_plot(prod_pwb_vals, 50, title, xlabel, threshold, outofbounds_ct)

# plot the list of values in a histogram    

hist_plot(prod_pwb_vals, 50, title, xlabel, threshold, outofbounds_ct)

#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys, os, csv
import lxml.etree as et

# More info here: https://bids-specification.readthedocs.io/en/latest/04-modality-specific-files/05-task-events.html
# And here: https://bids-specification.readthedocs.io/en/latest/04-modality-specific-files/07-behavioral-experiments.html

from belgerlab_utils import MyParser

def convert_to_seconds(text_value, units): 
    out_value = text_value
    if units == 'msec': 
        out_value = str(float(text_value)/1000)
    return out_value

# Setup and get the input arguments
parser = MyParser(description='Convert BIAC behavioral XML file to BIDS format xxxx_events.tsv')
parser.add_argument("xml_file", help="XML behavioral file you want to convert")
parser.add_argument("out_tsv", help="filename of the output xxxx_events.tsv file")
parser.add_argument("-r", "--rt_string", help="string that represents reaction time code; default RT", default="RT")
args = parser.parse_args()

# Initialize some variables
header_row = ['onset','duration','trial_type','response_time']

# Read the BXH file using XML parser
doc = et.parse(args.xml_file)
root = doc.getroot()

with open(args.out_tsv, mode='w') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(header_row)
    for event in root.iter('event'): 
        e_type = event.get('type')
        e_unit = event.get('units')
        if e_type: 
            e_onset = "0"
            e_duration = "0"
            e_RT = "0"
            trial_type = e_type
            for v in event: 
                v_name = 'N/A'
                v_unit = None
                v_value = v.text
                if v.tag == 'onset': 
                    e_onset = convert_to_seconds(v_value,v_unit)
                if v.tag == 'duration': 
                    e_duration = convert_to_seconds(v_value,v_unit) 
                if v.tag == 'value': 
                    v_name = v.get('name')
                    v_unit = v.get('units')
                    trial_type = trial_type + "_" + v_name + "-" + v_value
                if not v_unit: 
                    v_unit = e_unit               
                if v_name == args.rt_string: 
                    e_RT = convert_to_seconds(v_value,v_unit)
            # print(e_onset + " " + e_duration + " " + trial_type.replace(' ','-') + " " + e_RT)
            csv_writer.writerow([e_onset, e_duration, trial_type.replace(' ','-'), e_RT])
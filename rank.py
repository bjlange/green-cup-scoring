import csv
import pprint
import json

pp = pprint.PrettyPrinter()

data = {}
data['sororities']= {}
data['fraternities'] = {}
data['dining_dorms'] = {}
data['nondining_dorms'] = {}

totals = {}

categories = ['water','energy','participation']

def load_savings_data(csvfile, entity_type, data_type):
    """
    Loads energy data from CSV and calculates absolute and percent savings.
    Arguments: a file object of the CSV, a string representing the type of entity, and a string representing the data type.
    Entity types can be: sororities, fraternities, dining_dorms, nondining_dorms
    Data types can be: energy, water
    CSV format expected to be: 
    column 0: name of entity (dorm, sorority, frat)
    column 1: baseline reading
    column 2-5: weekly readings
    """

    if entity_type not in data.keys():
        print "dude. not recognizing that entity type."
        
    reader = csv.reader(csvfile)
    subdict = data[entity_type]
    for row in reader:
        # normalize the weird names from greek form
        if entity_type is 'sororities': row[0] = row[0].split(', ')[1]
        if entity_type is 'fraternities': row[0] = row[0].split(', ')[0]

        # start with unfilled dictionary for every entity
        try:
            subdict[row[0]][data_type] = {'absolute':[],'percent':[]}
        except KeyError:
            subdict[row[0]] = {data_type: {'absolute':[],'percent':[]}}
        
        try:
            baseline = float(row[1])

        except ValueError:
            print "WARNING: invalid/missing baseline for " + row[0] + " " + data_type
            subdict[row[0]][data_type]['baseline'] = [0]
            subdict[row[0]][data_type]['percent'] = [0]
            subdict[row[0]][data_type]['absolute'] = [0]

        else:
            subdict[row[0]][data_type]['baseline'] = [baseline]
            
            # iterate through weeks
            for weeknum in range(len(row) - 2):
                
                # absolute represents postive savings (so negative vaules = increase)
                subdict[row[0]][data_type]['absolute'].append(baseline - float(row[2+weeknum]))
                
                # percent represents percent reduction from baseline
                subdict[row[0]][data_type]['percent'].append(((baseline - float(row[2+weeknum])) / baseline)*100)


def load_participation_data(csvfile):
    """
    Given a CSV file, load participation percentage data. All
    percentages should be expressed as decimals.
    CSV should be structured like:
     - column 0 = name of residence (using the same names as the savings
    sheets)
     - column 1 = entity type. can be sororities, fraternities,
    dining_dorms or nondining_dorms
     - column 2 = sum of participation percentages for internal events
     - column 3+ = a column for each event with participation percentages
    """
    reader = csv.reader(csvfile)
    for row in reader:
        data[row[1]][row[0]]['participation']= {'internal':[float(row[2])],'events':[]}
        # iterate through events
        for event in range(len(row) - 3):
            data[row[1]][row[0]]['participation']['events'].append(float(row[event+3]))



def calculate_totals():            
    for type in data:
        #constructing aggregate structure
        totals[type]={}
        for category in categories:
            totals[type][category] = {}
        
        #loop through entities
        for name in data[type]:
            for category in categories:
                for attribute in data[type][name][category]:
                    for i, num in enumerate(data[type][name][category][attribute]):
                        if num > 0:
                            try:
                                totals[type][category][attribute][i] += float(num)

                            except KeyError:
                                totals[type][category][attribute] = [float(num)]

                            except IndexError:
                                totals[type][category][attribute].append(float(num))


def calculate_scores():
    #for each entity in each entity type...
    for type in data:
        for name in data[type]:
            data[type][name]['scores'] = {'water':0,
                                          'energy':0,
                                          'savings':0,
                                          'internal':0,
                                          'events':0,
                                          'participation':0,
                                          'overall':0
                                          }
            
            # ENERGY & WATER SCORES
            # iterate through weeks
            for saved in ['energy','water']:
                for i, weeksavings in enumerate(data[type][name][saved]['percent']):
                    # if this weeks savings are positive..
                    if float(weeksavings) > 0:
                        # divide by the total positive savings and add to the score
                        data[type][name]['scores'][saved] += 875*(float(weeksavings)/totals[type][saved]['percent'][i])
               
            # COMBINED SAVINGS SCORE
            data[type][name]['scores']['savings'] = data[type][name]['scores']['energy'] + data[type][name]['scores']['water']

            # EVENT & INTERNAL SCORES
            for amountper, metric in [(300,'internal'),(450,'events')]:
                for i,entry in enumerate(data[type][name]['participation'][metric]):
                    if float(entry) > 0:
                        data[type][name]['scores'][metric] += amountper*((float(entry)/totals[type]['participation'][metric][i]))
                        
            # COMBINED PARTICIPATION SCORE
            data[type][name]['scores']['participation'] = data[type][name]['scores']['internal'] + data[type][name]['scores']['events']

            # COMBINED OVERALL SCORE
            data[type][name]['scores']['overall'] = data[type][name]['scores']['savings'] + data[type][name]['scores']['participation']

            
    

def printSororityRankings(weeknum, score_type):
    def scoreGetter(key):
        return data['sororities'][key]['scores'][score_type]

    print "SORORITIES ranked by " + score_type

    for key in sorted(data['sororities'], key=scoreGetter, reverse=True):
        print "%s: %s" % (key, scoreGetter(key))

    print

def printFraternityRankings(weeknum, score_type):
    def scoreGetter(key):
        return data['fraternities'][key]['scores'][score_type]

    print "FRATERNITIES ranked by " + score_type

    for key in sorted(data['fraternities'], key=scoreGetter, reverse=True):
        print "%s: %s" % (key, scoreGetter(key))

    print

def printDiningDormRankings(weeknum, score_type):
    def scoreGetter(key):
        return data['dining_dorms'][key]['scores'][score_type]

    print "DINING DORMS ranked by " + score_type

    for key in sorted(data['dining_dorms'], key=scoreGetter, reverse=True):
        print "%s: %s" % (key, scoreGetter(key))


def printNondiningDormRankings(weeknum, score_type):
    def scoreGetter(key):
        return data['nondining_dorms'][key]['scores'][score_type]

    print "NONDINING DORMS ranked by " + score_type

    for key in sorted(data['nondining_dorms'], key=scoreGetter, reverse=True):
        print "%s: %s" % (key, scoreGetter(key))

    print

    
def printAnomalies(weeknum, tolerance):
    """
    Prints out of the ordinary numbers.
    Provide a weeknumber (1-4), and a percent tolerance.
    Example: printAnomalies(1,15) shows all savings values > 15% in
    either direction for week 1.
    """

    for type in data:
        print
        print "Anomalies for week %d for type %s:" % (weeknum,type)
        print "===================================="
        for entity in data[type]:
            for attribute in ['water','energy']:
                try:
                    if abs(data[type][entity][attribute]['percent'][weeknum-1]) > tolerance:
                        print entity, attribute, data[type][entity][attribute]['percent'][weeknum-1]
                except IndexError:
                    print "No week %d %s data for %s" % (weeknum, attribute, entity)


load_savings_data(open('numbers/sorowk1.csv', 'rU'),'sororities','energy')
load_savings_data(open('numbers/fratswk1.csv', 'rU'),'fraternities','energy')
load_savings_data(open('numbers/dining.csv', 'rU'),'dining_dorms', 'energy')
load_savings_data(open('numbers/nondining.csv', 'rU'),'nondining_dorms', 'energy')

load_savings_data(open('numbers/soro_water.csv', 'rU'),'sororities','water')
load_savings_data(open('numbers/frats_water.csv', 'rU'),'fraternities','water')
load_savings_data(open('numbers/dining_water.csv', 'rU'),'dining_dorms', 'water')
load_savings_data(open('numbers/nondining_water.csv', 'rU'),'nondining_dorms', 'water')

load_participation_data(open('numbers/participation.csv', 'rU'))



calculate_totals()
calculate_scores()

# pp.pprint(data)
# pp.pprint(totals)


# # Making sure things add up.
# for type in data:
#     print type
#     check = {}
#     for name in data[type]:
#         dict = data[type][name]['scores']
#         for key in dict:
#             try:
#                 check[key] += dict[key]
#             except KeyError:
#                 check[key] = dict[key]

#     print check



printSororityRankings(0,'overall')
print "\n===================================="
printFraternityRankings(0,'overall')
print "\n===================================="
printDiningDormRankings(0,'overall')
print "\n===================================="
printNondiningDormRankings(0,'overall')

#print json.dumps(data)

# printAnomalies(1,20)
# printAnomalies(2,20)

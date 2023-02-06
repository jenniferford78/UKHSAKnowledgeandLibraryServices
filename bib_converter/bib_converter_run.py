# Overall architecture
# Class hierarchy for parsing levels of the input string (translation should be line -> line)
##
# Ask classes to emit translations at their level
# Each object can be initialised with an Ovid string (to be refactored later)
# and has an export method taking the target database name 
# Hold warnings for each line in a global variable to be emitted alongside the outputs
# Command line operation, takes a plain text file with a search strategy and a output type
# Outputs a file with an attempted translation and another file of generated warnings

# Notes:
# Current aim is to map from Ovid only
# Rejects solo 'adj' from Ovid as this is a null operator
# Currently doesn't support multiple field search conditions

import re

# User customisable parameters

field_mappings_from_ovid = {'tw': {'WoS':'TS', 'Cochrane':'ti,ab', 'Scopus': 'TITLE-ABS', 'Proquest': 'ABSTRACT,TITLE', 'PubMed': 'tiab'},
'ti': {'WoS': 'TI', 'Cochrane':'ti', 'Scopus': 'TITLE', 'Proquest': 'TITLE', 'PubMed': 'ti', 'EBSCO': 'TI'},
'm.titl': {'WoS': 'TI', 'Cochrane':'ti', 'Scopus': 'TITLE', 'Proquest': 'TITLE', 'PubMed': 'ti', 'EBSCO': 'TI'},
'ab': {'Scopus': 'ABS', 'Cochrane':'ab', 'Proquest': 'ABSTRACT', 'PubMed': 'ab', 'EBSCO': 'AB'},
'kf': {'WoS': 'KP', 'Scopus': 'KEY', 'Cochrane':'kw', 'Proquest': 'IF', 'PubMed': 'ot', 'EBSCO': 'SU'},
'kw': {'WoS': 'KP', 'Scopus': 'KEY', 'Cochrane':'kw', 'Proquest': 'IF', 'PubMed': 'ot', 'EBSCO': 'SU'}}

field_combine_functions = {
    'Proquest': lambda fields, condition : ','.join(fields) + '(' + condition + ')',
    'Scopus': lambda fields, condition : '-'.join(fields) + '(' + condition + ')',
    'WoS' : lambda fields, condition: ' OR '.join([field + '=(' + condition + ')' for field in fields]),
    'Cochrane' : lambda fields, condition: condition + ':' + ','.join(fields),
    'EBSCO': lambda fields, condition : ','.join(fields) + condition,
    'PubMed' : lambda fields, condition: ' OR '.join([condition + '[' + field + ']' for field in fields])
}

query_mapping = {    'Proquest': lambda match: f'{match[0]}',
        'Scopus': lambda match: f'#{match[0]}',
        'WoS': lambda match: f'#{match[0]}',
        'Cochrane': lambda match: f'#{match[0]}',
        'EBSCO': lambda match: f'S{match[0]}',
        'PubMed': lambda match: f'#{match[0]}'
    }

adj_mapping = {    'Proquest': lambda ovid_distance: f'NEAR/{ovid_distance-1}',
                'Scopus': lambda ovid_distance: f'W/{ovid_distance-1}',
                'WoS' : lambda ovid_distance: f'NEAR/{ovid_distance-1}',
                'Cochrane' : lambda ovid_distance: f'NEAR/{ovid_distance-1}',
                'EBSCO': lambda ovid_distance: f'N{ovid_distance-1}',
                'PubMed': lambda ovid_distance: f'~{ovid_distance-1}'
            }

optionals = {'EBSCO': '#', 'Cochrane': '?', 'WoS': '$', 'Scopus': '*', 'Proquest': '*'}
mandatories = {'EBSCO': '?', 'Cochrane': '?', #Warning for Cochrane
                'WoS': '?', 'Scopus': '?', 'Proquest': '?' }


operator_regex = r'[^"]*(?:[^"]*["][^"]*["][^"]*)*\s(and|or|adj\d+)\s' #Operator must be preceded by an even number of quotes
# Use re.match instead of re.search to force starting at the start of the string


# Class hierarchy (bottom up)

class StringCondition:
    def __init__(self, input_string, from_database = 'Ovid'):
        self.input_string = input_string
        self.parsed_string = re.sub(f'\?', '<OPTIONAL>', self.input_string)
        self.parsed_string = re.sub(f'#', '<MANDATORY>', self.parsed_string)
        if self.input_string[0] == '"':
            self.quoted = True
        else:
            self.quoted = False
    def export(self, to_database):
        global warnings
        if to_database == 'PubMed' and re.findall(f'<', self.parsed_string):
            warnings = warnings.append('Wildcards could not be mapped as unsupported in PubMed for string ' + self.input_string)
            return '<WILDCARD ERROR>'
        if to_database == 'PubMed':
            temp_for_export = self.parsed_string
        else:
            temp_for_export = re.sub(f'<OPTIONAL>', optionals[to_database], self.parsed_string)
            if to_database == 'Cochrane' and re.findall(f'<MANDATORY>', temp_for_export):
                warnings = warnings.append('Mandatory wildcard converted to optional as unsupported in Cochrane for string ' + self.input_string)
            temp_for_export = re.sub(f'<MANDATORY>', mandatories[to_database], temp_for_export)
        if re.findall(f' ', temp_for_export) and not self.quoted:
            temp_for_export = '"' + temp_for_export + '"'
        return temp_for_export


class Operator:
    # And/Or/adjX
    def __init__(self, input_string, from_database = 'Ovid'):
        self.input_string = input_string
        self.is_adj = bool(re.findall('adj', input_string))
        if self.is_adj:
            # Do not accept 'adj' on its own from Ovid
            self.proximity_ovid = int(input_string[3:])
    def export(self, to_database):
        if self.is_adj:
            return adj_mapping[to_database](self.proximity_ovid)
        else:
            return self.input_string



class OperatorCombinedFieldCondition:
    def __init__(self, left_string, operator_string, right_string):
        self.left = FieldCondition(left_string)
        self.operator = Operator(operator_string)
        self.right = FieldCondition(right_string)
    def export(self, to_database):
        left_export = self.left.export(to_database)
        operator_export = self.operator.export(to_database)
        right_export = self.right.export(to_database)
        return left_export + ' ' + operator_export + ' ' + right_export


class FieldCondition:
    # This can be bracketed or otherwise
    def __init__(self, input_string, from_database = 'Ovid'):
        stripped_input = input_string.strip()
        def FindPairedBracket(string):
            # Ignore brackets in quotes
            depthCounter = 0
            quoted = False
            for n, i in enumerate(string):
                if i == '"':
                    quoted = not quoted
                if not quoted: 
                    if i == '(':
                        depthCounter = depthCounter + 1
                    elif i == ')':
                        depthCounter = depthCounter - 1
                        if depthCounter == 0:
                            return n
            return None
        if stripped_input[0] == '(':
            matching_bracket_location = FindPairedBracket(stripped_input)
            if matching_bracket_location + 1 == len(stripped_input):
                #input is entirely in a pair of brackets
                self.type = 'bracketedinput'
                self.condition = FieldCondition(stripped_input[1:-1])
            else:
                # operator combination of stuff
                left_string = stripped_input[:matching_bracket_location + 1]
                remaining_string = stripped_input[matching_bracket_location + 1:]
                self.type = 'operatorcombinedinput'
                operator_location = re.match(operator_regex, remaining_string)
                right_string = remaining_string[operator_location.end(1):]
                operator_string = remaining_string[operator_location.start(1):operator_location.end(1)].strip()
                self.condition = OperatorCombinedFieldCondition(left_string, operator_string, right_string)
        else:
            if re.match(operator_regex, stripped_input):
                self.type = 'operatorcombinedinput'
                operator_location = re.match(operator_regex, stripped_input)
                left_string = stripped_input[:operator_location.start(1)]
                operator_string = stripped_input[operator_location.start(1):operator_location.end(1)].strip()
                right_string = stripped_input[operator_location.end(1):]
                self.condition = OperatorCombinedFieldCondition(left_string, operator_string, right_string)
            else:
                self.type = 'stringcondition'
                self.condition = StringCondition(stripped_input)
    def export(self, to_database):
        if self.type == 'bracketedinput':
            return '(' + self.condition.export(to_database) + ')'
        elif self.type == 'operatorcombinedinput':
            return self.condition.export(to_database)
        elif self.type == 'stringcondition':
            return self.condition.export(to_database)


class FieldSearchCondition:
    def __init__(self, input_string, from_database = 'Ovid'):
        if from_database == 'Ovid':
            field_list = re.findall(r'\.[\w,]+\.?$', input_string)
            if field_list:
                field_list_string = field_list[0]
                self.has_field_list = True
                field_string = input_string[:-len(field_list_string)]
                self.field_list = field_list_string.strip('.').split(',')
                self.field_condition = FieldCondition(field_string)
            else:
                self.has_field_list = False
                self.field_condition = FieldCondition(input_string)
    def export(self, to_database):
        global warnings
        if not self.has_field_list:
            exported_field_condition = self.field_condition.export(to_database)
            return exported_field_condition
        def map_field_item(field_item, to_database):
            try:
                to_field = field_mappings_from_ovid[field_item][to_database]
            except KeyError:
                warnings.append(f'Was not able to find an equivalent for {field_item} for {to_database}')
                return None
            return to_field
        temp_mapped_field_items = [map_field_item(field_item, to_database) for field_item in self.field_list]
        temp_mapped_field_items = [item for item in temp_mapped_field_items if item is not None]
        exported_field_condition = self.field_condition.export(to_database)
        if to_database == 'PubMed':
            #Horrible hack to pull adjacency operators into the field items
            proximities = re.findall(f'~(\d+) ', exported_field_condition)
            if proximities:
                exported_field_condition = re.sub(f'~(\d+) ', '', exported_field_condition)
                greatest_proximity = max([int(proximity) for proximity in proximities])
                temp_mapped_field_items = [item + ':~' + str(greatest_proximity) for item in temp_mapped_field_items]
                #Ovid proximity search doesn't support wildcards so we have to strip them too
                if re.findall(f'*', exported_field_condition):
                    warnings.append(f'Ovid proximity search does not support wildcards in the string ' + exported_field_condition)
        return field_combine_functions[to_database](temp_mapped_field_items, exported_field_condition)

class SubjectTerm:
    def __init__(self, input_string, from_database = 'Ovid'):
        self.input_string = input_string
        cleaned_input = input_string.strip('/')
        if re.match('exp', cleaned_input):
            self.explode = True
        else:
            self.explode = False
        cleaned_input = cleaned_input.strip('exp ')
        if cleaned_input[0] == '*':
            self.focus = True
        else:
            self.focus = False
        cleaned_input = cleaned_input.strip('*')
        self.subject_text = cleaned_input
    def export(self, to_database):
        global warnings
        if not to_database == 'PubMed':
            warnings.append(f'Was not able to map subject heading for database ' + to_database + ' for string ' + self.input_string)
            return 'Unmapped subject heading ' + self.input_string
        elif to_database == 'PubMed':
            if self.focus == False:
                field = 'MeSH'
            else:
                field = 'Majr'
            if self.explode == False:
                field = field + ':noexp'
            return self.subject_text + '[' + field + ']'
                            

class Phrase:
    def __init__(self, input_string, from_database = 'Ovid'):
        cleaned_input = input_string.strip('\n')
        cleaned_input = cleaned_input.strip()
        # Clean off the 1. and the  
        line_number_match = re.match(r'\d+(\.|  )', cleaned_input)
        if line_number_match is None:
            pass
        else:
            cleaned_input = cleaned_input[line_number_match.end():].strip()
        result_count_match = re.search(r'\(\d+\)$', cleaned_input)
        # check if it's a boolean combination of previous queries or a FieldCondition
        if result_count_match is None:
            pass
        else:
            cleaned_input = cleaned_input[:result_count_match.start()].strip()
        print(cleaned_input)
        if re.match(r'\d+', cleaned_input):
            self.type = 'combinednumberedqueries'
            self.text = cleaned_input
        elif re.match(r'(and|or)/', cleaned_input):
            self.type = 'combinednumberedqueries'
            booleanmatch = re.match(r'(and|or)/', cleaned_input)
            queryrange = cleaned_input[booleanmatch.end():]
            queryrangemin = int(queryrange.split('-')[0])
            queryrangemax = int(queryrange.split('-')[1])
            operator = booleanmatch[0][:-1]
            self.text = (' ' + operator + ' ').join([str(i) for i in range(queryrangemin, queryrangemax + 1)])
        elif re.match(r'[,\w *]+/', cleaned_input):
            self.type = 'subjecttermquery'
            self.condition = SubjectTerm(cleaned_input)
        else:
            self.type = 'fieldsearchcondition'
            self.condition = FieldSearchCondition(cleaned_input)
    def export(self, to_database):
        if self.type == 'fieldsearchcondition':
            return self.condition.export(to_database)
        elif self.type == 'subjecttermquery':
            return self.condition.export(to_database)        
        else:
            # Query mappings
            return re.sub(r'\d+', query_mapping[to_database], self.text)


# Processing code

def do_a_line(line, to_database):
    #returns output, warningline
    global warnings
    warnings = []
    try:
        # Parse
        phrase = Phrase(line)
    except:
        # Error parsing the line
        returnline = 'Could not parse: ' + line.strip('\n')
        warningline = '; '.join(['Error: could not parse: ' + line.strip('\n')] + warnings)
        return returnline, warningline
    else: 
        try:
            export = phrase.export(to_database)
        except:
            # export failure
            returnline = 'Could not export: ' + line.strip('\n')
            warningline = '; '.join(['Error: could not export: ' + line.strip('\n')] + warnings)
            return returnline, warningline
        else:
            warningline = '; '.join(warnings)
            return export, warningline

# Browsing for file copied from (https://stackoverflow.com/a/3579625/11732165)

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter.simpledialog import askstring

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
input_file = askopenfile() # show an "Open" dialog box and return the path to the selected file

lines = input_file.readlines()
input_file.close()

to_database = askstring('Target database', 'Cochrane/WoS/EBSCO/Proquest/Scopus/PubMed')

done_lines = [do_a_line(line, to_database) for line in lines]

output_file = asksaveasfile(defaultextension=".txt", filetypes=(("text file", "*.txt"),("All Files", "*.*") ))
output_file.writelines([done_line[0] + '\n' for done_line in done_lines])
output_file.writelines(['Warnings:\n'])
output_file.writelines([done_line[1] + '\n' for done_line in done_lines])
output_file.close()
# Tests

"""
StringCondition('green space*').export('Cochrane')
StringCondition('Tumo?r*').export('Proquest')
Operator('and').export('Proquest')
Operator('adj16').export('EBSCO')
FieldCondition('air condi?ioning*').export('Proquest')
FieldCondition('air condi?ioning* and mushrooms').export('EBSCO')
FieldCondition('air condi?ioning* adj4 mushrooms').export('EBSCO')
FieldCondition('(bacon or sausages) adj3 mushrooms').export('WoS')
Phrase('1 and 2').export('Proquest')
Phrase(r'or/5-20').export('Proquest')
Phrase('bacon and eggs.tw,ti').export('EBSCO') #Error because fields not defined for EBSCO
Phrase('bacon and eggs.tw,ti').export('WoS')
FieldCondition('"air condi?ioning* and mushrooms"').export('EBSCO')
Phrase('37 weeks').export('EBSCO')
Phrase('"37 weeks"').export('EBSCO')
FieldSearchCondition('"air condi?ioning* and mushrooms"').export('EBSCO')
Phrase('bacon and eggs').export('EBSCO')
Phrase('"bacon and eggs"').export('EBSCO')
Phrase('"bacon sandwich" and "poached eggs"').export('EBSCO')

"""

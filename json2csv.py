#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Copyright Marco Conti 2014 - marcoconti83@gmail.com

# Converts JSON to CSV flattening any array into multiple CVS fields
# See readme.md for documentation / usage example

import json
import sys
import csv
import argparse
import StringIO

SUPPORTED_SCALAR_TYPES = [basestring, long, int, bool, float]
SUPPORTED_VECTOR_TYPES = [list, tuple]


##########################################################################
def die(*args):
    '''Prints an error message and exits'''
    print >> sys.stderr, "ERROR:", " ".join(map(str, args))
    exit(1)


###########################################################################
def isSupportedScalarType(value):
    '''Checks whether the variable is a supported scalar type'''
    for t in SUPPORTED_SCALAR_TYPES:
        if isinstance(value, t):
            return True
    return False

def isSupportedVectorType(value):
    '''Checks whether the variable is a supported scalar value'''
    for t in SUPPORTED_VECTOR_TYPES:
        if isinstance(value, t):
            # now check that internal values are scalar
            for i in value:
                if not isSupportedScalarType(i):
                    return False
            return True
            
    return False

def getValueAtPath(dictionary, path):
    '''
    Returns the value at the given path. Path is a list. 
    e.g. [a, b, c] will get the path at dictionary[a][b][c]
    '''
    val = dictionary
    for i in path:
        if isinstance(val, (list, tuple)):
            if i.isdigit():
                val = val[int(i)]
            else:
                die("Path",path,"at position",i,"expects a number as the JSON contains an array")
        else:
            val = val[i]
    return val

##########################################################################
class Json2CSVConverter(object):
    
    '''Converts a JSON into a CVS'''
    def __init__(self, file):
        self.__json = self.__loadFromFile(file)
        self.__fields = {} # field name (str) to field cardinality (int)
        self.arrayFieldNamingFormat = "{fieldName}_{index}"
        
    def __vectorialFieldName(self, field, index):
        '''Returns the name of the field for a vector field value in position index'''
        return self.arrayFieldNamingFormat.format(fieldName=field,index=index)
        
    def __loadFromFile(self, file):
        with open(file, "r") as FILE:
            return json.load(FILE)
    
    def __extractHeaders(self, dictionaries):
        '''Extract the list of headers for the CVS'''
        for d in dictionaries:
            for key in d.iterkeys():
                value = d[key]

                if isSupportedVectorType(value):
                    self.__addFieldHeader(key, max(len(value),1))
                    continue
                    
                if isSupportedScalarType(value):
                    self.__addFieldHeader(key, 1)
                    continue
                    
                die("Unknown type for value {}: {} ({})".format(key, value, type(value)))
    
    def __createFieldsDictionary(self):
        '''Returns a dictionary with keys from the headers list'''
        dictionary = {}
        for (field, cardinality) in self.__fields.items():
            if(cardinality == 1):
                dictionary[field] = None
            else:
                for i in xrange(cardinality):
                    name = self.__vectorialFieldName(field, i)
                    dictionary[name] = None
        return dictionary
    
    def __recordsList(self, dictionaries):
        '''Return the list of records'''
        
        records = []
        for values in dictionaries:
            record = self.__createFieldsDictionary()
            for (field, value) in values.items():
                if self.__fields[field] > 1:
                    # vector type
                    for i in xrange(len(value)):
                        name = self.__vectorialFieldName(field, i)
                        record[name] = value[i]
                # scalar type or size-1 array
                else:
                    if isSupportedVectorType(value):
                        if len(value) > 0:
                            value = value[0]
                        else:
                            value = None
                    if isinstance(value, unicode):
                        value = value.encode('ascii', errors='backslashreplace')
                    if isinstance(value, basestring):
                        value = value.replace('\r\n',' ')
                    record[field] = value
                    
            # now sort record by keys
            sortedRecord = []
            for k in sorted(record.keys()):
                sortedRecord.append(record[k])
                
            records.append(sortedRecord)
        return records
        
    
    def __flatten(self, dictionaries, file):
        '''Extracts a list of headers from an array of dictionaries'''
        self.__extractHeaders(dictionaries)
        records = self.__recordsList(dictionaries)

        sortedHeaders = sorted(self.__createFieldsDictionary().keys())
        
        outputBuffer = StringIO.StringIO()
        writer = csv.writer(outputBuffer)
        writer.writerow(sortedHeaders)
        writer.writerows(records)
            
        output = outputBuffer.getvalue()
        outputBuffer.close()
            
        if file:
            with open(file, "wb") as FILE:
                FILE.write(output)
                print len(records), "records written to", file
        else:
            print output
            
    def __addFieldHeader(self, fieldName, cardinality):
        '''Adds a field to the list, with the given cardinality. If the field exists already, uses the max cardinality between the two'''
        previous = self.__fields.get(fieldName, 1)
        self.__fields[fieldName] = max(cardinality, previous)
        
    def cvs(self, JSONpath, outputFile):
        '''Saves a CVS representation of an array in the JSON. JSON is a path (see 'getValueAtPath')'''
        self.__fields = {}
        array = getValueAtPath(self.__json, JSONpath)
        if not isinstance(array, (list,tuple)):
            die("Requested path", "->".join(map(str,JSONpath)), "is of unsupported type", type(array))
        for d in array:
            if not isinstance(d, dict):
                die("Requested path", "->".join(map(str,JSONpath)), "contains a non-dictionary element", d)
        
        self.__flatten(array, outputFile)
    
##############################################################################
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Converts a JSON file with an array of records to CSV (comma separated values)")
    parser.add_argument("json_file", help="The json input file")
    parser.add_argument("-o", "--output-file", help="Output to the specified file", default=None)
    parser.add_argument("-p", "--json-path", help="Path (comma-separated) inside the JSON to the array of records to converts, e.g. 'results,array' will point to the first-level field 'results' and then to its subfield 'array'. Leave empty only if the entire JSON is already an array of records", default=None)
    parser.add_argument("-n", "--array-field-naming", help="Format for naming of sub-fields for array-like fields. Use '{fieldName}' as a placeholder of the field name, and {index} as a placeholder for the sub-field index. This string is used in Python's str.format() function, please refer to the Python documentation for more advanced usages", default="{fieldName}_{index}")
    
    args = parser.parse_args()
    
    converter = Json2CSVConverter(args.json_file)
    converter.arrayFieldNamingFormat = args.array_field_naming
    path = []
    if args.json_path:
        path = args.json_path.split(',')
    
    converter.cvs(path, args.output_file)

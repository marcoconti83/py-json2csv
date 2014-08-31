py-json2csv
===========

A JSON to CSV converter made with Python

Copyright (C) Marco Conti 2014 - marcoconti83@gmail.com 

https://www.marco83.com/work

Scope
------------
It converts a JSON file with a set of records (array of dictionaries) into a CSV representation of those records.

Details
-----------

__Flattening vector fields__

Since dictionaries can have some fields that are arrays, the corresponding CSV representation will be flattened. 

E.g.
the following JSON record

    {
        "name" : "Marco",
        "aka" : ["MC", "Marco C"]
    }
    
will be converted to

    # headers
    name,aka_1,aka2
    # values
    Marco,MC,Marco C

__JSON path__

The list of records in the JSON doesn't need to be the top-level object. Nested objects like the one containing the records (`name:A` and `name:B` ) in the following example:

    {
        "data" : [
            {
                "payload" : "foo"
            },
            {
                "records" : [
                    {
                        "name" : "A"
                    },
                    {  
                        "name" : "B"
                    }
                ]
            }
        
        ]
    }

can be accessed with the following path syntax:

    data,1,records
    
which means: `data` field, second element (0-based indexing), `records` field

Sample usage
------------
Type

    ./json2csv.py --help
	
for a list of options

Try:

    ./json2csv.py -o o.txt -p queries,1,results -n "{fieldName}_n{index}" sample.json

It will convert the `sample.json` into `o.txt`
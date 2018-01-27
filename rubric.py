import os
import glob

def genSampleRubric():
    file = open('sample_rubric.txt', 'w+')
    file.write('# Lines that begin with \'#\' will be ignored as comments.\n')
    file.write('# Enter a single item per line, with the following syntax: \n')
    file.write('# <item_name>: /<max_val>\n')
    file.write('# Below are some examples.\n')
    file.write('compiles: /1\n')
    file.write('runs: /1\n')
    file.write('output: /4\n')
    file.close()

def parseRubric(filename):
    # First check if the file actually exists.
    if not os.path.isfile(filename):
        print('Please provide a valid rubric file.')
        return {}

    # Let's open the file and start reading lines.
    rubric = {}
    with open(filename) as file:
        for count, line in enumerate(file):
            if line.startswith('#'):
                continue
            tokens = line.split(':')

            # If we don't split into exactly 2, then we have a problem.
            if len(tokens) != 2:
                print('In file {} ({}): Invalid syntax'.format(filename, count))
                return {}

            # The item is stored in the first entry (before the ':').
            item = tokens[0]

            vals = tokens[1].split('/')
            if len(tokens) != 2:
                print('In file {} ({}): Invalid syntax'.format(filename, count))
                return {}

            # The value is in the second entry of the list.
            try:
                maxVal = int(vals[1])

            except ValueError as e:
                print('In file {} ({}): Invalid value provided. Expected \'int'
                      '\' received \'{}\''.format(filename, count, 
                                                  vals[1].strip()))
                return {}

            rubric[item] = [0, maxVal]

    return rubric

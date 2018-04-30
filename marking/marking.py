import argparse
import os
import time
import csv
import traceback
import configparser
from os.path import basename
from utils import Config, Editor, Rubric 
from marker import Marker

def convertPaths(path, join = False):
    dir = path
    if join:
        dir = ' '.join(path)

    dir = os.path.normpath(dir)
    if not os.path.isabs(dir):
        currDir = os.getcwd()
        dir = os.path.join(currDir, dir)

    return dir

def makeComments(grades, root):
    for entry in os.scandir(root):
        if not entry.is_dir():
            continue

        # We need to find the appropriate rubric.
        name = entry.name
        try:
            studentRubric = next(x for x in grades if x.studentName == name)
        except Exception as e:
            # If we can't find the student name in our list of marks, then
            # either they submitted nothing or they submitted garbage, so 
            # skip them.
            continue

        # Now switch into the students directory.
        os.chdir(entry.path)

        # Now we have to generate the comments.txt file.
        with open('comments.txt', 'w+', newline = '\n') as file:
            file.write('<pre>#=============================#\n')
            file.write('# Instructor\'s comments\n')
            file.write('#=============================#\n')
            i = 0
            for item, mark in studentRubric.attributes.items():
                file.write('{}: {}/{}\n'.format(item, mark,
                                                studentRubric.maxVals[i]))
                i += 1

            file.write('Total: {}\n'.format(studentRubric.total))
            file.write('Comments:\n{}'.format(studentRubric.comments))

def makeCSV(grades, root):
    filePath = os.path.join(root, 'grades.csv')
    rows = []
    with open(filePath, 'r+') as file:
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)

    # Now fill in the total mark.
    for i in range(3, len(rows)):
        id = rows[i][1]
        lastName = rows[i][2]
        firstName = rows[i][3]

        name = lastName + ', ' + firstName + '(' + id + ')'
        try:
            studentRubric = next(x for x in grades if x.studentName == name)
        except Exception as e:
            continue

        rows[i][-1] = studentRubric.total

    # Now let's write out the csv file.
    with open(filePath, 'w+', newline = '\n') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def readConfigFile(path):
    config = configparser.ConfigParser()
    config.read(path)

    # Let's read in the config stuff first.
    conf = Config()
    conf.root = convertPaths(config['Config']['root'])
    conf.makeCSV = config['Config'].getboolean('makeCSV')
    conf.makeComments = config['Config'].getboolean('makeComments')
    conf.workingDir = convertPaths(config['Config']['working'])


    # Now let's read in the editor
    editor = Editor()
    editor.cmd = config['Editor']['editor']

    # Since the editor args are completely optional, we need to check to
    # see if the user has provided any.
    if config.has_option('Editor', 'editorArgs'):
        editor.args = config['Editor']['editorArgs']

    # Now make the Marker
    marker = Marker()
    marker.extension = config['Language']['extension']
    marker.generatedExtension = config['Language']['generatedExtension']
    marker.isInterpreted = config['Language'].getboolean('isInterpreted')
    marker.compiler = config['Language']['compiler']
    marker.run = config['Language']['run']
    marker.editor = editor
    marker.workingDir = conf.workingDir

    # The IO section is optional, so only parse it if needed.
    if config.has_section('IO'):
        if config.has_option('IO', 'input'):
            inFiles = config['IO']['input']
            inFiles = inFiles.split(';')
            inf = []
            for file in inFiles:
                inf.append(convertPaths(file))

            marker.inputFiles = inf

        if config.has_option('IO', 'output'):
            outFiles = config['IO']['output']
            outFiles = outFiles.split(';')
            out = []
            for file in outFiles:
                out.append(convertPaths(file))
            marker.outputFiles = out

        if config.has_option('IO', 'diff'):
            marker.diff = config['IO'].getboolean('diff')

    if config.has_section('Aux'):
        if config.has_option('Aux', 'files'):
            auxFiles = config['Aux']['files']
            auxFiles = auxFiles.split(';')
            aux = []
            for file in auxFiles:
                aux.append(convertPaths(file))
            marker.auxFiles = aux
        if config.has_option('Aux', 'script'):
            script = config['Aux']['script']
            marker.preProcessScript = convertPaths(script)

    # Finally, we read the rubric.
    rubric = Rubric()
    for key in config['Rubric']:
        rubric.attributes[key] = 0
        rubric.maxVals.append(config['Rubric'].getfloat(key))

    return conf, marker, rubric

def makeSampleConfig():
    with open('sample.ini', 'w+') as file:
        file.write('# This is a sample config file for the marking script.\n')
        file.write('# You may use this as a template to build your own.\n')
        file.write('# Please note that all attributes (save for those under\n')
        file.write('# the [Rubric] section are reserved keywords).\n')
        file.write('# Lines that start with \'#\' are comments.\n\n')
        file.write('[Config]\n')
        file.write('root = \'path/to/root\'\n')
        file.write('makeCSV = true\n')
        file.write('makeComments = true\n')
        file.write('\n')
        file.write('[Editor]\n')
        file.write('editor = \'\'\n')
        file.write('editorArgs = \'\'\n')
        file.write('\n')
        file.write('[Language]\n')
        file.write('extension = \'\'\n')
        file.write('isInterpreted = false\n')
        file.write('compiler = \'\'\n')
        file.write('run = \'\'\n')
        file.write('\n')
        file.write('[IO]\n')
        file.write('input = \'\'\n')
        file.write('output = \'\'\n')
        file.write('diff = false\n')
        file.write('[Rubric]\n')
        file.write('# Your elements here.')

def main():
    parser = argparse.ArgumentParser(description = 
                                     'Marks assignments in an automatic way.')
    parser.add_argument('-g', '--generate-config', action = 'store_true',
                        dest = 'gen', default = False,
                        help = 'Generate sample config file.')
    parser.add_argument('-c', '--config', action = 'store', type = str,
                        dest = 'config', nargs = '+',
                        help = 'The config file to use.')

    args = parser.parse_args()

    # Check if we have to generate the sample ini file.
    if args.gen == True:
        makeSampleConfig()
        return

    # We don't, so first let's check the path for the config file.
    configPath = convertPaths(args.config, True)

    # Now that we have the path, let's start setting things up.
    conf, marker, rubric = readConfigFile(configPath)
    grades = marker.mark(conf.root, rubric)

    # Check if we have to generate the csv files and comment files
    if conf.makeComments:
        makeComments(grades, conf.root)

    if conf.makeCSV:
        makeCSV(grades, conf.root)

    # Only remove the incremental file if we have written everything to
    # the CSV and comment files.
    if conf.makeComments and conf.makeCSV:
        # At this point in the process we are done with everything, so clean up
        # the working directory.
        for file in os.scandir(conf.workingDir):
            if not file.is_file():
                continue
            os.remove(file)


if __name__ == '__main__':
    main()

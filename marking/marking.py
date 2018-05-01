import argparse
import os
import time
import csv
import traceback
import configparser
from os.path import basename
from utils import Config, Editor, Rubric 
from javamarker import JavaMarker
from pythonmarker import PythonMarker

def convertPaths(path, join = False):
    """
    Converts relative paths to absolute paths.

    Parameters:
    ----------
    path:
        The path to convert
    join:
        Whether the path should be joined or not.

    Returns:
    ----------
        A string containing the absolute path.
    """
    dir = path
    if join:
        dir = ' '.join(path)

    dir = os.path.normpath(dir)
    if not os.path.isabs(dir):
        currDir = os.getcwd()
        dir = os.path.join(currDir, dir)

    return dir

def makeComments(grades, root):
    """
    Creates the comments.txt file for each student submission.

    This utilizes the comments section from the rubrics to create the
    corresponding file for each student in the list.

    Parameters:
    ----------
    grades:
        The list of all the rubrics of all the students.
    root:
        The root containing the student directories.
    """
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
    """
    Populates the connex generated CSV file with the grades of all students.

    Parameters:
    ----------
    grades:
        The list of rubrics for each student.
    root:
        The directory containing the student submissions and the CSV file.
    """
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
    """
    Reads the provided ini file and obtains all the details.

    Parameters:
    ----------
    path:
        The path to the ini file.
    """
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

    # Now make the Marker depending on the language that we are using.
    # TODO: if more languages are needed, this needs to be replaced with a 
    # dynamic loading of modules.
    conf.language = config['Language']['name']
    if conf.language == 'java':
        marker = JavaMarker()
    elif conf.language == 'python':
        marker = PythonMarker()
    else:
        print("Error: language is not supported yet.")
        return

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

    # The Aux section is also optional.
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
    """
    Creates a sample ini file for the user.
    """
    with open('sample.ini', 'w+') as file:
        sample = """
# This is a sample config file for the marking script. You may use this
# as a template to build your own config files.
# Please note that all attributes (save those under the [Rubric] section
# are reserved keywords).
# Lines that start with \'#\' are comments.

[Config]
# Specifies the root directory of the assignments.
root = path/to/root
# If true, the script will populate the CSV file with the marks.
makeCSV = true
# If true, the script will generate the comments files for all students.
makeComments = true

[Editor]
# Specify the executable path of the editor of choice.
editor = gvim.
# If your editor requires additional arguments, specify them with
# editorArgs = args

[Language]
# This specifies the language. Currently only Java and Python are
# supported. Please use either \'java\' or \'python\'.
name = java

# The IO section is optional. Only add this if the assignments require
# user input and/or you wish to use the diff functionality of the
# script.
[IO]
# The list of files containing the user input for the programs. They
# must have the same name as the file they are to be used with. Multiple
# files are separated with a semicolon.
input = /path/to/file1;/path/to/file2
# The list of files containing the master output to perform the diff. If
# diff is set to true, these must be given. As before, the files must
# have the same name as the file that they are to be used with.
output = /path/to/file1;/path/to/file2
# Tells the script whether a diff should be performed between the
# student's output and the provided master.
diff = true

# The Aux section is also optional. Add this if the assignment requires:
# additional instructor provided files (either code or files the
# students can load), or if a pre-processing script needs to be run
# prior to testing of the student submission.
[Aux]
# The list of additional files. These will be simply copied every time
# a new student's submission is evaluated.
files = /path/to/file1;/path/to/file2
# If a pre-processing script is required, specify it here.
script = /path/to/script

[Rubric]
# This is the marking rubric. Each item goes in a separate line, and it
# must be assigned to the maximum number of marks per item.
item 1 = 1
item 2 = 2
        """
        file.write(sample)

def main():
    """
    Main function of the program.
    """
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

    # Before we get started, let's switch the directory to the one that holds
    # the ini file.
    newPath = os.path.dirname(configPath)
    os.chdir(newPath)

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
            os.remove(file.path)


if __name__ == '__main__':
    main()

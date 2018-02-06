import argparse
import os
import time
import csv
import traceback
import configparser
from subprocess import Popen, PIPE
from copy import deepcopy
from pathlib import Path
from os.path import basename

class Config:
    def __init__(self):
        self.root = ''
        self.makeCSV = False
        self.makeComments = False

class Editor:
    def __init__(self):
        self.cmd = ''
        self.args = []

    def run(self, files):
        editorProc = Popen([self.cmd] + [self.args] + files)
        editorProc.communicate()

class Rubric:
    def __init__(self):
        self.studentName = ''
        self.attributes = {}
        self.maxVals = []
        self.total = 0
        self.comments = ''

    def make(self, rubric):
        self.studentName = rubric.studentName
        self.attributes = deepcopy(rubric.attributes)
        self.maxVals = deepcopy(rubric.maxVals)
        self.total = rubric.total
        self.comments = rubric.comments

    def addMarks(self):
        for item, mark in self.attributes.items():
            self.total += mark

class Marker:
    def __init__(self):
        self.extension = ''
        self.isInterpreted = False
        self.compiler = ''
        self.run = ''
        self.editor = Editor()
        self.inputFiles = ''
        self.outputFiles = ''
        self.diff = False

    def convertByteString(self, bytes):
        decoded = False
        # Try to decode as utf-8.
        try:
            bytes = bytes.decode('utf-8', 'backslashreplace')
            decoded = True
        except:
            pass

        if decoded:
            # Remove any Windows newlines.
            bytes = bytes.replace('\r\n', '\n')

        return bytes

    def compileFile(self, name):
        # Run the compiler on the given file and grab its stdout, stdin, stderr,
        # and its return code.
        compileProc = Popen([self.compiler, name], stdout = PIPE,
                            stdin = PIPE, stderr = PIPE)
        compileOut, compileErr = compileProc.communicate()
        compileCode = compileProc.returncode

        compileOut = self.convertByteString(compileOut)
        compileErr = self.convertByteString(compileErr)

        return compileCode, compileErr, compileOut

    def runFile(self, name, args = ''):
        runProc = Popen([self.run, name], stdout = PIPE, stdin = PIPE, 
                        stderr = PIPE)
        # Check if there is an input file that needs to be used.
        inputFile = ''
        for file in self.inputFiles:
            fName = os.path.splitext(basename(file))[0]
            if fName == name:
                inputFile = file
                break

        if inputFile:
            with open(inputFile, 'r') as inFile:
                inLines = inFile.read()
                inLines = str.encode(inLines)
                runOut, runErr = runProc.communicate(input = inLines)
        else:
            runOut, runErr = runProc.communicate()

        runCode = runProc.returncode
        runOut = self.convertByteString(runOut)
        runErr = self.convertByteString(runErr)
        return runCode, runErr, runOut

    def parseSubmission(self, submission, args = ''):
        outFilename = 'out.txt'
        fileList = []

        # Grab all the files that have the required extensions and compile
        # them.
        for entry in submission[-1]:
            if self.extension not in entry.name:
                continue

            fileList.append(entry.name)
            if not self.isInterpreted:
                compileCode, compileErr, compileOut = self.compileFile(entry.name)
                if compileCode is 0:
                    name = entry.name[:-len(self.extension)]
                    # Note that we currently do not handle multiple input
                    # files per file of code. Coming soon... I hope.
                    runCode, runErr, runOut = self.runFile(name, args)

                if os.path.exists(outFilename):
                    mode = 'a'
                else:
                    mode = 'w'

                with open(outFilename, mode, newline = '\n') as outFile:
                    if compileCode is not 0:
                        outFile.write('#=============================#\n')
                        outFile.write('# File: {}\n'.format(entry.name))
                        outFile.write('#=============================#\n')
                        outFile.write('For file{}:\n'.format(entry.name))
                        outFile.write(
                            'Compilation error: return code {}\n\n'.format(
                                compileCode))
                        outFile.write('#=============================#\n')
                        outFile.write('# stderr\n')
                        outFile.write('#=============================#\n')
                        outFile.write('{}\n\n'.format(compileErr))
                        outFile.write('#=============================#\n')
                        outFile.write('# stdout\n')
                        outFile.write('#=============================#\n')
                        outFile.write('{}\n\n'.format(compileOut))
                    else:
                        outFile.write('#=============================#\n')
                        outFile.write('# File: {}\n'.format(entry.name))
                        outFile.write('#=============================#\n')
                        outFile.write('For file{}:\n'.format(entry.name))
                        outFile.write('Compilation successful\n\n')
                        outFile.write('Program return code: {}\n'.format(runCode))
                        outFile.write('#=============================#\n')
                        outFile.write('# stderr\n')
                        outFile.write('#=============================#\n')
                        outFile.write('{}\n\n'.format(runErr))
                        outFile.write('#=============================#\n')
                        outFile.write('# stdout\n')
                        outFile.write('#=============================#\n')
                        outFile.write('{}\n\n'.format(runOut))
            else:
                print('Error: we currently do not support interpeted languages')
                return

        fileList.append(outFilename)
        return fileList

    def formatForCSV(self, table, rubric):
        # First make the header.
        header = ['Student']
        for item in rubric.attributes:
            header.append(item)

        header.append('Total')
        header.append('Comments')

        grades = []
        for entry in table:
            row = []
            row.append(entry.studentName)
            for item, num in entry.attributes.items():
                row.append(num)
            row.append(entry.total)
            row.append(entry.comments)
            grades.append(row)

        return header, grades


    def writeIncremental(self, table, rubric, rootDir):
        header, grades = self.formatForCSV(table, rubric)
        csvFile = os.path.join(rootDir, 'grades_inc.csv')
        with open(csvFile, 'w+', newline = '\n') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(grades)

    def loadIncremental(self, file, masterRubric):
        count = 0
        table = []
        with open(file, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            for line in reader:
                count += 1
                rubric = Rubric()
                rubric.make(masterRubric)
                for i in range(1, len(header) - 2):
                    rubric.attributes[header[i]] = float(line[i])
                rubric.comments = line[-1]
                rubric.total = float(line[-2])
                rubric.studentName = line[0]
                table.append(rubric)
        return table, count

    def mark(self, rootDir, rubric, args = ''):
        table = []

        # Check if we have a partial file already.
        incPath = os.path.join(rootDir, 'grades_inc.csv')
        incFile = Path(incPath)
        start = 0
        if incFile.is_file():
            table, start = self.loadIncremental(incFile, rubric)

        count = 0
        for entry in os.scandir(rootDir):
            if not entry.is_dir():
                continue
            if start is not 0:
                start -= 1
                continue

            name = entry.name
            subPath = os.path.join(entry.path, 'Submission attachment(s)')
            submission = [file for file in os.scandir(subPath) if file.is_file()]
            bundle = [submission]
            os.chdir(subPath)

            try:
                list = self.parseSubmission(bundle)
            except Exception as e:
                print('Error in entry{}'.format(count))
                print('Path: {}'.format(subPath))
                print(traceback.format_exc())
                self.writeIncremental(table, rubric, rootDir)
                continue

            # Now make the file that contains the marking rubric.
            with open('rubric.txt', 'w+') as rubricFile:
                i = 0
                for item, mark in rubric.attributes.items():
                    rubricFile.write('{}: {}/{}\n'.format(item, mark, 
                                                          rubric.maxVals[i]))
                rubricFile.write('#==============================#\n')
                rubricFile.write('# Instructor comments\n')
                rubricFile.write('#==============================#\n')
                rubricFile.write('')

            list.append('rubric.txt')
            self.editor.run(list)

            # The grader has now entered the grades and comments, so lets
            # re-open the file and update the marks.
            studentRubric = Rubric()
            studentRubric.make(rubric)
            studentRubric.studentName = name
            with open('rubric.txt', 'r+') as rubricFile:
                header = 0
                comments = []
                for line in rubricFile:
                    if line.startswith('#'):
                        header += 1
                        continue
                    if header is 3:
                        comments.append(line)
                        continue

                    tokens = line.split(':')
                    item = tokens[0]
                    vals = tokens[1].split('/')
                    studentRubric.attributes[item] = float(vals[0])

            comments = ' '.join(comments)
            studentRubric.comments = comments
            studentRubric.addMarks()
            table.append(studentRubric)
            self.writeIncremental(table, rubric, rootDir)
            os.remove('rubric.txt')
            os.remove('out.txt')

            # Check if we need to remove anything else from the student 
            # directory.
            deleteFiles = [file for file in os.scandir(subPath) if file.is_file()]
            fileNames = [entry.name for entry in submission]
            for file in deleteFiles:
                if file.name in fileNames:
                    continue
                os.remove(file)

        return table

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

    # Now let's read in the editor
    editor = Editor()
    editor.cmd = config['Editor']['editor']
    editor.args = config['Editor']['editorArgs']

    # Now make the Marker
    marker = Marker()
    marker.extension = config['Language']['extension']
    marker.isInterpreted = config['Language'].getboolean('isInterpreted')
    marker.compiler = config['Language']['compiler']
    marker.run = config['Language']['run']
    marker.editor = editor

    inFiles = config['IO']['input']
    inFiles = inFiles.split(';')
    inf = []
    for file in inFiles:
        inf.append(convertPaths(file))

    outFiles = config['IO']['output']
    outFiles = outFiles.split(';')
    out = []
    for file in outFiles:
        out.append(convertPaths(file))

    marker.inputFiles = inf
    marker.outputFiles = out
    marker.diff = config['IO'].getboolean('diff')

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
        path = os.path.join(conf.root, 'grades_inc.csv')
        os.remove(path)



if __name__ == '__main__':
    main()

import argparse
import os
import time
import csv
import traceback
from subprocess import Popen, PIPE
from copy import deepcopy
from pathlib import Path

class Marker:
    def __init__(self):
        self.fileExtension = '.java'
        self.compiler = 'javac'
        self.run = 'java'
        self.editor = 'gvim'
        self.editorArgs = ['-o']
        self.isInterpreted = False

    def compileFile(self, name):
        compileProc = Popen([self.compiler, name], stdout = PIPE, 
                            stdin = PIPE, stderr = PIPE)
        compileOut, compileErr = compileProc.communicate()
        compileCode = compileProc.returncode
        compileOut = compileOut.decode('utf-8', 'backslashreplace').replace(
            '\r\n', '\n')
        compileErr = compileErr.decode('utf-8', 'backslashreplace').replace(
            '\r\n', '\n')
        return compileCode, compileErr, compileOut

    def runFile(self, name, args = ''):
        runProc = Popen([self.run, name], stdout = PIPE, stdin = PIPE, stderr = PIPE)
        runOut, runErr = runProc.communicate(input = str.encode(args))
        runCode = runProc.returncode
        runOut = runOut.decode('utf-8', 'backslashreplace').replace('\r\n', '\n')
        runErr = runErr.decode('utf-8', 'backslashreplace').replace('\r\n', '\n')
        return runCode, runErr, runOut


    def parseBundle(self, bundle, args = ''):
        outFilename = 'out.txt'
        fileList = []

        # Grab all the files that have the required extension and compile them.
        for entry in bundle[-1]:
            if self.fileExtension not in entry.name:
                continue

            fileList.append(entry.name)
            if not self.isInterpreted:
                compileCode, compileErr, compileOut = self.compileFile(entry.name)
                if compileCode is 0:
                    name = entry.name[:-5]
                    runCode, runErr, runOut = self.runFile(name)

                if os.path.exists(outFilename):
                    mode = 'a'
                else:
                    mode = 'w'

                with open(outFilename, mode, newline = '\n') as outFile:
                    if compileCode is not 0:
                        # We know a compilation error occurred.
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

        fileList.append(outFilename)
        return fileList

    def formatForCSV(self, table, rubric, sTable = ''):
        # Check if we have to load in a table that maps the students names.
        studentMap = {}
        if sTable:
            with open(sTable, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    studentMap[row[1]] = row[0]

        # First make the header.
        header = ['Student ID']
        for item in rubric:
            header.append(item)

        header.append('Total')
        header.append('Comments')

        grades = []
        for name, mark in table.items():
            row = []
            if studentMap:
                name = name.split('(')[0]
                row.append(studentMap[name])
            else:
                row.append(name)
            total = 0
            for item, num in mark[0].items():
                row.append(num[0])
                total += num[0]
            row.append(total)
            row.append(mark[1])
            grades.append(row)

        return header, grades

    def incrementalWrite(self, table, rubric, rootDir):
        header, grades = self.formatForCSV(table, rubric)
        csvFile = os.path.join(rootDir, 'grades_inc.csv')

        with open(csvFile, 'w+', newline = '\n') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(grades)

    def loadIncrementalFile(self, file, masterRubric):
        count = 0
        table = {}
        with open(file, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            for line in reader:
                count += 1
                rubric = {}
                for i in range(1, len(header) - 2):
                    maxVal = masterRubric[header[i]][1]
                    rubric[header[i]] = [float(line[i]), maxVal]
                comments = line[-1]
                table[line[0]] = [rubric, comments]

        return table, count

    def mark(self, rootDir, rubric, args = '', studentTable = ''):
        table = {}
        # Check if we have a partial file already.
        incPath = os.path.join(rootDir, 'grades_inc.csv')
        incFile = Path(incPath)
        start = 0
        if incFile.is_file():
            # We do, so let's count the number of lines in the file.
            table, start = self.loadIncrementalFile(incFile, rubric)

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
                list = self.parseBundle(bundle, args)
            except Exception as e:
                print('Error in entry {}.'.format(count))
                print('Path: {}'.format(subPath))
                print(traceback.format_exc())
                self.incrementalWrite(table, rubric, rootDir)
                continue

            # Now make the file that contains the marking rubric.
            with open('rubric.txt', 'w+') as rubricFile:
                for item, mark in rubric.items():
                    rubricFile.write('{}: {}/{}\n'.format(item, mark[0], 
                                                          mark[1]))
                rubricFile.write('#==============================#\n')
                rubricFile.write('# Instructor comments\n')
                rubricFile.write('#==============================#\n')
                rubricFile.write('')

            list.append('rubric.txt')
            editorProc = Popen([self.editor] + self.editorArgs + list)
            editorProc.communicate()

            # The grader has now entered the grades and comments, so lets 
            # re-open the file and update the marks.
            studentRubric = deepcopy(rubric)
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
                    studentRubric[item][0] = float(vals[0])

            comments = ' '.join(comments)

            table[name] = [studentRubric, comments]
            self.incrementalWrite(table, rubric, rootDir)
            os.remove('rubric.txt')
            os.remove('out.txt')

        return self.formatForCSV(table, rubric, studentTable)

def readRubric(filename):
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
            if not line.strip():
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

def makeSampleRubric():
    file = open('sample_rubric.txt', 'w+')
    file.write('# Lines that begin with \'#\' will be ignored as comments.\n')
    file.write('# Enter a single item per line, with the following syntax: \n')
    file.write('# <item_name>: /<max_val>\n')
    file.write('# Below are some examples.\n')
    file.write('compiles: /1\n')
    file.write('runs: /1\n')
    file.write('output: /4\n')
    file.close()

def convertPaths(path, join = False):
    dir = path
    if join:
        dir = ' '.join(path)

    dir = os.path.normpath(dir)

    if not os.path.isabs(dir):
        currDir = os.getcwd()
        dir = os.path.join(currDir, dir)

    return dir

def printSummary(dir):
    outName = os.path.join(dir, 'summary.txt')
    csvName = os.path.join(dir, 'grades.csv')
    csvPath = Path(csvName)
    if not csvPath.is_file():
        print('Error: A summary can only be generated once all assignments are'
              ' graded')
        return

    with open(outName, 'w+', newline = '\n') as outFile:
        with open(csvPath, 'r') as csvFile:
            reader = csv.reader(csvFile)
            header = next(reader)
            for line in reader:
                outFile.write('#==============================#\n')
                for i in range(len(header)):
                    outFile.write('{}: {}\n'.format(header[i], line[i]))
                outFile.write('\n')

def main():
    parser = argparse.ArgumentParser(description = 
                                     'Marks assignments in an automatic way')
    parser.add_argument('-g', '--generate-rubric', action = 'store_true',
                        dest = 'gen', default = False, 
                        help = 'Generate a sample marking rubric')
    parser.add_argument('-d', '--dir', action = 'store', type = str, 
                        dest = 'dir', nargs = '+',
                        help = 'The root directory of the assignments')
    parser.add_argument('-r', '--rubric', action = 'store', type = str, 
                        dest = 'rubric',
                        help = 'The grading rubric to use')
    parser.add_argument('-t', '--student-table', action = 'store', type = str,
                        dest = 'table', default = '',
                        help = 'A table that maps names to some ID')
    parser.add_argument('-s', '--summary', action = 'store_true', 
                       dest = 'summary', default = False,
                       help = 'Generate a read-friendly summary of grades')

    args = parser.parse_args()

    # First things first, check if we have to generate the sample rubric.
    if args.gen == True:
        makeSampleRubric()
        return

    if args.dir == None:
        return

    if args.summary:
        printSummary(convertPaths(args.dir, True))
        return

    if args.rubric == None:
        print('Please provide a marking rubric to use.')
        return

    # If we hit this point, then we have everything we need, so let's get
    # started by first parsing the rubric and getting back the list of things  
    # we have to grade.
    rubric = readRubric(args.rubric)
    if not rubric:
        return

    # Let's first make the path for the root directory a path
    dir = convertPaths(args.dir, True)

    
    tablePath = args.table
    if tablePath:
        tablePath = convertPaths(tablePath)

    startTime = time.time()
    marker = Marker()
    marker.editorArgs = []
    header, grades = marker.mark(dir, rubric, studentTable = tablePath)
    elapsed = time.time() - startTime
    m, s = divmod(elapsed, 60)
    h, m = divmod(m, 60)
    print('Total grading time %d:%02d:%02d' % (h, m, s))

    # Last thing that needs to get done is to save the grades to a CSV file.
    csvFile = os.path.join(dir, 'grades.csv')
    with open(csvFile, 'w+', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(grades)


if __name__ == '__main__':
    main()

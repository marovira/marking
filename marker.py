import os
import csv
import traceback
import shutil
from subprocess import Popen, PIPE
from pathlib import Path
from os.path import basename
from utils import Config, Editor, Rubric, Process
import difflib

class Marker:
    def __init__(self):
        self.extension = ''
        self.generatedExtension = ''
        self.isInterpreted = False
        self.compiler = ''
        self.run = ''
        self.editor = Editor()
        self.inputFiles = ''
        self.runArgs = []
        self.outputFiles = ''
        self.diff = False
        self.workingDir = ''
        self.preProcessScript = ''
        self.auxFiles = []

    def convertByteString(self, bytes):
        decoded = False

        # Try to decode as utf-8
        try:
            bytes = bytes.decode('utf-8', 'backslashreplace')
            decoded = True
        except:
            pass

        if decoded:
            bytes = bytes.replace('\r\n', '\n')

        return bytes

    def compileFile(self, name):
        compileProc = Popen([self.compiler, name], stdout = PIPE,
                stdin = PIPE, stderr = PIPE)
        compileOut, compileErr = compileProc.communicate()
        compileCode = compileProc.returncode

        compileOut = self.convertByteString(compileOut)
        compileErr = self.convertByteString(compileErr)

        return compileCode, compileErr, compileOut

    def runFile(self, name):
        runProc = Popen([self.run, name] + [self.runArgs], stdout = PIPE, 
                stdin = PIPE, stderr = PIPE)
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

    def performDiff(self, expected, ans):
        d = difflib.Differ()
        diff = list(d.compare(expected, ans))
        if len(diff) != len(expected):
            return 1, diff
        return 0, []

    def runSubmission(self, submission):
        summaryFile = 'summary.txt'
        fileList = []

        for entry in submission[-1]:
            if self.extension not in entry.name:
                continue
            fileList.append(entry.name)

            if not self.isInterpreted:
                compileCode, compileErr, compileOut = self.compileFile(
                        entry.name)
                if compileCode is 0:
                    name = entry.name[:-len(self.extension)]
                    # TODO: Add support for multiple input files.
                    runCode, runErr, runOut = self.runFile(name)

                    diffResult = []
                    diffCode = -1
                    if runCode is 0 and self.diff:
                        # First load in the output file.
                        outFile = ''
                        for file in self.outputFiles:
                            fName = os.path.splitext(basename(file))[0]
                            sName = os.path.splitext(basename(entry.name))[0]
                            if fName == sName:
                                outFile = file
                                break

                        if outFile:
                            with open(outFile, 'r') as oFile:
                                master = oFile.readlines()
                            student = runOut.splitlines(keepends = True)

                            diffCode, diffResult = self.performDiff(master, 
                                                                    student)

                if os.path.exists(summaryFile):
                    mode = 'a'
                else:
                    mode = 'w'

                with open(summaryFile, mode, newline = '\n') as sFile:
                    sFile.write('#=========================================#\n')
                    sFile.write('# Summary for file {}\n'.format(entry.name))
                    sFile.write('#=========================================#\n')

                    if compileCode is not 0:
                        sFile.write('Compilation error: return code {}\n'.format(
                            compileCode))
                        sFile.write('{}\n\n'.format(compileErr))
                        sFile.write('{}\n\n'.format(compileOut))
                    else:
                        sFile.write('Compilation successful\n')
                        sFile.write('Program return code: {}\n\n'.format(runCode))

                        if runCode is 0:
                            if self.diff:
                                if diffCode is 0:
                                    sFile.write(
                                        'Diff results: outputs are identical.\n\n')
                                elif diffCode is -1:
                                    sFile.write('Could not perform diff.\n\n')
                                else:
                                    sFile.write('Diff results:\n')
                                    sFile.write('Legend:\n')
                                    sFile.write('-: expected\n')
                                    sFile.write('+: received\n')
                                    sFile.write('?: diff results\n\n')
                                    sFile.writelines(diffResult)
                                    sFile.write('\n')
                            else:
                                sFile.write('# Output for {}\n'.format(
                                    entry.name))
                                sFile.write('#=============================#\n')
                                sFile.write('stdout:\n{}\n\n'.format(runOut))
                                sFile.write('#=============================#\n')
                                sFile.write('stderr:\n{}\n\n'.format(runErr))
                        else:
                            sFile.write('# Output for {}\n'.format(entry.name))
                            sFile.write('#=============================#\n')
                            sFile.write('stdout:\n{}\n\n'.format(runOut))
                            sFile.write('#=============================#\n')
                            sFile.write('stderr:\n{}\n\n'.format(runErr))
            else:
                # TODO: Add support for interpreted languages.
                print('Error: interpreted languages are not supported yet.')
                return
        fileList.append(summaryFile)
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

    def writeIncremental(self, table, rubric):
        header, grades = self.formatForCSV(table, rubric)
        csvFile = os.path.join(self.workingDir, 'grades_inc.csv')
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

    def mark(self, rootDir, rubric):
        table = []

        # Check if we have a partial file already.
        incPath = os.path.join(self.workingDir, 'grades_inc.csv')
        incFile = Path(incPath)
        start = 0
        if incFile.is_file():
            table, start = self.loadIncremental(incFile, rubric)

        # Next, check copy over any input and output files to the working
        # directory.
        for file in self.inputFiles:
            shutil.copy2(file, self.workingDir)

        for file in self.outputFiles:
            shutil.copy2(file, self.workingDir)

        for file in self.auxFiles:
            shutil.copy2(file, self.workingDir)

        if self.preProcessScript:
            shutil.copy2(self.preProcessScript, self.workingDir)

        count = 0
        for entry in os.scandir(rootDir):
            if not entry.is_dir():
                continue
            if start is not 0:
                start -= 1
                continue

            name = entry.name
            subPath = os.path.join(entry.path, 'Submission attachment(s)')
            submission = [file for file in os.scandir(subPath) if
                    file.is_file()]
            bundle = [submission]

            # Now copy the submission over to the working directory.
            for file in submission:
                shutil.copy2(file, self.workingDir)

            os.chdir(self.workingDir)

            # Check if we have to run anything before.
            if self.preProcessScript:
                proc = Process()
                proc.procName = 'python'
                proc.procArgs = [self.preProcessScript]
                proc.run()

            try:
                list = self.runSubmission(bundle)
            except Exception as e:
                print('Error in entry {}'.format(count))
                print('Path: {}'.format(subPath))
                print(traceback.format_exc())
                self.writeIncremental(table, rubric)
                continue

            with open('rubric.txt', 'w+') as rubricFile:
                i = 0
                for item, mark in rubric.attributes.items():
                    rubricFile.write('{}: {}/{}\n'.format(item, mark,
                        rubric.maxVals[i]))
                    i += 1
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
            self.writeIncremental(table, rubric)
            try:
                os.remove('rubric.txt')
            except:
                pass

            try:
                os.remove('summary.txt')
            except:
                pass

            for file in list:
                if file == 'rubric.txt' or file == 'summary.txt':
                    continue
                os.remove(file)

            # Now remove any generated files.
            for file in os.scandir(self.workingDir):
                if not file.is_file():
                    continue
                if self.generatedExtension not in file.name:
                    continue
                os.remove(file)

            print('Done')

        return table

import os
import glob
from subprocess import Popen, PIPE

extension = '.java'
compiler = 'javac'
run = 'java'
editor = 'gvim'
editorArgs = ['-o']

def parseBundle(bundle):
    outFilename = 'out.txt'
    fileList = []
    # Grab all of the files that have the required extension and compile them.
    for entry in bundle[-1]:
        if extension not in entry.name:
            continue
        fileList.append(entry.name)
        # Compile the file.
        compileProc = Popen([compiler, entry.name], stdout = PIPE, 
                            stdin = PIPE, stderr = PIPE)
        compileOut, compileErr = compileProc.communicate()
        compileCode = compileProc.returncode
        compileOut = compileOut.decode('ascii').replace('\r\n', '\n')
        compileErr = compileErr.decode('ascii').replace('\r\n', '\n')

        # We only attempt to run things if the compilation was successful.
        if compileCode is 0:
            name = entry.name[:-5]
            runProc = Popen([run, name], stdout = PIPE, stdin = PIPE, 
                            stderr = PIPE)
            runOut, runErr = runProc.communicate()
            runCode = runProc.returncode
            runOut = runOut.decode('ascii').replace('\r\n', '\n')
            runErr = runErr.decode('ascii').replace('\r\n', '\n')

        # Select which mode of opening we need.
        if os.path.exists(outFilename):
            mode = 'a'
        else:
            mode = 'w'

        with open(outFilename, mode, newline = '\n') as outFile:
            if compileCode is not 0:
                # We know a compilation error occurred.
                outFile.write('For file {}:\n'.format(entry.name))
                outFile.write('Compilation error: return code {}\n'.format(
                    compileCode))
                outFile.write('STDERR:\n{}\n'.format(compileErr))
                outFile.write('STDOUT:\n{}\n'.format(compileOut))
                outFile.write('\n')
            else:
                # Everything went fine, so just output the result of running
                # the program.
                outFile.write('For file {}:\n'.format(entry.name))
                outFile.write('Compilation successful.\n')
                outFile.write('Compiler stdout:\n{}\n'.format(compileOut))
                outFile.write('Compiler stderr:\n{}\n'.format(compileErr))
                outFile.write('\n')
                outFile.write('Program return code: {}\n'.format(runCode))
                outFile.write('Program stdout:\n{}\n'.format(runOut))
                outFile.write('Program stderr:\n{}\n'.format(runErr))
                outFile.write('\n')

    fileList.append(outFilename)
    return fileList

def formatForCSV(table, rubric):
    # First, prepare the header.
    header = ['Student V#']
    for item in rubric:
        header.append(item)

    grades = []
    for name, mark in table.items():
        row = []
        row.append(name)
        for item, num in mark.items():
            row.append(num[0])
        grades.append(row)

    return header, grades


    # We need a way of changing the student name to V#.
    #for name, mark in table.items():



def grade(rootDir, rubric):
    i = 0
    table = {}
    for entry in os.scandir(rootDir):
        if not entry.is_dir():
            continue
        if i is not 0:
            break

        name = entry.name
        subPath = os.path.join(entry.path, 'Submission attachment(s)')
        submission = [file for file in os.scandir(subPath) if file.is_file()]
        bundle = [submission]

        os.chdir(subPath)
        list = parseBundle(bundle)

        # Now we need to create the file that contains the marking rubric.
        with open('rubric.txt', 'w+') as rubricFile:
            for item, mark in rubric.items():
                rubricFile.write('{}: {}/{}\n'.format(item, mark[0], mark[1]))

        # Finally, we open all of the files in the text editor (for now Vim).
        list.append('rubric.txt')
        editorProc = Popen([editor] + editorArgs + list)
        editorProc.communicate()

        # The grader has now entered the grades into the rubric file, so let's
        # re-open it and update the marks.
        with open('rubric.txt', 'r+') as rubricFile:
            for line in rubricFile:
                tokens = line.split(':')
                item = tokens[0]
                vals = tokens[1].split('/')
                newVal = vals[0]
                rubric[item][0] = int(newVal)

        # We now have the updated marks, so all that we have left to do
        # is store this in a dictionary with the marks for each student.
        table[name] = rubric

        # Finally, lets clean up after ourselves.
        os.remove('rubric.txt')
        os.remove('out.txt')
        i = i + 1

    return formatForCSV(table, rubric)
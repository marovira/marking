"""
Utility module containing classes used by the main marking module.
"""

import os
from subprocess import Popen, PIPE
from copy import deepcopy

class Process:
    """
    Serves as a wrapper for the logic of Popen.

    Attributes
    ----------
    procName:
        The name of the process (executable) to run.
    procArgs: 
        The list of arguments that the process specified in procArgs takes.
    """
    def __init__(self):
        self.procName = ''
        self.procArgs = []

    def run(self):
        """
        Invokes Popen with the process and arguments specified in procName and
        procArgs.

        Note
        ----
        This does not pipe stdout, stdin, or stderr, nor does it give the return
        code from the process. 
        """
        proc = Popen([self.procName] + self.procArgs)
        proc.communicate()

    def runPiped(self, input = None):
        """
        Invokes Popen with the process and arguments specified in procName and
        procArgs with pipes.

        This function captures stdout, stderr, and stdin for the process and
        returns them (in raw byte string form) along with the return code.

        Parameters
        ----------
        input:
            The input for the process (if any).
        """
        proc = Popen([self.procName] + self.procArgs, stdout = PIPE, stdin =
                PIPE, stderr = PIPE)
        procOut, procErr = proc.communicate(input)
        procCode = proc.returncode
        return procOut, procErr, procCode

class Config:
    """
    A place-holder for all the configuration options of the main marking script.

    Attributes
    ----------
    root:
        The root directory of the assignments.
    makeCSV:
        Whether to write the resulting marks to the connex formatted CSV file.
    makeComments:
        Whether to write the comment files for each student.
    workingDir:
        The working directory for the script.
    language:
        The language in which the assignments are written (currently one of
        Java or Python).
    """

    def __init__(self):
        self.root = ''
        self.makceCSV = False
        self.makeComments = False
        self.workingDir = ''
        self.language = ''

class Editor:
    """
    A wrapper for the editor process.

    Since the code needs to be inspected, this wraps the usage of Process on the
    specific case of the text editor.

    Attributes
    ----------
    cmd:
        The name of the text editor executable.
    args:
        The arguments for the text editor.
    """

    def __init__(self):
        self.cmd = ''
        self.args = []

    def run(self, files):
        """
        Executes the text editor process with the given files.

        Parameters
        ----------
        files:
            The list of files with which to run the text editor.
        """
        proc = Process()
        proc.procName = self.cmd
        proc.procArgs = self.args + files
        proc.run()

class Rubric:
    """
    Holds the grading rubric.

    Attributes
    ----------
    studentName:
        The name of the current student.
    attributes:
        The elements of the marking rubric.
    maxVals:
        The maximum values of each element of the marking rubric.
    total:
        The total mark for the student.
    comments:
        The instructor's comments for the student.
    """
    def __init__(self):
        self.studentName = ''
        self.attributes = {}
        self.maxVals = []
        self.total = 0
        self.comments = ''

    def make(self, rubric):
        """
        Performs a deep copy of the provided rubric.

        Parameters
        ----------
        rubric:
            The source rubric to copy from.
        """
        self.studentName = rubric.studentName
        self.attributes = deepcopy(rubric.attributes)
        self.maxVals = deepcopy(rubric.maxVals)
        self.total = rubric.total
        self.comments = rubric.comments

    def addMarks(self):
        """
        Computes the total mark for the student.
        """
        for item, mark in self.attributes.items():
            self.total += mark

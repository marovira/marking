import os
from subprocess import Popen, PIPE
from copy import deepcopy

class Process:
    def __init__(self):
        self.procName = ''
        self.procArgs = []

    def run(self):
        proc = Popen([self.procName] + self.procArgs)
        proc.communicate()

class Config:
    def __init__(self):
        self.root = ''
        self.makceCSV = False
        self.makeComments = False

class Editor:
    def __init__(self):
        self.cmd = ''
        self.args = []

    def run(self, files):
        proc = Process()
        proc.procName = self.cmd
        proc.procArgs = [self.args] + files
        proc.run()

class Rubric:
    def __init__(self):
        self.studentName = ''
        self.attributes = {}
        self.maxVals = []
        self.total = 0
        self.comments = ''

    def make(self, rubric):
        self.studentName = rubric.studentName
        self.attributes = rubric.attributes
        self.maxVals = deepcopy(rubric.maxVals)
        self.total = rubric.total
        self.comments = rubric.comments

    def addMarks(self):
        for item, mark in self.attributes.items():
            self.total += mark

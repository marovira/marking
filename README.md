# Marking v1.0
An automated marking script for grading programming assignments. Developed for
first year courses at UVic.

## What is it?
This script enables the marker to automate certain components of the process of
marking assignments while still allowing for manual code inspection. The script
is designed to automatically compile, run, capture output, and perform a diff
against a master output. The results are then written to a series of text files
and displayed in the text editor of choice. Once marking is done, the script
automatically generates the comments files as well as the grades file that can
then be uploaded to connex to be released to students.

## How does it work?
Please see the wiki for more information on usage of the script, along with
guidelines for designing assignments that can use it. The full documentation of
the source code can be seen [here](https://marovira.github.io/marking/)

## TODO list

* Allow for multiple input files per program (different testing cases) with
  their corresponding outputs for diff.

## How can I contribute?
There are currently two options for contributing to the script:

1. Send an email to [me](mailto:marovira@uvic.ca).
2. Submit a pull request for your change. Make sure that you take a look at the
   coding standards and general code structure prior to submission.

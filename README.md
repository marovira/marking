# marking
An automated marking script for CSc 110 at UVic.

Currently, the script supports the following:

* Easy script configuration using an ini file. The script can generate a sample
  file for reference.
* Automatic compilation, execution, and capturing of stdout of student
  submissions.
* Easy integration with command-line based text editors.
* Output to csv file.
* Capturing of instructor comments per student.
* Generates a summary file.
* Can convert student names to ids given a csv table.
* Can take pre-defined input to supply student submissions. Currently only one
  file of input is allowed.
* The script can now generate the appropriate csv and comments files that connex
  needs to set student grades and comments automatically.

Coming soon:
* Ability to automatically compare student output with a pre-defined master
  output (easy).
* Ability to supply multiple input files to a single student submission.
* Other features... maybe.

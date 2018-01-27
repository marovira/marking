import argparse
import os
import rubric as rubr
import examine as ex
import time
import csv

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

    args = parser.parse_args()

    # First things first, check if we have to generate the sample rubric.
    if args.gen == True:
        rubr.genSampleRubric()
        return

    if args.dir == None:
        return

    if args.rubric == None:
        print('Please provide a marking rubric to use.')
        return

    # If we hit this point, then we have everything we need, so let's get
    # started by first parsing the rubric and getting back the list of things
    # we have to grade.
    rubric = rubr.parseRubric(args.rubric)
    if not rubric:
        return

    # We now have the rubric parsed and ready to go, so let's dive into the
    # directories.
    dir = ' '.join(args.dir)
    dir = os.path.normpath(dir)

    if not os.path.isabs(dir):
        currDir = os.getcwd()
        dir = os.path.join(currDir, dir)

    startTime = time.time()
    header, grades = ex.grade(dir, rubric)
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

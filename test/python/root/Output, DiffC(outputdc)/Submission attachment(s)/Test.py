# First open the file.
print("Contents of file:")
with open('test.txt', 'r') as inFile:
    lines = inFile.readlines()
    for line in lines:
        print(line.rstrip())


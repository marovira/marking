# First open the file.
print("Some random text.")
print("contentS of File:")
with open('test.txt', 'r') as inFile:
    lines = inFile.readlines()
    for line in lines:
        print(line.rstrip())
print("Exiting...")

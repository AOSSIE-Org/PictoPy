import os

path = "tests/inputs"
lst = [os.getcwd() + "/" + x for x in os.listdir(path)]
print(lst)
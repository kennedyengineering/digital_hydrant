import os

path = os.path.dirname(os.path.realpath(__file__))
path = path.split("/")
del path[len(path)-1]
print(path)


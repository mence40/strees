from c45 import c45
import sys
import numpy as np

# TODO: Learn how to traverse a tree and classify data
def classify(tree, data):
  return []

args = sys.argv[1:]

tree = c45(args[0], args[1], args[2])

# starts out column wise
test_data = []

with open(args[3], 'r') as f:
  for line in f:
    test_data.append(line.split(","))
    
classifications = classify(tree, test_data)

condensed_labels = []

end = len(test_data) - 1

for i in range(len(test_data[0])):
  if test_data[end][i] == 1:
    condensed_lables.append(0)
  else:
    condensed_lables.append(1)
    
correct = 0
incorrect = 0

for i in range(len(classificaitons)):
  if classifications[i] == condensed_lables[i]:
    correct += 1
  else:
    incorrect += 1
    
    
print(correct)
print(incorrect)
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  


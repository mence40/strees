from c45 import c45
import sys

# TODO: Learn how to traverse a tree and classify data
def classify(tree, data):
  return []

# input/output samples path, depth, prep_atr
args = sys.argv[1:]

input_data = []
with open(args[0], 'r') as f:
  for line in f:
    input_data.append(line.split(","))
    
test_data = input_data[-2:]
input_data = input_data[:len(input_data) - 2]

tree = c45(input_data, args[1], args[2])
    
  
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

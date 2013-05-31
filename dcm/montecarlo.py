import random
import math

total = 200000
incircle = 0
for i in xrange(total):
    x = random.random()
    y = random.random()
    if math.sqrt(x**2+y**2) < 1: 
        incircle += 1
print 4*float(incircle)/total
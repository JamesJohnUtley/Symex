from z3 import *
from tqdm import tqdm
 
# Create the solver
s = Solver()
x = Int('x')
s.add(x > 30)

# test 1
# for i in tqdm(range(0,512), desc="Test 1"):
#     s.check()

for i in range(30,600):
    s.add(x != i)

# test 2
for i in tqdm(range(0,512), desc="Test 2"):
    s.check()
# Declare our variables: "pie_price", which we know the 
# value of, "num_pies", which we don't, and "pies_owing", which depends upon the values of the other two
# pie_price = Real('pie_price')
# num_pies = Int('num_pies')
# pies_owing = pie_price * num_pies
 
# # Assert that pie_price is equal to 3.14
# s.add(pie_price == 3.14)
 
# # Assert that pies_owing is greater than 10
# s.add(pies_owing > 10)
exit()

a = String('a')
b = String('b')
c = String('c')
s.add(a == 'ab')
s.add(b == 'cd')
s.add(c == a + b)
# s.add(pies_owing > 20)
# Ask if these these can be true at the same time
s.check() # returns "sat" - they can be!!
# for e in s:
#     print(e)
# print(s)
# m = s.model()
# for x in m:
#     print(f"x = {m[x]}")
if s.check() == sat:
    # Get simplified model
    model = s.model()
    print("Original Constraints:")
    print(s.assertions())
    print("Simplified Constraints:")
    print([simplify(c) for c in s.assertions()])
    print("Model:")
    print(model)
    print(model[a])
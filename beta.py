# beta.py is for smoothing out the code and making a final snippet
# alpha.p and beta.py are dynamic while final.py is static


from cs50 import SQL
from helpers import lookup

db = SQL("sqlite:///finance.db")


########################################################################################################################
class Solution:
    def twoSum(self, nums: List[int], target: int):
        okay = []
        for i in nums:
            for j in nums:
                x = i + j
                if x == target:
                    okay.append(i)
                    okay.append(j)
                    return okay

                    break
            print("nope")
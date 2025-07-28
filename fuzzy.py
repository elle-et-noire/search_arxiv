from rapidfuzz import fuzz

s1 = "apple"
s2 = "applr"
similarity = fuzz.ratio(s1, s2)
print(similarity)  # 例: 80.0
import re

def load_rules(file_path="rules.txt"):
    rules = {}
    with open(file_path, "r") as f:
        for line in f:
            rule, code = line.strip().split("->")
            rules[rule.strip()] = code.strip()
    return rules

def match_code(data, rules):
    for pattern, code in rules.items():
        if re.search(pattern, data):  # Use regex for pattern matching
            return code
    return "UNKNOWN"  # Default code if no match is found

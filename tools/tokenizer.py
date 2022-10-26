import random

def ReadBytes(preferred_values):
    lst = list(preferred_values)
    choice = random.choice(lst)
    print(f"Did read: {choice}")
    return choice


def getShortestStringLength(array):
    length = 10000
    for element in array:
        l = len(element)
        if l < length:
            length = l
    return length

def getToken(possible_tokens):
    shortest_string_length = getShortestStringLength(possible_tokens)
    preferred_values = set()

    for token in possible_tokens:
        preferred_values.add(token[:shortest_string_length])

    selection = ReadBytes(preferred_values)
    for token in possible_tokens:
        if token.startswith(selection):
            need = len(token) - shortest_string_length
            choice = token

    print(f"Did read {shortest_string_length} bytes still need to read {need} bytes!")
    missingBytes = choice[shortest_string_length:]
    ReadBytes([missingBytes])

    return selection

def main():
    possible_tokens = ["alp", "beta", "gamma"]
    token = getToken(possible_tokens)
    print(f"Next Token: {token}")


if __name__ == "__main__":
    main()
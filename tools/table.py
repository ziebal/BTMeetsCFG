import json

def getContent(o, mode=1):
    res = None
    try:
        if mode == 1:
            res = o["generation"]
        else:
            res = o["parsing"]
    except:
        return "Failed"
    res = res.split(" of ")
    return f"{int(100 * (int(res[0]) / int(res[1])))}\\%"

def main():
    with open("./result.json", "r") as f:
        result = json.load(f)

    index = 1
    for k, v in result.items():
        print(k , index)
        # print(f"Sample{index}.json & {getContent(v, 1)} & {getContent(v, 2)}\\\\")
        # print("\\hline")
        index += 1

if __name__ == "__main__":
    main()
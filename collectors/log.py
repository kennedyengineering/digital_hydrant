import datetime

# simple output formatting function, makes output look more professional

def log(string, error=False): 
    postfix = datetime.datetime.now()
    if error:
        prefix = "[ERROR] "
        prRed(prefix, end='')
    else:
        prefix = "[INFO] "
        prGreen(prefix, end='')
    print("{: <40} {: >20}".format(string, str(postfix)))

def prRed(skk, end="\n"): print("\033[91m {}\033[00m" .format(skk), end=end)
def prGreen(skk, end="\n"): print("\033[92m {}\033[00m" .format(skk), end=end)


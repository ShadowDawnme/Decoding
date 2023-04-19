from bs4 import BeautifulSoup as busp
import bs4
import requests
import connect_auxliary as gotcha
import math
import time
import concurrent.futures.thread as Thruser
import json
import os

"""
since this just a script, I wont build class to wrapper function
"""
header =gotcha.headers
mycookies = gotcha.cookies
EtherCloud = "https://etherscan.io/labelcloud"
Etherprefix = "https://etherscan.io"
Ethersuffix : str = "?subcatid={}&size=100&start={}"
alldict :dict = {}
Checkpoint : int = 1
Cpfile : str = ""

def Etherscan_labelWordCloud_geter(inputUrl : str):
    res = requests.get(url=inputUrl, headers=header, cookies= mycookies)
    result = busp(res.text, 'html.parser')
    time.sleep(1)
    return result

# special build due to Etherscan current structure
def number_counter(target : str):
    return int(target[target.index("(") + 1 : target.index(")") ])

def tester(links : str):
    # some labels contain sorted blocks and txs
    # here we would ignore it.
    targetSet : list = ["tokens", "accounts"]
    Elink = links.split("/")
    if Elink[1] not in targetSet: return True
    return False
    
def url_process(tags : bs4.BeautifulSoup, page : int):
    tagOne = tags.find_all("div", class_ = "card")
    if not tagOne: 
        return (False, page)
    tagOne = tagOne[-1]
    tag = tagOne.find_all("li", class_ = "nav-item")
    if not len(tag): return (False, page)
    values : list = [(element.find("a")["val"], number_counter(element.text)) for element in tag]
    page = 0
    for item in values:
        page += math.ceil(item[1]/100)
    return (values, page)

def reaptedProcess(Eurl : str, checkOne : list):
    subdict : dict = {}
    laberes = Etherscan_labelWordCloud_geter(Eurl)
    layerone = laberes.find_all('tbody')
    layertwo = None
    for interT in layerone:
        if len(interT.find_all("tr")):
            layertwo = interT.find_all("tr")
            break
    if layertwo is None:
        return subdict
    for item in layertwo:
        target = item.find("a").text
        # check point checker
        if target in checkOne: break
        # for accounts
        if item.find("i") == None:
            if not subdict.get("accounts") : subdict["accounts"] = []
            subdict["accounts"].append(target)
        # None accounts
        elif item.find("i"):
            try: name = item.find("i")["title"]
            except KeyError: name = "token/Contain Contracts"
            if not subdict.get(name): subdict[name] = []
            subdict[name].append(target) 
    return subdict

def LinkParser(eachlink : str, total : int):
    resultList : list = []
    finalRes : list = []
    webCounter = 0
    prePivot = 0
    # initial URLs
    URLs : list = [Etherprefix + eachlink + "?size=100"]
    laberes = Etherscan_labelWordCloud_geter(URLs[0])
    resultList = url_process(laberes, total)
    # we first get all corresponding urls
    for iteral in range(resultList[1]): 
        if resultList[1] <= 1: break
        # these if statements special built for currently Etherscan html design
        # if website has any changen, line with variable "resultList" should be checked first
        if not resultList[0]: URLs.append(Etherprefix + eachlink + Ethersuffix.format("undifined", (iteral+1) * 100))  
        elif isinstance(resultList[0], list):
            Eurl : str = ""
            if resultList[0][webCounter][1] > (iteral+1) * 100:
                Eurl = Etherprefix + eachlink + Ethersuffix.format(resultList[0][webCounter][0], (iteral-prePivot+1) * 100)
            else:
                webCounter += 1
                if webCounter >= len(resultList[0]): continue
                prePivot = iteral + 1
                Eurl = Etherprefix + eachlink + Ethersuffix.format(resultList[0][webCounter][0], (iteral-prePivot+1) * 100)
            URLs.append(Eurl)
    # using multithreading since we have lots of I/O operations
    with Thruser.ThreadPoolExecutor() as executor:
        results = [executor.submit(reaptedProcess, url, URLs) for url in URLs]
        finalRes = [eleE.result() for eleE in results]
    return finalRes
    
def EtherParser():
    labels : busp= Etherscan_labelWordCloud_geter(EtherCloud)
    outer = labels.find_all("div", class_ = "col-md-4 col-lg-3 mb-3 secondary-container")
    # goahead = 0
    for items in outer:
        lastMan : list = []
        layerOne : list = items.find_all("div")
        """
        in this step, you can use stence like:
        nextLayer = items.find_all("a") 
        to faster get correspondind link, but in there for beauty and establish of
        dict, we start from outer "div"
        """
        name : str = layerOne[0].find("span").text
        name = " ".join(name.split(" ")[ :-1])
        layerTwo = layerOne[1].find_all("a")
        alldict[name] = {layT.text : layT['href'] for layT in layerTwo}
        stuffs : dict = {}
        stuffs[name] = {}
        for total, eachlink in alldict[name].items():
            if tester(eachlink): continue
            total = math.ceil(number_counter(total)/100)
            Rts : list= LinkParser(eachlink, total)
            for Eitems in Rts:
                for eleK, eleV in Eitems.items():
                    if stuffs[name].get(eleK):  stuffs[name][eleK] = [*stuffs[name][eleK], *eleV]
                    else: stuffs[name][eleK] = eleV
                    # add lastest accounts/contracts in checkPoint
                    lastMan.append(eleV[0])
        with open("targetFile.json", "r+") as fp:
            data : list= json.load(fp=fp)
            if Checkpoint: 
                for keys, values in data[name]:
                    data[name][keys] = [*stuffs[name][keys], *values]
            else : data = {**data, **stuffs}
            # reset file pointer to position 0
            fp.seek(0)
            json.dump(data, fp, indent=4)

def CheckRead():
    with open("CheckPoint.json" , "r") as cp:
        files = json.load(fp=cp)
    return files

def CheckCreater():
    with open("CheckPoint.json", "w") as cp:
        json.dump({}, cp, indent=4)
    return

if __name__ == "__main__":
    if not os.path.exists("targetFile.json"):
        with open("targetFile.json", "w") as file:
            json.dump({}, file, indent=4)
    if not os.path.exists("CheckPoint.json"):
        Checkpoint = 0
        CheckCreater()
    else : Cpfile = CheckRead()
    EtherParser()
    
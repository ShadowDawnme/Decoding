from bs4 import BeautifulSoup as busp
import requests
import connect_auxliary as gotcha

"""
since this just a script, I wont build class to wrapper any function
"""
header = gotcha.headers
mycookies = gotcha.cookies
EtherCloud = "https://etherscan.io/labelcloud"
Etherprefix = "https://etherscan.io"
Ethersuffix : str = "?subcatid=1&size=25&start=0&col=1&order=asc"

res = requests.get(url=EtherCloud, headers=header, cookies= mycookies)
result = busp(res.text, 'html.parser')
outer = result.find_all("div", class_ = "col-md-4 col-lg-3 mb-3 secondary-container")
alldict :dict = {}
for items in outer:
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
    total : int =0
    for partial in alldict[name].keys():
        total += int(partial[partial.index("(") + 1 : partial.index(")") ])
    total = int(total/25)
    links = alldict[name].values()
    for eachlink in links:
    # here, for detailed parse of a label, go into another fuction
    # parameters that function need: eachlink, total, alldict
        subdict : dict = {}
        for iteral in range(total):
            if not total: Eurl = Etherprefix + eachlink
            else: Eurl 
            labeled = requests.get(url = Etherprefix + eachlink, headers=header)
            laberes = busp(labeled.text, "html.parser")
            layerone = laberes.find('tbody')
            layertwo = layerone.find_all("tr")
            for item in layertwo:
                target = item.find("a").text
                if item.find("i") == None:
                    if not len(subdict):subdict["accounts"] = []
                    subdict["accounts"].append(target)
                elif item.find("i"):
                    name = item.find("i")["title"]
                    if not subdict.get(name): subdict[name] = []
                    subdict[name].append(target)
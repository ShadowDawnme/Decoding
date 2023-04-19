import HeaderFile as hf

# auxiliary class, used to provide some important variable type.
# include web3 connection, contract factory variable, ABI file
class W3:
    w3 : hf.Web3
    Etherscan_key : str = "KCZFUVHX2EBKU1TRYN5NAI31KHTQSYNPRK"
    contract_factory = None 
    # CurrentPath = hf.os.getcwd()
    CurrentPath = "D:\pycharm\simulate\python_simulate\ABI_FIle_generator"
    
    def __init__(self):
        self.w3 = hf.Web3(hf.Web3.HTTPProvider("https://mainnet.infura.io/v3/e871b52e91224b89a26ce7aad3857819"))
        if not self.w3.isConnected(): 
            raise ConnectionError("cannot establish web3 object, check your web connection")

    def ABIreadPath(self, contractHash : str):
        suffix = contractHash + ".json"
        fullPath = hf.os.path.join(self.CurrentPath, "ABIfiles", suffix)
        dirPath = hf.os.path.join(self.CurrentPath, "ABIfiles")
        if not hf.os.path.isdir(dirPath):
            hf.os.mkdir(dirPath)
        return fullPath
    
    def csvPath(self, name : str):
        suffix = name + ".csv"
        dirPath = hf.os.path.join(self.CurrentPath, "CSVfiles")
        fullPath = hf.os.path.join(dirPath, suffix)
        if not hf.os.path.isdir(dirPath):
            hf.os.mkdir(dirPath)
        return fullPath
    
    def w3_provider(self):
        return self.w3
    
    # if input ABI doesnt exist, program would go etherscan to match the ABI file according to given address(contract address)
    def Abi_Get(self, Address : str, ABI : dict):
        Address = hf.Web3.toChecksumAddress(Address)
        if ABI is None:
            connector = f"https://api.etherscan.io/api?module=contract&action=getabi&address={Address}&apikey={self.Etherscan_key}"
            Abi = hf.basic_json.loads(hf.requests.get(connector).text)
        else : 
            Abi = ABI
        if Abi["message"] == "NOTOK" or isinstance(Abi, str): 
            return False
        self.contract_factory = self.w3.eth.contract(address=Address, abi= Abi["result"])
        return Abi
        
    # return a factory type variable
    def contract_factory_provider(self):
        if self.contract_factory == None:
            raise ValueError("cannot return correct factory object, please check your input address and Etherscan Key")
        return self.contract_factory

    
    # newly updated function, which could get contract binary code
    def byteContract(self, ContractAdrs: str): # ->str
        ContractAdrs = hf.Web3.toChecksumAddress(ContractAdrs)
        CbyteCode: hf.HexBytes = self.w3.eth.get_code(ContractAdrs)
        return CbyteCode.hex()

provider : W3 = W3()

class Reader:
    path : str = ""
    
    def __init__(self, path) -> None:
        self.path += provider.ABIreadPath(path)
    
    def my_read_json(self):
        with open (self.path, 'r') as fp: 
            files = hf.json.load(fp)
        fp.close()
        return files                                                                             

    # return type: a dictionary with four items or False
    # which stores event ABI, functions ABI
    # and full ABI files(above three are dict), contract address with string type
    def pre_map(self):                                                          
        file = self.my_read_json()
        if not file:
            print("this tx doesnt upload its source code.")
            return False
        event, functions = dict(), dict()
        contract_address = hf.ntpath.basename(self.path)[:-5]
        for parenthetical in file:
            if (parenthetical['type'] == 'event'): event[parenthetical['signature']] = parenthetical
            elif (parenthetical['type'] == 'function'): functions[parenthetical["signature"]] = parenthetical
        return {"event" : event, "functions" : functions, "ABI_files" : file, "contract_address": contract_address}

# used to detect the path existence
# return bool
def contract_detect(path):
    return hf.os.path.isfile(path)

def function_hash(item:dict):
    if ('inputs' not in item.keys()):
        return
    input_list = [input_item['type'] for input_item in item['inputs']]
    full_name = item['name'] + '(' + ','.join(input_list) + ')'
    fhash=hf.Web3.keccak(text = full_name)
    fhash=fhash.hex()
    return fhash

def ABI_adjustor(Abi):
    if Abi['message']!='OK' or (Abi['result'] is None): 
        return False
    result = hf.basic_json.loads(Abi['result'])
    functions, event  = {}, {}
    for bracket in result:
        if (bracket["type"] == "function"): 
            bracket["signature"] = function_hash(bracket)[0:10]
            functions[bracket["signature"]] = bracket
        elif (bracket["type"] == "event"): 
            bracket["signature"] = function_hash(bracket)  #  event_hash(parenthetical["name"])
            event[bracket["signature"]] = bracket
        else: bracket["signature"] = bracket["type"]
    return result, {"functions": functions, "event": event}

Mplock = None
def LockReceiver(Lock : hf.process.Lock):
    global Mplock
    Mplock = Lock
    return 

# store ABI files as json
def abi_json_writer(input_path, abi_files):
    global Mplock
    Mplock.acquire()
    path = provider.ABIreadPath(input_path)
    with open(path, 'w') as final_step:
        hf.basic_json.dump(abi_files, final_step, ensure_ascii=False, indent=4)
    final_step.close()
    Mplock.release()
    return

writorLock = 0

def abi_csv_writer(csv_write_path : str, file_content : list):
    if not len(file_content) : return
    Mplock.acquire()
    global writorLock
    target_csv = open(csv_write_path, 'a+', newline= "" )
    longest_dict = max([(file_content.index(rdict), len(rdict.values())) for rdict in file_content], key = lambda value: value[1])
    csvW = hf.csv.DictWriter(target_csv, fieldnames = file_content[longest_dict[0]].keys(), extrasaction="ignore")
    if not writorLock:
        csvW.writeheader()
        writorLock =1
    csvW.writerows(file_content)
    target_csv.close()
    Mplock.release()
    return

def pdCSVwriter(csvName : str, file_content : dict):
    df = hf.pandas.DataFrame.from_dict(file_content, orient="index")

# in this function, or default input data should be considered as tuple
# the last position would store its onctract address
def LOGWriter(Ltype : str, ABIList : tuple = hf.Any, txmsg : tuple = hf.Any, Logs : tuple = hf.Any) :
    Mplock.acquire()
    Emsg, filenames = "", ""
    if Ltype == "ABIs":
        Emsg = """
        web3 hasnt return corresponding event ABI. 
        target ABI address is:  {} 
        target event signature is:  {}""".format(ABIList[0], ABIList[1])
        filenames = "ABIs"
    elif Ltype == "txs":
        Emsg = """
        According to test, seems this txs doesnt equip with a meanful input, 
        transaction hash is: {}""".format(txmsg[0])
        filenames = "txs_Elog"
    elif Ltype == "Logs":
        Emsg = """
        According to test, seems this txs doesnt equip with a meanful logs, 
        under txs: {},
        logs refered hash is: {}""".format(Logs[0], Logs[1])
        filenames = "txs_Elog"
    else: 
        raise ValueError("Input wrong data type here...")
    Rformat = "%(asctime)s - %(pathname)s - %(funcName)s - %(message)s"
    hf.logging.basicConfig(filename= filenames + ".log", filemode = "a", level = hf.logging.INFO, format = Rformat)
    hf.logging.info(Emsg)
    Mplock.release()
    return 0

def combine_tx(contract_hash : str):
    # focus on path
    path : str= provider.ABIreadPath(contract_hash)
    if contract_hash is None: return False
    ABIFile = provider.Abi_Get(contract_hash, None)
    if not ABIFile:  return False
    # first, if we have Corresponding file
    if contract_detect(path):
        return Reader(contract_hash).pre_map() # ->dict
    #if we cant find the ABI
    abi, info = ABI_adjustor(ABIFile)
    info["contract_address"] = hf.Web3.toChecksumAddress(contract_hash)
    # in single cpu process part
    # seems need to modified if we really wanna it to use multi-something to process it
    abi_json_writer(contract_hash, abi)
    
    return info

import HeaderFile as hf

def abi_json_writer(input_path, abi_files):
    # global Mplock
    # Mplock.acquire()
    path = W3().ABIreadPath(input_path)
    with open(path, 'w') as final_step:
        hf.basic_json.dump(abi_files, final_step, ensure_ascii=False, indent=4)
    final_step.close()
    # Mplock.release()
    return

# in this function, or default input data should be considered as tuple
# the last position would store its onctract address
def LOGWriter(Ltype : str, ABIList : tuple = hf.Any, txmsg : tuple = hf.Any, Logs : tuple = hf.Any) :
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
    return 0

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

    # newly updated function, which could get contract binary code
    def byteContract(self, ContractAdrs: str):
        ContractAdrs = hf.Web3.toChecksumAddress(ContractAdrs)
        CbyteCode: hf.HexBytes = self.w3.eth.get_code(ContractAdrs)
        return CbyteCode.hex()
    
    def _w3_geter(self):
        return self.w3

    # return a factory type variable
    def _contract_factory_geter(self):
        if self.contract_factory == None:
            raise ValueError("cannot return correct factory object, please check your input address and Etherscan Key")
        return self.contract_factory
    
    def ABIreadPath(self, contractHash : str):
        suffix = contractHash + ".json"
        fullPath = hf.os.path.join(self.CurrentPath, "ABIfiles", suffix)
        dirPath = hf.os.path.join(self.CurrentPath, "ABIfiles")
        if not hf.os.path.isdir(dirPath):
            hf.os.mkdir(dirPath)
        return fullPath
    
    # used to detect the path existence
    # return bool
    def contract_detect(self, path):
        return hf.os.path.isfile(path)
    
    def csvPath(self, name : str):
        suffix = name + ".csv"
        dirPath = hf.os.path.join(self.CurrentPath, "CSVfiles")
        fullPath = hf.os.path.join(dirPath, suffix)
        if not hf.os.path.isdir(dirPath):
            hf.os.mkdir(dirPath)
        return fullPath
    
    # if input ABI doesnt exist, program would 
    # go etherscan to match the ABI file according to given address(contract address)
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
    
    # return type: a dictionary with four items or False
    # which stores event ABI, functions ABI
    # and full ABI files(above three are dict), contract address with string type
    def pre_map(self, fpath):     
        with open (fpath, 'r') as fp: 
            files = hf.json.load(fp)                                                  
        if not files:
            print("this tx doesnt upload its source code.")
            return False
        event, functions = files["event"], files["functions"]
        contract_address = hf.ntpath.basename(fpath)[:-5]
        return {"event" : event, "functions" : functions, "ABI_files" : files, "contract_address": contract_address}
    
    # can this be replaced by web3 built in functions?
    def function_hash(self, item:dict):
        if ('inputs' not in item.keys()):
            return 
        input_list = [input_item['type'] for input_item in item['inputs']]
        full_name = item['name'] + '(' + ','.join(input_list) + ')'
        fhash=hf.Web3.keccak(text = full_name)
        fhash=fhash.hex()
        return fhash
    
    def ABI_adjustor(self, Abi):
        if Abi['message']!='OK' or (Abi['result'] is None): 
            return False
        result = hf.basic_json.loads(Abi['result'])
        functions, event  = {}, {}
        for bracket in result:
            if (bracket["type"] == "function"): 
                bracket["signature"] = self.function_hash(bracket)[0:10]
                functions[bracket["signature"]] = bracket
            elif (bracket["type"] == "event"): 
                bracket["signature"] = self.function_hash(bracket)  #  event_hash(parenthetical["name"])
                event[bracket["signature"]] = bracket
            else: bracket["signature"] = bracket["type"]
        return result, {"functions": functions, "event": event}
    
    def combine_tx(self, contract_hash : str):
        """formula (1) should switch position with formula (2)
        used to get ABI file then parser/manuiplate them and store as JSON file in specific local position
        in future will involve calling for database to take place storage functionality. 
        
        Args:
            contract_hash (str): a string record contract hash

        Returns:
            dict: return a dict contain JSON type ABI file or a dict only contain false if there isnt mathced ABI file
        """
        if contract_hash is None: return False
        path : str= self.ABIreadPath(contract_hash)  
        ABIFile = self.Abi_Get(contract_hash, None) # (1)
        if not ABIFile:  return False  # (1)
        if self.contract_detect(path):  # (2)
            return self.pre_map(path)  # (2)
        
        #------need debugging here!!---------------
        abi, info = self.ABI_adjustor(ABIFile)
        info["contract_address"] = hf.Web3.toChecksumAddress(contract_hash)
        # in single cpu process part
        # seems need to modified if we really wanna it to use multi-something to process it
        abi_json_writer(contract_hash, info)
        
        return info
    
def convert(x):
    if x.__class__ in  [hf.hexbytes.main.HexBytes, bytes]:
        return x.hex()
    return x
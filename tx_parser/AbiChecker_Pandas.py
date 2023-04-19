import HeaderFile as hf
import neWeb3 as webp
from EventProcess_Pandas import Event_checker as Evch

# main workflow of this program
class Checker:
    w3provider = webp.W3()
    w3 = w3provider._w3_geter()
    tx_hash : str
    aggrCon : dict
    
    def __init__(self, tx_hash) :
        if tx_hash is None: raise SyntaxError
        self.tx_hash=tx_hash
        
    def file_get(self, Address : str) :  # Address in there has been checked
        self.aggrCon = self.w3provider.combine_tx(Address)
        if not self.aggrCon: return False
        return True
    
    # will using multiprocessing to faster the programming
    def total_console(self):
        """
        logs on August 14th: 
        1. input decoding must activate the contract factory, and changed contract not satisfy its requreiment
        2. input decoding library has some special decoding methods...
        """
        with hf.Thruser.ThreadPoolExecutor(max_workers=2) as executor:
            tx : hf.Future = executor.submit(self.w3.eth.get_transaction, self.tx_hash)
            receipt : hf.Future = executor.submit(self.w3.eth.get_transaction_receipt, self.tx_hash)
        greek = self.file_get(hf.Web3.toChecksumAddress(tx.result().to))
        if not greek: return False
        self.decode_tx_input(tx.result())
        self.decode_tx_event(receipt.result())
        print("exection of event finsihed")
        return 
    
    def decode_tx_input(self, tx_input : hf.structure.AttributeDict) :      
        """decode input
        the way use pandas to flatten nested JSON file from there:
        https://stackoverflow.com/questions/52795561/flattening-nested-json-in-pandas-data-frame

        Args:
            tx_input (hf.structure.AttributeDict): the AttributeDict from Ethereum API

        Returns:
            None
            
        Raise:
            KeyError: 
        """
        contract = self.w3provider._contract_factory_geter()
        matched = None
        try:
            matched = self.aggrCon["functions"][tx_input['input'][0:10]].copy()
        except KeyError:
            return 0, False
        if matched == None: 
            print("input cannot match with current ABI files")
            return 0, False
        tx_input = {key : (value.hex() 
        if type(value) is hf.hexbytes.main.HexBytes else value) 
        for key, value in dict(tx_input).items()}
        
        tx_input = {**tx_input, **matched}
        input_result = contract.decode_function_input(tx_input["input"])
        for inputs_index in range(len(input_result[1])):
            deInput = input_result[1][matched['inputs'][inputs_index]['name']]
            tx_input['inputs'][inputs_index]['result'] = (deInput.hex() 
                                                                                if type(deInput) in [hf.hexbytes.main.HexBytes, bytes] 
                                                                                else deInput)
        tx_input['function full name'] = str(input_result[0])
        del tx_input["input"]

        tx_input = (hf.pd.json_normalize(tx_input, max_level=3)
        .apply(hf.pd.Series.explode)
        .reset_index()
        )
        column_to_norm = ["inputs", "outputs"]
        normalized : list = list()
        for item in column_to_norm:
            target = hf.pd.json_normalize(tx_input[item], sep=".")
            target.columns = [f"{item}_{v}" for v in target.columns]
            normalized.append(target.copy())
        tx_input : hf.pd.DataFrame = (hf.pd.concat([tx_input.drop(columns = column_to_norm)] + normalized , axis = 1)
                                                        .explode("inputs_result"))
        tx_input.inputs_result = tx_input.inputs_result.apply(webp.convert)
        
        # here, a tx_input file is needed before go ahead
        tx_input.to_csv("ABI_FIle_generator/CSVfiles/tx_input.csv",
        mode = "a",
        index = False,
        header = False if hf.os.stat("ABI_FIle_generator/CSVfiles/tx_input.csv").st_size else True)
        # os.stat could only detect existed file
        
    # used to decode event
    def decode_tx_event(self, receipt : hf.structure.AttributeDict):        
        if not self.aggrCon["event"]: return False,  False
        logs = Evch(
        receipt, 
        self.aggrCon["functions"],
        self.aggrCon["event"], 
        )
        logs.assumble()
        return 
    
def starter(txList: list):
    for tx in txList:
        JackThr: Checker = Checker(tx.hex())
        JackThr.total_console()
    return True

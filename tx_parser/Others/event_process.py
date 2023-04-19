import HeaderFile as hf
from times import time_length
import web3_provider

class Event_checker:
    
    w3 = web3_provider.provider.w3_provider()
    receipt : hf.structure.AttributeDict
    event : dict # receive ABI
    func: dict   # receive ABI
    contract_address : str
    template: dict = None
    
    Otimes : time_length
    
    def __init__(self, receipt, func: dict, event : dict, address:str) -> None:
        if receipt is None or event is None:
            print("invalid information/connection fails")
            exit()
        self.receipt = receipt
        self.func : dict= func
        self.event : dict = event
        self.contract_address : str = address
    
    def mapping(self, Otimes : time_length):
        self.Otimes = Otimes
        return 
    
    # during codes running this function usually will cost most time
    # convert this function into multiprocess will greately optimize codes effience
    def assumble(self, logs:dict):
        matched_event : list = []
    # this loop is used for single process running
        for ievent in logs:  
            event_result = self.event_decoder(ievent)
            # if not event_result: continue 
            matched_event.append(event_result)
        return matched_event 
       
    def event_decoder(self, event : dict):
        # custom emitted event will be transfered to a decodable format
        if event["topics"][0].hex()[10 :] == "00000000000000000000000000000000000000000000000000000000":
            new_event : dict = web3_provider.combine_tx(event['address'])
            self.func = new_event["functions"]
            try:
                print(event["topics"][0].hex()[ :10], event["topics"][0].hex()[ :10] in self.func)
                matchedInput: hf.Any = self.func[event["topics"][0].hex()[ :10]]
            except KeyError: return {"Logs" : "NOT decode-able"}   
            inpuEvent: dict = self.camouflage(matchedInput, event)
            event = inpuEvent["ChengedEvent"]
            self.event = {**{event["topics"][0].hex() :inpuEvent["digused ABI"].copy()}, **self.event}
        # retrieve if the coressponding ABI has been read or not
        elif event['topics'][0].hex() not in self.event:
            new_event : dict = web3_provider.combine_tx(event['address'])
            try:
                # merge the two dict and update self.event
                self.event = {**self.event, **new_event['event']} 
            except TypeError: return {"Logs" : "NOT decode-able"}
        
        try:
            result : dict = self.event[event['topics'][0].hex()].copy()
        except KeyError: 
            web3_provider.LOGWriter(Ltype="ABIs", ABIList= (event['address'], event['topics'][0].hex()))
            return {"Logs" : "NOT decode-able"}
        counterpart = hf.parser.get_event_data(self.w3.codec, result, event)  # decode data by using web3
        # except NonEmptyPaddingBytes: return 0
        counter_keys : list = ["transactionHash", "name", "signature", "type", "logIndex", "transactionIndex"]
         # first iteration, bascially we do the same with inputs
        for value in counterpart:  # insert processed input data into matched_event
            if value == 'args':
                # second iteration since result of get_event_data is more complex, its not a tuple
                for index in range(len(result['inputs'])):
                    pointer = result['inputs'][index]['name']
                    # store result
                    result['inputs'][index]['result'] = counterpart[value][pointer]
                    # add new items in both result, counter_keys
                    counter_keys.extend(["inputs" + str(index) + "_" + items for items in result["inputs"][index].keys()])
                    for dkey, dvalue in result['inputs'][index].items():
                        result["inputs" + str(index) + "_" + dkey] = dvalue.hex() if type(dvalue) == hf.hexbytes.main.HexBytes or type(dvalue) == bytes else dvalue
            elif type(counterpart[value]) == hf.hexbytes.main.HexBytes:
                result[value] = counterpart[value].hex()
            if value not in counter_keys and value not in ['inputs', 'args', 'event'] : 
                counter_keys.append(value)
            if value not in result.keys() and value != "event" and value != "args":
                result[value] = counterpart[value].hex() if type(counterpart[value]) == hf.hexbytes.main.HexBytes or type(counterpart[value]) == bytes else counterpart[value]
        result['name'] = result['name'] + '(' + ",".join([result['inputs'][loops]['type'] + " "+ result['inputs'][loops]['name'] for loops in range(len(result['inputs']))]) + ')'
        result.pop("inputs")
        counter_keys.append("anonymous")
        result = dict(sorted(result.items(), key=lambda x: counter_keys.index(x[0])))
        return result
    
    def position_checker(self, Postart: int):
        if not (Postart-1) % 64: return False
        return True
    
    def indexed_marker(self, totalData: list, indexedList: list, input_ABI: list):
        for indexed in range(len(indexedList)):
            if indexedList[indexed] in totalData:
                input_ABI[indexed]['indexed'] = True
    
    def camouflage(self, func_ABI: dict, target: hf.structure.AttributeDict):
        # read the standard format of event 
        if self.template == None:
            with open(r"ABIfiles/Event_standard_format.json", 'r') as tarfile:
                self.template = hf.json.load(tarfile)
            tarfile.close()
        standrformat: dict = hf.copy.deepcopy(self.template)
        vaLength: int
        # set standard format as basement, access in it
        for key, value in standrformat.items():
            # import some necessary first layer key value
            if key!= "inputs" and key in func_ABI.keys():
                standrformat[key] = func_ABI[key]
            # merge value in inputs to standard template of event
            if key == "inputs":
                inlogs: list = func_ABI["inputs"] 
                vaLength = len(inlogs)
                for invalue in inlogs:
                    # dict in value[0] wont be overwriteen instead it always been set as template
                    inpuTemplate: dict = value[0].copy()
                    # merge value with same key in both dicts in dict layer to keep code concise
                    # this expression only suit for python 3.5+, for detail you can refer to
                    # https://stackoverflow.com/questions/71546879/how-to-assign-value-in-dict1-to-dict2-if-the-key-are-the-same-without-loop
                    inpuTemplate = {**inpuTemplate, **invalue}
                    inpuTemplate["internalType"] = invalue["type"]
                    # value is target(receipt)['logs]['inputs'], which is a list
                    value.append(inpuTemplate)
                # in the last we delete the template value[0]
                del value[0]
        # second step, change item topics and data in target
        topics: list = [topic.hex()[2: ] for topic in target['topics']]
        Postart: int = target['data'].find(topics[0][: 8]) + 8
        if not self.position_checker(Postart):
            # later add a function to skip the part and record it into logs
            raise ValueError("there is similar singature appear, check the status.")
        trueInput: list = [target['data'][Postart+tarval*64 : Postart + 64* (tarval+1)] for tarval in range(vaLength)]
        indexed: list = [trueInput[indexedval] for indexedval in range(len(trueInput)) if trueInput[indexedval] in topics and indexedval<3]
        # rerturn type of event_abi_to_log_topic has already been hexbytes type 
        standrformat["type"] = "event"
        target = dict(target)
        target['topics'] = list(map(hf.hexbytes.main.HexBytes, [hf.tools.event_abi_to_log_topic(standrformat)] + indexed))
        self.indexed_marker(trueInput, indexedList = indexed, input_ABI = standrformat['inputs'])
        # restore the data part.
        differenceInput: list = [trueInput[Nval] for Nval in range(len(trueInput)) if trueInput[Nval] not in indexed or Nval+1>len(indexed)]  #set(trueInput).symmetric_difference(set(indexed))
        # disguise data type, from dict to structure.AttributeDict
        target['data'] = "0x" + ''.join(map(str, differenceInput))
        target = hf.structure.AttributeDict(target)
        return {"digused ABI" : standrformat, "ChengedEvent": target, "indexedPar" : indexed}
    
    def event_spliter(self):
        # decoded_logs = {}
        decoded_logs = self.assumble(self.receipt["logs"])
        return decoded_logs

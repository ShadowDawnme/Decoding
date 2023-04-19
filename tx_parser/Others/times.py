import queue
from web3 import Web3
import time
import web3_provider as servant
# import new_Abi_checker as console

class time_length:
    timeQue: queue.LifoQueue = queue.LifoQueue(maxsize = 3)
    CustomizedQueue : list
    def __init__(self) -> None:
        return None
    
    def dict_add(self, name:str):
        self.CustomizedQueue.append({name: time.time()})
        return True
    
    # debug needed
    
    def dict_pop(self, name: str):
        correspoonding: dict = self.CustomizedQueue.pop()
        if correspoonding.keys()[0] != name:
            raise OverflowError("Not the same function time with current function, or stack overflow") 
        return name, time.time() - correspoonding.values()[0]

        
    def time_addr(self, name: str):       
        self.timeQue.put({name: time.time()})
        return True
    
    def time_pop(self, name: str):
        if self.timeQue.get(block=False).keys()[0] != name or not self.timeQue.qsize():
            raise OverflowError("Not the same function time with current function, or stack overflow") 
        return name, time.time() - self.timeQue.get(block = False).values()[0]


# change new program entrance in there, test 1000 blocks to record and calcualte its average time.
class block_tx:
    w3 : Web3.HTTPProvider = servant.provider.w3_provider()
    
    def __init__(self) -> None:
        return
    
    def blk_txs(self) :
        # blockNumList : list = [self.w3.eth.get_block(blkindex).transactions for blkindex in range(14190000, 100+14190000)] 
        blockNumList: list = self.w3.eth.get_block(14190080).transactions
        print("Do We start? ---------------------------------------------")
        # OK this is single one, Attention !! resouce conflication may coursed in there
        # for txs in blockNumList:
        #     console.starter(txs)
        # multiprocessing one
        # with Prouser.ProcessPoolExecutor() as executorPool:
        #     executorPool.map(console.starter, blockNumList)
        return self.w3.eth.get_block(14190080).transactions

# if __name__ == "__main__":
#     block_tx().blk_txs()
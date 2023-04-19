import HeaderFile as hf
import AbiChecker_Pandas as AP
import neWeb3 as nw

# how to convert timestamp to date: https://ethereum.stackexchange.com/questions/7287/how-to-find-the-date-of-an-ethereum-transaction-while-parsing-it-with-web3 
w3 = nw.W3()._w3_geter()
# block number in (2022, 2, 23, 23, 36, 21), sereval hours before Ukranie and Russian war
initialBlk : int = 14277036
testOne : int = 14278036
endBlk : int = 14500000
# Currentblk : int = w3.eth.get_block("latest")

def fileRead():
    hashes : hf.pd.DataFrame = ["0x2fac1fd587efc1ca7ba1ff1e7dae672d36e283460644c830f801dbc70d16a1ad"]
    AP.starter(hashes)
    
def multiRunning(blknum : int):
    temp = w3.eth.get_block(blknum)
    AP.starter(temp.transactions)
    
if __name__ == "__main__":
    with hf.Prouser.ProcessPoolExecutor(max_workers=5) as executor:
        executor.map(multiRunning, [blk for blk in range(initialBlk, initialBlk + 20)])
    # fileRead()
    
# 0x2fac1fd587efc1ca7ba1ff1e7dae672d36e283460644c830f801dbc70d16a1ad
# 0xe34fda41d1cb852a0ff612843a9306e1a3932a579f3ae93d29b28916ffe14fbd
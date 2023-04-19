import pyodbc
import pandas as pd
import json


def unify_dict_key(data_dict, key_dict):
    for key in key_dict.keys():
        data_dict[key_dict[key]] = data_dict.pop(key)
    return data_dict


def unify_df_header(df: pd.DataFrame, header_dict):
    return df.rename({header_dict}, axis=1)


def get_unique_records(df_list, cols, key):
    # cols = ['th', 'blockNumber']
    unique_records = pd.DataFrame(columns=cols)
    for df in df_list:
        df = df[cols]
        unique_records += df
    unique_records.drop_duplicates(subset=key)
    return unique_records


class DAIPoolDB:
    server = 'web3.database.windows.net'
    database = 'web3ct'
    username = 'freeman'
    password = '{19081789d@}'
    driver = '{ODBC Driver 17 for SQL Server}'

    def __init__(self):
        self.connect = pyodbc.connect('DRIVER=' + DAIPoolDB.driver + ';SERVER=tcp:' + DAIPoolDB.server +
                                      ';PORT=1433;DATABASE=' + DAIPoolDB.database + ';UID=' + DAIPoolDB.username +
                                      ';PWD=' + DAIPoolDB.password)
        self.cursor = self.connect.cursor()

    def close(self):
        self.cursor.close()
        self.connect.close()

    def execute_sql_query(self, sql_code):
        self.cursor.execute(sql_code)
        return self.cursor.fetchall()

    def execute_sql_code(self, sql_code):
        self.cursor.execute(sql_code)
        self.connect.commit()

    def get_col_names(self, table):
        sql_code = ("SELECT COLUMN_NAME "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    f"WHERE TABLE_NAME = \'{table}\' "
                    "ORDER BY ORDINAL_POSITION")
        self.cursor.execute(sql_code)
        return [item[0] for item in self.cursor.fetchall()]

    def insert_df(self, df, table):
        self.cursor.execute(f"SET IDENTITY_INSERT {table} ON")

        col_names = self.get_col_names(table)
        df = df[col_names]
        col_names_str = ','.join(col_names)
        for index, row in df.iterrows():
            attrs_str = ','.join(
                [str(int(row[col_name])) if type(row[col_name]) == bool else str(
                    row[col_name]) if type(row[col_name]) != str else "\'" + row[col_name] + "\'"
                 for col_name in col_names]
            )

            sql_code = f"INSERT INTO {table} ({col_names_str}) VALUES ({attrs_str})"
            # print(sql_code)
            self.cursor.execute(sql_code)
        self.connect.commit()

        self.cursor.execute(f"SET IDENTITY_INSERT {table} OFF")

    def insert_df_with_dict(self, df, table, db_data_attr_dict):
        self.cursor.execute(f"SET IDENTITY_INSERT {table} ON")

        col_names = self.get_col_names(table)
        df = df[[db_data_attr_dict[col_name] for col_name in col_names]]
        col_names_str = ','.join(col_names)
        for index, row in df.iterrows():
            attrs_str = ','.join(
                [str(row[db_data_attr_dict[col_name]]) if type(row[db_data_attr_dict[col_name]]) != str
                 else "\'" + row[db_data_attr_dict[col_name]] + "\'" for col_name in col_names]
            )

            sql_code = f"INSERT INTO {table} ({col_names_str}) VALUES ({attrs_str})"
            # print(sql_code)
            self.cursor.execute(sql_code)
        self.connect.commit()

        self.cursor.execute(f"SET IDENTITY_INSERT {table} OFF")

    def insert_csv(self, path, table):

        df = pd.read_csv(path)
        self.insert_df(df, table)

    def insert_csv_with_dict(self, path, table, db_data_attr_dict):

        df = pd.read_csv(path)
        self.insert_df_with_dict(df, table, db_data_attr_dict)

    def insert_dict(self, table, data_dict):

        col_names = self.get_col_names(table)
        col_names_str = ','.join(col_names)

        attrs_str = ','.join(
            [str(int(data_dict[col_name])) if type(data_dict[col_name]) == bool else str(
                data_dict[col_name]) if type(data_dict[col_name]) != str else "\'" + data_dict[col_name] + "\'"
             for col_name in col_names]
        )

        sql_code = f"INSERT INTO {table} ({col_names_str}) VALUES ({attrs_str})"
        print(sql_code)
        self.cursor.execute(sql_code)
        self.connect.commit()

    def insert_funcs(self, funcs, contract_address):
        cf_cols = ['fs', 'fname', 'stateMutability', 'contractAddress']
        fo_cols = ['fs', 'foname', 'foInternalType', 'foType']
        fi_cols = ['fs', 'finame', 'fiInternalType', 'fiType']
        key_dict = {'signature': 'fs', 'name': 'fname'}
        key_input_dict = {"internalType": "fiInternalType", "name": "finame", "type": "fiType"}
        key_output_dict = {"internalType": "foInternalType", "name": "foname", "type": "foType"}

        for fs in funcs.keys():
            func = unify_dict_key(funcs[fs], key_dict)
            func['contractAddress'] = contract_address
            cf_record_dict = {k: func[k] for k in cf_cols}
            self.insert_dict('cf', cf_record_dict)

            for input_argument in func['inputs']:
                input_argument['fs'] = func['fs']
                unify_dict_key(input_argument, key_input_dict)
                fi_record_dict = {k: input_argument[k] for k in fi_cols}
                self.insert_dict('fi', fi_record_dict)

            for output_argument in func['outputs']:
                output_argument['fs'] = func['fs']
                unify_dict_key(output_argument, key_output_dict)
                fo_record_dict = {k: output_argument[k] for k in fo_cols}
                self.insert_dict('fo', fo_record_dict)

    def insert_events(self, events, contract_address):
        ce_cols = ['es', 'anonymous', 'ename', 'contractAddress']
        ei_cols = ['es', 'einame', 'eiInternalType', 'eiType', 'indexed']
        key_dict = {'signature': 'es', 'name': 'ename'}
        key_input_dict = {"internalType": "eiInternalType", "name": "einame", "type": "eiType"}

        for es in events.keys():
            event = unify_dict_key(events[es], key_dict)
            event['contractAddress'] = contract_address
            ce_record_dict = {k: event[k] for k in ce_cols}
            self.insert_dict('ce', ce_record_dict)

            for input_argument in event['inputs']:
                input_argument['es'] = event['es']
                unify_dict_key(input_argument, key_input_dict)
                ei_record_dict = {k: input_argument[k] for k in ei_cols}
                print(ei_record_dict)
                self.insert_dict('ei', ei_record_dict)

    def insert_contract(self, contract):
        self.insert_funcs(contract["functions"], contract["contract_address"])
        self.insert_events(contract["event"], contract["contract_address"])

    def insert_t_all(self, inputs_df, events_df):
        inputs_df = unify_df_header(inputs_df, {'hash': 'th', 'signature': 'fs', 'inputs_name': 'finame',
                                                'inputs_result': 'fiArgumentValue'})
        events_df = unify_df_header(events_df,
                                    {'signature': 'es', 'input_name': 'einame', 'input_result': 'eiArgumentValue',
                                     'hash': 'th'})
        self.insert_unique_records('t', [inputs_df, events_df], ['th', 'blockNumber'], ['th'])

        self.insert_unique_records('tfi', [inputs_df], ['th', 'finame', 'fiArgumentValue'], ['th', 'finame'])

        self.insert_unique_records('tfo', [inputs_df], ['th', 'foname', 'fiArgumentValue'], ['th', 'foname'])

        self.insert_unique_records('tf', [inputs_df], ['th', 'gas', 'gasPrice', 'fs', 'value'], ['th'])

        self.insert_unique_records('tei', [events_df], ['th', 'es', 'einame', 'eiArgumentValue'],
                                   ['th', 'es', 'einame'])

    def insert_unique_records(self, table, dfs, cols, key):
        self.insert_df(get_unique_records(dfs, cols, key), table)


contract_json = '''{
    "functions": {
        "0xe40c936f": {
            "inputs": [],
            "name": "RootHash",
            "outputs": [
                {
                    "internalType": "bytes32",
                    "name": "",
                    "type": "bytes32"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0xe40c936f"
        },
        "0x095ea7b3": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "to",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "approve",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x095ea7b3"
        },
        "0x70a08231": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x70a08231"
        },
        "0x13faede6": {
            "inputs": [],
            "name": "cost",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x13faede6"
        },
        "0x081812fc": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "getApproved",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x081812fc"
        },
        "0xa45ba8e7": {
            "inputs": [],
            "name": "hiddenMetadataUri",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0xa45ba8e7"
        },
        "0xe985e9c5": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "owner",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "operator",
                    "type": "address"
                }
            ],
            "name": "isApprovedForAll",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0xe985e9c5"
        },
        "0x94354fd0": {
            "inputs": [],
            "name": "maxMintAmountPerTx",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x94354fd0"
        },
        "0xd5abeb01": {
            "inputs": [],
            "name": "maxSupply",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0xd5abeb01"
        },
        "0xa0712d68": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_mintAmount",
                    "type": "uint256"
                }
            ],
            "name": "mint",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function",
            "signature": "0xa0712d68"
        },
        "0x06fdde03": {
            "inputs": [],
            "name": "name",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x06fdde03"
        },
        "0x9c70b512": {
            "inputs": [],
            "name": "onlyWhitelisted",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x9c70b512"
        },
        "0x8da5cb5b": {
            "inputs": [],
            "name": "owner",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x8da5cb5b"
        },
        "0xd52c57e0": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_mintAmount",
                    "type": "uint256"
                },
                {
                    "internalType": "address",
                    "name": "_receiver",
                    "type": "address"
                }
            ],
            "name": "ownerMint",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xd52c57e0"
        },
        "0x6352211e": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "ownerOf",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x6352211e"
        },
        "0x5c975abb": {
            "inputs": [],
            "name": "paused",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x5c975abb"
        },
        "0x5618dc49": {
            "inputs": [],
            "name": "preSaleWalletLimit",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x5618dc49"
        },
        "0x715018a6": {
            "inputs": [],
            "name": "renounceOwnership",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x715018a6"
        },
        "0x51830227": {
            "inputs": [],
            "name": "revealed",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x51830227"
        },
        "0x42842e0e": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "from",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "to",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "safeTransferFrom",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x42842e0e"
        },
        "0xb88d4fde": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "from",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "to",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                },
                {
                    "internalType": "bytes",
                    "name": "_data",
                    "type": "bytes"
                }
            ],
            "name": "safeTransferFrom",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xb88d4fde"
        },
        "0xa22cb465": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "operator",
                    "type": "address"
                },
                {
                    "internalType": "bool",
                    "name": "approved",
                    "type": "bool"
                }
            ],
            "name": "setApprovalForAll",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xa22cb465"
        },
        "0x44a0d68a": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_cost",
                    "type": "uint256"
                }
            ],
            "name": "setCost",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x44a0d68a"
        },
        "0x4fdd43cb": {
            "inputs": [
                {
                    "internalType": "string",
                    "name": "_hiddenMetadataUri",
                    "type": "string"
                }
            ],
            "name": "setHiddenMetadataUri",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x4fdd43cb"
        },
        "0xb071401b": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_maxMintAmountPerTx",
                    "type": "uint256"
                }
            ],
            "name": "setMaxMintAmountPerTx",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xb071401b"
        },
        "0x3c952764": {
            "inputs": [
                {
                    "internalType": "bool",
                    "name": "_state",
                    "type": "bool"
                }
            ],
            "name": "setOnlyWhitelisted",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x3c952764"
        },
        "0x16c38b3c": {
            "inputs": [
                {
                    "internalType": "bool",
                    "name": "_state",
                    "type": "bool"
                }
            ],
            "name": "setPaused",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x16c38b3c"
        },
        "0xb64ee2de": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_PreSaleWalletLimit",
                    "type": "uint256"
                }
            ],
            "name": "setPreSaleWalletLimit",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xb64ee2de"
        },
        "0xe0a80853": {
            "inputs": [
                {
                    "internalType": "bool",
                    "name": "_state",
                    "type": "bool"
                }
            ],
            "name": "setRevealed",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xe0a80853"
        },
        "0x2d7eae66": {
            "inputs": [
                {
                    "internalType": "bytes32",
                    "name": "_Root",
                    "type": "bytes32"
                }
            ],
            "name": "setRootHash",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x2d7eae66"
        },
        "0x7ec4a659": {
            "inputs": [
                {
                    "internalType": "string",
                    "name": "_uriPrefix",
                    "type": "string"
                }
            ],
            "name": "setUriPrefix",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x7ec4a659"
        },
        "0x16ba10e0": {
            "inputs": [
                {
                    "internalType": "string",
                    "name": "_uriSuffix",
                    "type": "string"
                }
            ],
            "name": "setUriSuffix",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x16ba10e0"
        },
        "0x01ffc9a7": {
            "inputs": [
                {
                    "internalType": "bytes4",
                    "name": "interfaceId",
                    "type": "bytes4"
                }
            ],
            "name": "supportsInterface",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "",
                    "type": "bool"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x01ffc9a7"
        },
        "0x95d89b41": {
            "inputs": [],
            "name": "symbol",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x95d89b41"
        },
        "0xc87b56dd": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_tokenId",
                    "type": "uint256"
                }
            ],
            "name": "tokenURI",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0xc87b56dd"
        },
        "0x18160ddd": {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x18160ddd"
        },
        "0x23b872dd": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "from",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "to",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "transferFrom",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x23b872dd"
        },
        "0xf2fde38b": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "newOwner",
                    "type": "address"
                }
            ],
            "name": "transferOwnership",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0xf2fde38b"
        },
        "0x62b99ad4": {
            "inputs": [],
            "name": "uriPrefix",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x62b99ad4"
        },
        "0x5503a0e8": {
            "inputs": [],
            "name": "uriSuffix",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x5503a0e8"
        },
        "0x438b6300": {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_owner",
                    "type": "address"
                }
            ],
            "name": "walletOfOwner",
            "outputs": [
                {
                    "internalType": "uint256[]",
                    "name": "",
                    "type": "uint256[]"
                }
            ],
            "stateMutability": "view",
            "type": "function",
            "signature": "0x438b6300"
        },
        "0xd2cab056": {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_mintAmount",
                    "type": "uint256"
                },
                {
                    "internalType": "bytes32[]",
                    "name": "_merkleProof",
                    "type": "bytes32[]"
                }
            ],
            "name": "whitelistMint",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function",
            "signature": "0xd2cab056"
        },
        "0x3ccfd60b": {
            "inputs": [],
            "name": "withdraw",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "signature": "0x3ccfd60b"
        }
    },
    "event": {
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": {
            "anonymous": false,
            "inputs": [
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "approved",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "Approval",
            "type": "event",
            "signature": "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
        },
        "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31": {
            "anonymous": false,
            "inputs": [
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "owner",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "operator",
                    "type": "address"
                },
                {
                    "indexed": false,
                    "internalType": "bool",
                    "name": "approved",
                    "type": "bool"
                }
            ],
            "name": "ApprovalForAll",
            "type": "event",
            "signature": "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31"
        },
        "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0": {
            "anonymous": false,
            "inputs": [
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "previousOwner",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "newOwner",
                    "type": "address"
                }
            ],
            "name": "OwnershipTransferred",
            "type": "event",
            "signature": "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0"
        },
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": {
            "anonymous": false,
            "inputs": [
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "from",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "internalType": "address",
                    "name": "to",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "Transfer",
            "type": "event",
            "signature": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        }
    },
    "contract_address": "0x62629A1Fd652E7701DCF5362c2e2d91290575631"
}'''
contract_dict = json.loads(contract_json)
db = DAIPoolDB()
db.execute_sql_code('''DELETE FROM fi
DELETE FROM fo
DELETE FROM ce
DELETE FROM ei
DELETE FROM t
DELETE FROM tfi
DELETE FROM tf
DELETE FROM tfo
DELETE FROM tei
DELETE FROM cf''')

db.insert_contract(contract_dict)

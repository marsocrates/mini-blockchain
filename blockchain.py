from hashlib import sha256
import gzip
import json
from tqdm.auto import tqdm

miner = "0x000a89667abeb2e87a42c724757ceee4cdc46eaa"

def serialize(block):
    string = ",".join([str(block[key]) for key in sorted(block)])
    return "0x" + sha256(string.encode()).hexdigest()

class MerkleTree:
    def __init__(self, value, sons=[], parent=None, leaves={}):
        self.value = value
        self.sons = sons
        self.parent = parent
        self.leaves = leaves
        for son in sons:
            son.parent = self

    @staticmethod
    def H(a,b):
        if a < b:
            return "0x"+sha256((a+b).encode()).hexdigest()
        else:
            return "0x"+sha256((b+a).encode()).hexdigest()
    
    @staticmethod
    def from_list_rec(hashs, leaves = {}):
        if len(hashs) == 0:
            raise ValueError("Cannot create merkle tree with empty transactions")
        if len(hashs) == 1:
            return hashs[0]
        new_hashs = []
        for i in range((len(hashs)+1)//2):
            if 2*i+1 < len(hashs):
                parent = MerkleTree(MerkleTree.H(hashs[2*i].value,hashs[2*i+1].value), sons=[hashs[2*i],hashs[2*i+1]],leaves=leaves)
            else:
                parent = MerkleTree(MerkleTree.H(hashs[2*i].value,"0x" + 64*"0"), sons=[hashs[2*i]], leaves=leaves)
            new_hashs.append(parent)
        return MerkleTree.from_list_rec(new_hashs, leaves=leaves)
    
    @staticmethod
    def from_list(hashs):
        leaves = {hash:MerkleTree(hash) for hash in hashs}
        return MerkleTree.from_list_rec(list(leaves.values()), leaves=leaves)

    def get_proof(self,hash):
        leaf = self.leaves[hash]
        proof = [hash]
        par = leaf.parent
        cur_hash = hash
        while par is not None:
            if len(par.sons) == 1:
                proof.append("0x"+64*"0")
            elif par.sons[0].value == cur_hash:
                proof.append(par.sons[1].value)
            elif par.sons[1].value == cur_hash:
                proof.append(par.sons[0].value)
            else:
                raise ValueError("probleme")
            par = par.parent
            cur_hash = MerkleTree.H(proof[-1],cur_hash)
        return proof
    
    @staticmethod
    def verify_proof(proof, merkle_root):
        cur_hash = proof[0]
        for comb_hash in proof[1:]:
            cur_hash = MerkleTree.H(cur_hash,comb_hash)
        return cur_hash == merkle_root
    
def create_blocks(mempool_file,blockchain_file, miner, blockchain_output, mempool_output, number=1):
    blockchain = read_json_gz(blockchain_file)
    mempool = read_json_gz(mempool_file)
    for i in range(number):
        prev_block = blockchain[-1]['header']
        transactions, mempool = select_n_transactions(mempool,50,prev_block['timestamp']+10)
        merkle = MerkleTree.from_list([serialize(transaction) for transaction in transactions])
        block_header = {
            "height":prev_block['height']+1,
            "previous_block_header_hash":prev_block['hash'],
            "timestamp":prev_block['timestamp']+10,
            "difficulty":min(6,(prev_block['height']+1)//50),
            "transactions_merkle_root":merkle.value,
            "transaction_count":len(transactions),
            "miner":miner,
            "nonce":0,
        }
        block_header = mine(block_header)
        block = {"header":block_header,"transactions":transactions}
        blockchain.append(block)
    write_json_gz(blockchain,blockchain_output)
    write_json_gz(mempool,mempool_output)

def proof_of_work(block):
    trailing = 0

    for i in range(block["difficulty"]):
        if block["hash"][2+trailing] != "0":
            return False
        trailing += 1
    return True

def mine(block):
    block["hash"] = serialize(block)
    pbar = tqdm()
    while not proof_of_work(block):
        pbar.update(1)
        block["nonce"] += 1
        block["hash"] = serialize(block)
    return block

def select_n_transactions(mempool, n, timestamp):
    sorted_transactions = sorted(mempool,key=lambda x: x["transaction_fee"])
    i = 0
    i_s = []
    transactions = []
    while len(transactions) < n and i < len(sorted_transactions):
        if sorted_transactions[i]["lock_time"] <= timestamp:
            transactions.append(sorted_transactions[i])
        i_s.append(i)
        i+=1
    for el in reversed(i_s):
        mempool.pop(el)
    return transactions, mempool

def get_trans_hash(blockchain_file,block_height,trans_number):
    blockchain = read_json_gz(blockchain_file)
    return serialize(blockchain[block_height]['transactions'][trans_number])

def read_json_gz(file_path):
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    return data

def write_json_gz(data, file_path):
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        json.dump(data, f)
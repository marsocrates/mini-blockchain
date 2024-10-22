import blockchain

blockchain_state = "data/blockchain.json.gz"

chain = blockchain.read_json_gz(blockchain_state)
block = chain[18]

transactions = block['transactions']

merkle = blockchain.MerkleTree.from_list([blockchain.serialize(transaction) for transaction in transactions])

print(merkle.value == block['header']['transactions_merkle_root'])

trans_hash = blockchain.serialize(transactions[7])

proof = merkle.get_proof(trans_hash)
print(merkle.value)
print("")

print(blockchain.MerkleTree.verify_proof(proof,merkle.value))
import click
import blockchain
import json

miner = "0x000a89667abeb2e87a42c724757ceee4cdc46eaa"


@click.group()
@click.option('--blockchain-state',default="blockchain.json.gz")
@click.pass_context
def blockchain_poc(ctx, blockchain_state):
    ctx.ensure_object(dict)
    ctx.obj['blockchain-state'] = blockchain_state

@blockchain_poc.command()
@click.option('--mempool', default="mempool.json.gz")
@click.option('--blockchain-output',default="new-blockchain.json.gz")
@click.option('--mempool-output',default="new-mempool.json.gz")
@click.option('-n','--number',default=1)
@click.pass_context
def produce_blocks(ctx, mempool,blockchain_output,mempool_output,number):
    blockchain_state = ctx.obj['blockchain-state']
    blockchain.create_blocks(mempool,blockchain_state,miner,blockchain_output,mempool_output,number)

@blockchain_poc.command()
@click.argument('block',type=click.INT)
@click.argument('transaction',type=click.INT)
@click.pass_context
def get_tx_hash(ctx, block,transaction):
    blockchain_state = ctx.obj['blockchain-state']
    print(blockchain.get_trans_hash(blockchain_state,block,transaction))

@blockchain_poc.command()
@click.argument('block',type=click.INT)
@click.argument('tx_hash',type=click.STRING)
@click.option('-o','--output',default="proof.json")
@click.pass_context
def generate_proof(ctx, block, tx_hash, output):
    blockchain_state = ctx.obj['blockchain-state']
    chain = blockchain.read_json_gz(blockchain_state)
    merkle = blockchain.MerkleTree.from_list([blockchain.serialize(transaction) for transaction in chain[block]["transactions"]])
    proof = merkle.get_proof(tx_hash)
    with open(output, 'wt', encoding='utf-8') as f:
        json.dump(proof, f)

@blockchain_poc.command()
@click.argument('file',type=click.Path(exists=True))
@click.pass_context
def verify_proof(ctx, file):
    blockchain_state = ctx.obj['blockchain-state']
    with open(file, 'rt', encoding='utf-8') as f:
        proof = json.load(f)
    chain = blockchain.read_json_gz(blockchain_state)
    for block in chain:
        if blockchain.MerkleTree.verify_proof(proof,block["header"]["transactions_merkle_root"]):
            print(True)
            return
    print(False)
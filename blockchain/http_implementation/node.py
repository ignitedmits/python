from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)
CORS(app)


@app.route('/',methods=['GET'])
def get_ui():
    return send_from_directory('ui','node.html')


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key == None:
        response = {
            'message' : 'No Wallet found'
        }
        return jsonify(response), 400
    values = request.get_json()
    if not values:
        response = {
            'message' : 'No Data Found'
        }
        return jsonify(response), 400
    required_fields = ['recipient', 'amount']
    if not all(fields in values for fields in required_fields):
        response = {
            'message' : 'Required Data missing'
        }
        return jsonify(response), 400
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount)
    if success:
        response = {
            'funds' : blockchain.get_balances(),
            'message' : 'Transaction Added Successfully',
            'transaction' : {
                'sender' : wallet.public_key,
                'recipient' : recipient,
                'amount' : amount,
                'signature' : signature                
            }
        }
        return jsonify(response), 500
    else:
        response = {
            'message' : 'Create Transaction Failed'
        }
        return jsonify(response), 500


@app.route('/wallet',methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'public_key' : wallet.public_key,
            'private_key' : wallet.private_key,
            'funds' : blockchain.get_balances()
        }
        return jsonify(response), 201
    else:
        response = {
            'message' : 'Keys failed to SAVE'
        }
        return jsonify(response), 500


@app.route('/transactions',methods=['GET'])
def get_open_transaction():
    transactions = blockchain.get_open_transaction()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), 200

@app.route('/wallet',methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'public_key' : wallet.public_key,
            'private_ket' : wallet.private_key,
            'funds' : blockchain.get_balances()
        }
        return jsonify(response), 201
    else:
        response = {
            'message' : 'Keys failed to LOAD'
        }
        return jsonify(response), 500


@app.route('/balance', methods=['GET'])
def get_balances():
    balance = blockchain.get_balances()
    if balance != None:
        response = {
            'message' : 'Fetching Balance Success',
            'funds' : blockchain.get_balances()
        }
        return jsonify(response), 200
    else:
        response = {
            'message' : 'Fetching Balance Failed',
            'wallet_set_up' : wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/mine', methods=['POST'])
def mine():
    block = blockchain.mine_block()
    if block != None:
        #print(block)
        dict_block = block.__dict__.copy()
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
        response = {
           'message' : 'Block added succesfully',
           'block ' : dict_block,
           'funds' : blockchain.get_balances()
        }
        return jsonify(response), 201
    else: 
        response = {
            'message' : 'Adding a block failed',
            'wallet_set_up' : wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/chain',methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
    return jsonify(dict_chain), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
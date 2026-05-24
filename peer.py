#import libraries
import base64
import json
from Blockchain import Blockchain
from Block import Block
from flask import Flask, request, Response

#app object
app = Flask(__name__)
#blockchain object
blockchain = Blockchain()
#peers list
peers = []

@app.route("/new_transaction", methods=["POST"])
# new transaction added to the block. When user selects to submit new request
def new_transaction():
    file_data = request.get_json() #get json response
    required_fields = ["user", "v_file", "file_data", "file_size"]
    #if any of the fields is missing dont append and throw the message
    for field in required_fields:
        if not file_data.get(field):
            return "Transaction does not have valid fields!", 404
    #else append it to pending transaction
    blockchain.add_pending(file_data)
    return "Success", 201

#gets the whole chain to user if not already displayed
@app.route("/chain", methods=["GET"])
def get_chain():
    # consensus()
    chain = []
    #create a new chain from our blockchain
    for block in blockchain.chain:
        chain.append(block.__dict__)
    #print chain len
    print("Chain Len: {0}".format(len(chain)))
    return json.dumps({"length" : len(chain), "chain" : chain})

@app.route("/", methods=["GET"])
def index():
    html = """
    <h1>Blockchain File Storage Node</h1>
    <p>Use the form below to upload a file to the blockchain pending pool.</p>
    <p><a href='/chain'>View chain</a> | <a href='/pending_tx'>Pending transactions</a> | <a href='/files'>View stored files</a></p>
    <form action='/upload' method='post' enctype='multipart/form-data'>
      <label>User name: <input type='text' name='user' value='anonymous'></label><br><br>
      <label>File: <input type='file' name='file'></label><br><br>
      <button type='submit'>Upload File</button>
    </form>
    """
    return html

@app.route("/upload", methods=["POST"])
def upload_file():
    user = request.form.get("user", "anonymous")
    file = request.files.get("file")
    if not file or file.filename == "":
        return "No file uploaded.", 400

    file_bytes = file.read()
    file_base64 = base64.b64encode(file_bytes).decode("utf-8")
    transaction = {
        "user": user,
        "v_file": file.filename,
        "file_data": file_base64,
        "file_size": len(file_bytes)
    }
    blockchain.add_pending(transaction)
    return "Upload successful. File transaction added to pending pool.", 201

@app.route("/download/<int:block_index>/<filename>", methods=["GET"])
def download_file(block_index, filename):
    if block_index < 0 or block_index >= len(blockchain.chain):
        return "Block not found.", 404

    block = blockchain.chain[block_index]
    for tx in block.transactions:
        if tx.get("v_file") == filename:
            file_data = base64.b64decode(tx.get("file_data", ""))
            return Response(
                file_data,
                mimetype="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    return "File not found in block.", 404

@app.route("/files", methods=["GET"])
def list_files():
    html = """
    <h1>Files Stored on Blockchain</h1>
    <p><a href='/'>Home</a> | <a href='/chain'>View chain</a> | <a href='/pending_tx'>Pending transactions</a></p>
    """
    if len(blockchain.chain) <= 1:
        html += "<p>No mined blocks yet. Upload a file and then mine to store it.</p>"
    else:
        for block in blockchain.chain[1:]:
            html += f"<h2>Block {block.index}</h2>"
            html += f"<p>Previous hash: {block.prev_hash}</p>"
            html += "<ul>"
            for tx in block.transactions:
                filename = tx.get('v_file', 'unnamed')
                user = tx.get('user', 'unknown')
                size = tx.get('file_size', 0)
                html += f"<li>{filename} ({size} bytes) by {user} - <a href='/download/{block.index}/{filename}'>Download</a></li>"
            html += "</ul>"
    return html
        
@app.route("/mine", methods=["GET"])
#Mines pending tx blocks and call mine method in blockchain
def mine_uncofirmed_transactions():
    result = blockchain.mine()
    if result:
        return "Block #{0} mined successfully.".format(result)
    else:
        return "No pending transactions to mine."
    


@app.route("/pending_tx")
# Queries uncofirmed transactions
def get_pending_tx():
    return json.dumps(blockchain.pending)



@app.route("/add_block", methods=["POST"])
# Adds a block mined by user to the chain
def validate_and_add_block():
    block_data = request.get_json() #get the json response
    #create a new block incl its hash
    block = Block(block_data["index"],block_data["transactions"],block_data["prev_hash"])
    hashl = block_data["hash"]
    #append the new block
    added = blockchain.add_block(block, hashl)
    #if not added succesfully
    if not added:
        return "The Block was discarded by the node.", 400
    return "The block was added to the chain.", 201
#run the app
if __name__ == "__main__":
    app.run(port=8800, debug=True)

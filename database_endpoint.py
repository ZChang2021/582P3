from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""

def log_message(d)
    # Takes input dictionary d and writes it to the Log table
    g.session.add(logtime = datetime.now(), message = json.dumps(d))
    g.session.commit()
    return

"""
---------------- Endpoints ----------------
"""
    
@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )
            
        #Your code here
        #Note that you can access the database session using g.session
        sig = content["sig"]
        signedInfo = json.dumps(content["payload"])
        
        sender_pk = content["payload"]["sender_pk"]
        receiver_pk = content["payload"]["receiver_pk"]
        buy_currency = content["payload"]["receiver_pk"]
        sell_currency = content["payload"]["sell_currency"]
        buy_amount = content["payload"]["buy_amount"]
        sell_amount = content["payload"]["sell_amount"]
        platform = content["payload"]["platform"]
        
        #check signature
        sig_verification = False
        if platform == "Ethereum":
            eth_encoded_msg = eth_account.messages.encode_defunct(text=signedInfo)
            if eth_account.Account.recover_message(eth_encoded_msg,signature=sig) == sender_pk:
    #             print( "Eth sig verifies!" )
                sig_verification = True
                g.session.add(Order(sender_pk=sender_pk, receiver_pk=receiver_pk, buy_currency=buy_currency, sell_currency=sell_currency, buy_amount=buy_amount, sell_amount=sell_amount, signature=sig))
        elif platform == "Algorand":
            if algosdk.util.verify_bytes(signedInfo.encode('utf-8'),sig,sender_pk):
    #             print( "Algo sig verifies!" )
                sig_verification = True
                g.session.add(Order(sender_pk=sender_pk, receiver_pk=receiver_pk, buy_currency=buy_currency, sell_currency=sell_currency, buy_amount=buy_amount, sell_amount=sell_amount, signature=sig))
            
        if sig_verification:
            g.session.commit()
        else:
            log_message(content)
            
    return jsonify(sig_verification)

@app.route('/order_book')
def order_book():
    #Your code here
    #Note that you can access the database session using g.session
    data = []
    for order in g.session.query(Order).all():
        data.append({'sender_pk': order.sender_pk, 'receiver_pk': order.receiver_pk, 'buy_currency': order.buy_currency, 'sell_currency': order.sell_currency, 'buy_amount': order.buy_amount, 'sell_amount': order.sell_amount, 'signature': order.signature})
    return jsonify(data=data)

if __name__ == '__main__':
    app.run(port='5002')

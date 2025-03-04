from flask import Flask, request, make_response, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import logging
import time
import Pyro5.api
import sys

from waitress import serve

import os

app = Flask(__name__)

nameserver_ip = os.environ.get('ENAMESERVER_IP')
tnameserver_port = os.environ.get('ENAMESERVER_PORT')

if (nameserver_ip == None or nameserver_ip == "") and (tnameserver_port == None or tnameserver_port == ""):
    print("Usage: nameserver_ip nameserver_port")
    exit(-1)

print(" 1st: " + str(nameserver_ip) + " 2nd: " + str(tnameserver_port))

if isinstance(tnameserver_port,str):
    nameserver_port = int(tnameserver_port)
else:
    nameserver_port = tnameserver_port

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

@app.errorhandler(429)
def ratelimit_handler(e):
    return make_response(
            jsonify(error=f"Rate limit exceeded: {e.description}")
            , 429
    )

# Route to serve the HTML page (client)
@app.route('/')
@limiter.limit("1/second", override_defaults=False)
def index():
    return render_template('index.html')

# Route to run a command
@app.route('/run_command', methods=['POST', 'OPTIONS'])
@limiter.limit("1 per 10 seconds", override_defaults=False, error_message="Only 1 request per 10 seconds allowed")
def run_command():

    # Get the password and configname from the request
    data = request.json
    username = data.get('username')
    password = data.get('password')
    configname = data.get('configname')
    command = data.get('command')
    cloneVMNames = []
    # Check if configname is provided
    if not configname:
        return jsonify({"error": "No Scenario Name Provided"}), 400

    try:
        # Connect to remote nameserver
        ns = Pyro5.api.locate_ns(nameserver_ip,nameserver_port)
        
        pEngine = Pyro5.api.Proxy(ns.lookup("engine"))
        pUserPool = Pyro5.api.Proxy(ns.lookup("userpool"))
        
        res = pEngine.execute("vm-manage mgrstatus")
        while res["writeStatus"] != 0:
            time.sleep(.1)
            logging.debug("Waiting for experiment start to complete...")
            res = pEngine.execute("vm-manage mgrstatus")

        usersConns = pUserPool.generateUsersConns(configname)
        if (username, password) in usersConns:
            vmInfos = usersConns[(username, password)]
        else:
            return jsonify({"error": "Invalid username or password"}), 403

        for vmInfo in vmInfos:
            cloneVMNames.append(vmInfo[0])
        
        # Execute command for each vm with rdp enabled and return result
        cmds = []
        output = ""
        if command == "start":
            for cloneVMName in cloneVMNames:
                cmds = []
                cmds.append("experiment start " + configname + " vm " + str(cloneVMName))
                for cmd in cmds:
                    pEngine.execute(cmd)
                    res = pEngine.execute("experiment status")
                    logging.debug("Waiting for experiment start to complete...")

                    while res["writeStatus"] != 0:
                        time.sleep(.1)
                        logging.debug("Waiting for experiment start to complete...")
                        res = pEngine.execute("experiment status")
                output = cmd + " Completed\n"

        elif command == "stop":
            for cloneVMName in cloneVMNames:
                cmds = []
                cmds.append("experiment stop " + configname + " vm " + str(cloneVMName))
                for cmd in cmds:
                    pEngine.execute(cmd)
                    res = pEngine.execute("vm-manage mgrstatus")
                    logging.debug("Waiting for experiment stop to complete...")
                    while res["writeStatus"] != 0:
                        time.sleep(.1)
                        logging.debug("Waiting for experiment stop to complete...")
                        res = pEngine.execute("experiment status")
                output = cmd + " Completed\n"

        elif command == "status":
            for cloneVMName in cloneVMNames:
                cmd = "vm-manage refresh " + str(cloneVMName)
                pEngine.execute(cmd)
                res = pEngine.execute("vm-manage mgrstatus")
                logging.debug("Waiting for vm refresh update to complete...")
                while res["writeStatus"] != 0:
                    time.sleep(.1)
                    logging.debug("Waiting for vm refresh update to complete...")
                    res = pEngine.execute("vm-manage mgrstatus")
                res = pEngine.execute("vm-manage vmstatus " + str(cloneVMName))
                vmName = os.path.basename(cloneVMName)
                if res == -1:
                    output += "VM: " + str(vmName) + ": missing\n"
                elif res != None and "vmState" in res and res["vmState"] != None and res["vmState"] != "" and "vmName" in res and res["vmName"] != None and res["vmName"] != "":
                    output += "VM: " + str(vmName) + ": " + str(res["vmState"] + "\n")
                else:
                    output += "VM: " + str(vmName) + ": Error Querying VM State\n"
                    
        elif command == "restore":
            for cloneVMName in cloneVMNames:
                cmds = []
                cmds.append("experiment stop " + configname + " vm " + str(cloneVMName))
                cmds.append("experiment restore " + configname + " vm " + str(cloneVMName))
                cmds.append("experiment start " + configname + " vm " + str(cloneVMName))
                for cmd in cmds:
                    pEngine.execute(cmd)
                    res = pEngine.execute("experiment status")
                    logging.debug("Waiting for experiment restore to complete...")
                    while res["writeStatus"] != 0:
                        time.sleep(.1)
                        logging.debug("Waiting for experiment restore to complete...")
                        res = pEngine.execute("experiment status")
                    output += cmd + " Completed\n"
                output += "\n"
        
        return jsonify({"output": output}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        #return jsonify({"error": str("The config name is incorrect or it does not exist")}), 500

# main driver function
if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    #app.run()
    #Use waitress to host
    serve(app, host="0.0.0.0", port=5000)
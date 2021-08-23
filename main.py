import requests
import json
from mac_vendor_lookup import MacLookup
import config
import time

pineapple_ip = config.pineapple_ip
api_token = config.api_token
wigle_api_name = config.wigle_api_name
wigle_api_token = config.wigle_api_token

with open("./ignorelist") as f:
    ignorelist_ssids = f.read().splitlines()

class WifiPineapple:
    
    def getSsidPool(self):

        getPoolJson = {
            "module": "PineAP",
            "action": "getPool",
            "apiToken": api_token
            }
        
        r = requests.post(pineapple_ip, data=json.dumps(getPoolJson), verify=False)
        
        response = json.loads(r.text[5:])
        response = response["ssidPool"].split("\n")
        
        for i in response[:]:
            if i in ignorelist_ssids:
                response.remove(i)

        response.remove("")

        return response
    
    def listScanResults(self):
        listScanResultsJson = {
            "module":"Recon",
            "action":"getScans",
            "apiToken": api_token
            }
        
        r = requests.post(pineapple_ip, data=json.dumps(listScanResultsJson), verify=False)
        response = json.loads(r.text[5:])
        for i in response["scans"]:
            print(i)
    
    def clearSSIDPool(self):
        clearPoolJson = {
            "module": "PineAP",
            "action": "clearPool",
            "apiKey": apiKey
            }
        r = requests.post(pineapple_ip, data=json.dumps(listScanResultsJson), verify=False)
        
    def getUnassociatedClients(self, scanID):
        mac = MacLookup()
        
        getUnassociatedClientsJson = {
            "module":"Recon",
            "action":"loadResults",
            "scanID":scanID,
            "apiToken": api_token
            }

        r = requests.post(pineapple_ip, data=json.dumps(getUnassociatedClientsJson), verify=False)
        response = json.loads(r.text[5:])
        response = response["results"]["ap_list"]
        
        for i in response:
            try:
                mac_vendor = MacLookup().lookup(i["bssid"])
            except:
                mac_vendor = "None"

            i["bssid_vendor"] = mac_vendor
        
        print(response)
        
        fileName = "./results/Unassociated_Clients_{}.json".format(scanID)
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)        

    def getScanResults(self, scanID):
        mac = MacLookup()
        
        getScanResultsJson = {
            "module":"Recon",
            "action":"loadResults",
            "scanID": scanID,
            "apiToken": api_token
            }

        r = requests.post(pineapple_ip, data=json.dumps(getScanResultsJson), verify=False)
        response = json.loads(r.text[5:])
        response = response["results"]["ap_list"]

        # it takes a little more work to look up mac addresses in scan results
        for i in response:
            try:
                mac_vendor = MacLookup().lookup(i["bssid"])
            except:
                mac_vendor = "None"

            i["bssid_vendor"] = mac_vendor
            
            # this looks up any vendors connected to an AP
            if i["clients"]:
                for j in i["clients"]:
                    try:
                        mac_vendor = MacLookup().lookup(j["mac"])
                    except:
                        mac_vendor = "None"
                    j["mac_vendor"] = mac_vendor

        print(response)

        fileName = "./results/Scan_Results_{}.json".format(scanID)
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)

class WigleAPI:
    
    # generate a file with the history of one ssid
    def getSsidHistory(self, ssid, resultsToReturn):
        print(ssid)
        headers = {
            'accept': 'application/json',
            }
        
        params = (
            ('onlymine', 'false'),
            ('freenet', 'false'),
            ('paynet', 'false'),
            ('ssid', ssid),
            ('resultsPerPage', resultsToReturn),
            )
        
        response = requests.get('https://api.wigle.net/api/v2/network/search', 
                                headers=headers, 
                                params=params, 
                                auth=(wigle_api_name,wigle_api_token)).json()
        
        fileName = "./results/WiFi_History_{}.json".format(ssid)
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)
        
    # generate a file that has geolocation information for each ssid in the pool
    def generateGeolocatedSSIDs(self, ssids, clearPoolOption):
        print(ssids)
        
        wigle_results = []
    
        for i in response:
            headers = {
                'accept': 'application/json',
                }
            
            params = (
                ('onlymine', 'false'),
                ('freenet', 'false'),
                ('paynet', 'false'),
                ('ssid', i),
                ('resultsPerPage', '1'),
                )
            
            response = requests.get('https://api.wigle.net/api/v2/network/search', headers=headers, params=params, auth=(wigle_api_name,wigle_api_token)).json()
            print(response)
            wigle_results.append(json.dumps(response))
            
        print(wigle_results)
        
        # get the current time in seconds and add it to the file name
        fileName = "./results/Wigle_Results_{}.json".format(str(int(round(time.time() * 1000))))
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)


        # now that we have it saved, clear out the ssid pool
        if(clearPoolOption == "y"):
            wp = WifiPineapple()
            wp.clearSSIDPool()

            
if __name__ == "__main__":

    wp = WifiPineapple()
    wigle = WigleAPI()
    
    txt = ""

    while txt != "0":
        print("1. Get SSID's")
        print("2. List Scan Results")
        print("3. Generate Unassociated Clients File")
        print("4. Get WiFi History")
        print("5. Generate Scan Results File")
        print("9. Update MAC Vendor DB")
        print("10. Geolocate SSID's")
        print("0. Quit")
        txt = input("\nEnter your input: ")
        
        if(txt == "1"):        
            response = wp.getSsidPool()
            print(response)
        elif(txt == "2"):
            wp.listScanResults()
        elif(txt == "3"):
            scan_id = input("Scan ID: ")
            wp.getUnassociatedClients(scan_id)
        elif(txt == "4"):
            wifiName = input("WiFi Name: ")
            resultsToReturn = input("Number Of Results To Return: ")
            wigle.getSsidHistory(wifiName, resultsToReturn)
        elif(txt == "5"):
            scan_id = input("Scan ID: ")
            wp.getScanResults(scan_id)
        elif(txt == "9"):
            mac = MacLookup()
            mac.update_vendors()
        elif(txt == "10"):
            response = wp.getSsidPool()
            clearPoolOption = input("Clear SSID pool after generating file(y/n)?")
            wigle.generateGeolocatedSSIDs(response, clearPoolOption)
        elif(txt == "0"):
            break
        else:
            print("Option Not Available")

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

class bgcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class WifiPineapple:

    def getSsidPool(self):

        getPoolJson = {
            "module": "PineAP",
            "action": "getPool",
            "apiToken": api_token
            }

        r = requests.post(pineapple_ip, data=json.dumps(
            getPoolJson), verify=False)

        response = json.loads(r.text[5:])
        response = response["ssidPool"].split("\n")

        for i in response[:]:
            if i in ignorelist_ssids:
                response.remove(i)

        response.remove("")

        ssid_file = open("ssids.txt", "a")
        for i in response:
            ssid_file.write(i + "\n")
        ssid_file.close()

        print(bgcolors.OKGREEN + "\nYou can now delete the SSID pool info\nFile written to: ./ssids.txt\n" + bgcolors.ENDC)

        # return the results but not doing anything with them
        return response

    def listScanResults(self):
        listScanResultsJson = {
            "module": "Recon",
            "action": "getScans",
            "apiToken": api_token
            }

        r = requests.post(pineapple_ip, data=json.dumps(
            listScanResultsJson), verify=False)
        response = json.loads(r.text[5:])
        
        print("\n")
        for i in response["scans"]:
            print(i)
        print("\n")


    def getUnassociatedClients(self, scanID):
        mac = MacLookup()

        getUnassociatedClientsJson = {
            "module": "Recon",
            "action": "loadResults",
            "scanID": scanID,
            "apiToken": api_token
            }

        r = requests.post(pineapple_ip, data=json.dumps(
            getUnassociatedClientsJson), verify=False)
        response = json.loads(r.text[5:])
        response = response["results"]["unassociated_clients"]

        for i in response:
            try:
                mac_vendor = MacLookup().lookup(i["mac"])
            except:
                mac_vendor = "None"

            i["mac_vendor"] = mac_vendor

        #print(response)

        fileName = "./results/Unassociated_Clients_{}.json".format(scanID)
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)
        
        
        print(bgcolors.OKGREEN + "\nSet host as unassociated-clients\nFile written to: ./results/Unassociated_Clients_{}.json\n".format(scanID) + bgcolors.ENDC)

    def getScanResults(self, scanID):
        mac = MacLookup()

        getScanResultsJson = {
            "module": "Recon",
            "action": "loadResults",
            "scanID": scanID,
            "apiToken": api_token
            }

        r = requests.post(pineapple_ip, data=json.dumps(
            getScanResultsJson), verify=False)
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
        
        # this is just for printing the response
        #print(response)

        fileName = "./results/Scan_Results_{}.json".format(scanID)
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)

        print(bgcolors.OKGREEN + "\nSet host as scan-results\nFile written to: ./results/Scan_Results_{}.json\n".format(scanID) + bgcolors.ENDC)

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
                                auth=(wigle_api_name, wigle_api_token)).json()

        fileName = "./results/WiFi_History_{}.json".format(ssid)
        with open(fileName, 'w') as outfile:
            json.dump(response, outfile)

    # generate a file that has geolocation information for each ssid in the pool
    def generateGeolocatedSSIDs(self):

        ssids = [] # store the ssids from the local file
        wigle_results = [] # results from the wigle lookup

        # get the first 25 lines from the ssid file since wigle seems to allow 100 lookups per day
        with open("ssids.txt", "r") as file:
            for i in range(25):
                line = next(file).strip("\n")
                ssids.append(line)

        print(ssids)
        print(len(ssids))

        for i in ssids:
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

            response = requests.get('https://api.wigle.net/api/v2/network/search',
                                    headers=headers, params=params, auth=(wigle_api_name, wigle_api_token)).json()
            print(response)

            if(response["success"] == True):
                wigle_results.append(response)
            else:
                print(i)

        print(wigle_results)

        # get the current time in seconds and add it to the file name
        fileName="./results/Wigle_Results_{}.json".format(
            str(int(round(time.time() * 1000))))

        with open(fileName, 'w') as outfile:
            json.dump(wigle_results, outfile)

        print(bgcolors.OKGREEN + "\nSet host as wifi-probes\nDelete top {} lines\nFile written to: {}".format(len(wigle_results),fileName) + bgcolors.ENDC)

if __name__ == "__main__":

    wp=WifiPineapple()
    wigle=WigleAPI()

    txt=""

    while txt != "0":
        print("1. Get SSID's")
        print("2. List Scan Results")
        print("3. Generate Unassociated Clients File")
        print("4. Get WiFi History")
        print("5. Generate Scan Results File")
        print("9. Update MAC Vendor DB")
        print("10. Geolocate SSID's")
        print("0. Quit")
        txt=input("\nEnter your input: ")

        if(txt == "1"):
            response=wp.getSsidPool()

        elif(txt == "2"):
            wp.listScanResults()

        elif(txt == "3"):
            scan_id=input("Scan ID: ")
            wp.getUnassociatedClients(scan_id)

        elif(txt == "4"):
            wifiName=input("WiFi Name: ")
            resultsToReturn=input("Number Of Results To Return: ")
            wigle.getSsidHistory(wifiName, resultsToReturn)

        elif(txt == "5"):
            scan_id=input("Scan ID: ")
            wp.getScanResults(scan_id)

        elif(txt == "9"):
            mac=MacLookup()
            mac.update_vendors()

        elif(txt == "10"):
            #response=wp.getSsidPool()
            #wigle.generateGeolocatedSSIDs(response)
            # taking this out for now since we'll get the ssids from the text file

            wigle.generateGeolocatedSSIDs()

        elif(txt == "0"):
            break

        else:
            print("Option Not Available")

# Copyright 2019 Dylian Melgert
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
<plugin key="GoodWeSEMS" name="GoodWe solar inverter via SEMS API" version="1.0.0" author="dylian94">
    <description>
        <h2>GoodWe inverter (via SEMS portal)</h2>
        <p>This plugin uses the GoodWe SEMS api to retrieve the status information of your GoodWe inverter.</p>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>temperature - Inverter temperature (Celcius)</li>
            <li>power - Ooutput power (Watts)</li>
            <li>current - Output current (ampere)</li>
            <li>voltage - Output Voltage</li>
        </ul>
        <h3>Configuration</h3>
        <ul>
            <li>Register your inverter at GoodWe SEMS portal (if not done already): <a href="https://www.semsportal.com">https://www.semsportal.com</a></li>
            <li>Choose one of the following options:</li>
            <ol type="a">
                <li>If you want all of your stations added to Domoticz you only have to enter your login information below</li>
                <li>If you want to add one specific station to Domoticz follow the following steps:</li>
                <ol>
                    <li>Login to your account on: <a href="https://www.semsportal.com">www.semsportal.com</a></li>
                    <li>Go to the plant status page for the station you want to add to Domoticz</li>
                    <li>Get the station ID from the URL, this is the sequence of characters after: https://www.semsportal.com/PowerStation/PowerStatusSnMin/</li>
                    <li>Add the station ID to the hardware configuration</li>
                </ol>
            </ol>
        </ul>
    </description>
    <params>
        <param field="Address" label="SEMS Server" width="200" required="true">
            <options>
                <option label="Europe" value="eu.goodwe-power.com"/>
                <option label="Australia" value="au.goodwe-power.com"/>
                <option label="Global" value="www.goodwe-power.com" default="true"/>
            </options>
        </param>
        <param field="Port" label="SEMS API port" width="30px" required="true" default="82"/>
        <param field="Username" label="E-Mail address" width="200" required="true"/>
        <param field="Password" label="Password" width="200" required="true" password="true"/>
        <param field="Mode1" label="Power Station ID (Optional)" width="200"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import json
import Domoticz


class GoodWeSEMSPlugin:
    httpConn = None
    runAgain = 6
    disconnectCount = 0
    tokenAvailable = False
    token = {
        "uid": "",
        "timestamp": 0,
        "token": "",
        "client": "web",
        "version": "",
        "language": "en-GB"
    }
    powerStationList = {}
    powerStationIndex = 0
    baseDeviceIndex = 0

    def __init__(self):
        return

    def apiRequestHeaders(self):
        return {
            'Content-Type': 'application/json; charset=utf-8',
            'Connection': 'keep-alive',
            'Accept': 'Content-Type: application/json; charset=UTF-8',
            'Host': Parameters["Address"] + ":" + Parameters["Port"],
            'User-Agent': 'Domoticz/1.0',
            'token': json.dumps(self.token)
        }

    def apiConnection(self):
        return Domoticz.Connection(Name="SEMS Portal API", Transport="TCP/IP", Protocol="HTTP", Address=Parameters["Address"], Port=Parameters["Port"])

    def tokenRequest(self):
        return {
                    'Verb': 'POST',
                    'URL': '/api/v2/Common/CrossLogin',
                    'Data': json.dumps({
                        "account": Parameters["Username"],
                        "pwd": Parameters["Password"],
                        "is_local": True,
                        "agreement_agreement": 1
                    }),
                    'Headers': self.apiRequestHeaders()
                }

    def stationListRequest(self):
        return {
            'Verb': 'POST',
            'URL': '/api/v2/HistoryData/QueryPowerStationByHistory',
            'Data': '{}',
            'Headers': self.apiRequestHeaders()
        }

    def stationDataRequest(self):
        return {
            'Verb': 'POST',
            'URL': '/api/v2/PowerStation/GetMonitorDetailByPowerstationId',
            'Data': json.dumps({
                "powerStationId": self.powerStationList[self.powerStationIndex]
            }),
            'Headers': self.apiRequestHeaders()
        }

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            DumpConfigToLog()

        self.httpConn = self.apiConnection()
        self.httpConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Connected to SEMS portal API successfully.")
            if not self.tokenAvailable:
                self.powerStationList = {}
                self.powerStationIndex = 0
                Connection.Send(self.tokenRequest())
            else:
                Connection.Send(self.stationDataRequest())
        else:
            Domoticz.Log("Failed to connect (" + str(Status) + ") to: " + Parameters["Address"] + ":" + Parameters["Port"] + " with error: " + Description)

    def onMessage(self, Connection, Data):
        responseText = Data["Data"].decode("utf-8", "ignore")
        status = int(Data["Status"])

        if status == 200:
            apiRresponse = json.loads(responseText)
            apiUrl = apiRresponse["components"]["api"]
            apiData = apiRresponse["data"]

            if "api/v2/Common/CrossLogin" in apiUrl:
                self.token = apiData
                Domoticz.Log("SEMS API Token: " + json.dumps(self.token))
                self.tokenAvailable = True

                if len(Parameters["Mode1"]) > 0:
                    self.powerStationList.update({0: Parameters["Mode1"]})
                    Connection.Send(self.stationDataRequest())
                else:
                    Connection.Send(self.stationListRequest())

            elif "/api/v2/HistoryData/QueryPowerStationByHistory" in apiUrl:
                for key, station in enumerate(apiData["list"]):
                    self.powerStationList.update({key: station["id"]})
                    Domoticz.Log("Station found: " + station["id"])

                Connection.Send(self.stationDataRequest())

            elif "api/v2/PowerStation/GetMonitorDetailByPowerstationId" in apiUrl:
                if apiData is None:
                    Domoticz.Log("No station data received from GoodWe SEMS API (Station ID: " + self.powerStationList[self.powerStationIndex] + ")")
                    self.tokenAvailable = False
                else:
                    Domoticz.Log("Station data received from GoodWe SEMS API (Station ID: " + self.powerStationList[self.powerStationIndex] + ")")

                    for inverter in apiData["inverter"]:
                        if len(Devices) <= self.baseDeviceIndex:
                            Domoticz.Device(Name="Solar inverter temperature (SN: " + inverter["sn"] + ")", Unit=(self.baseDeviceIndex + 1), Type=80, Subtype=5).Create()
                            Domoticz.Device(Name="Solar inverter output current (SN: " + inverter["sn"] + ")", Unit=(self.baseDeviceIndex + 2), Type=243, Subtype=23).Create()
                            Domoticz.Device(Name="Solar inverter output voltage (SN: " + inverter["sn"] + ")", Unit=(self.baseDeviceIndex + 3), Type=243, Subtype=8).Create()
                            Domoticz.Device(Name="Solar inverter output power (SN: " + inverter["sn"] + ")", Unit=(self.baseDeviceIndex + 4), Type=243, Subtype=29).Create()
                            Domoticz.Log("Devices created for GoodWe inverter (SN: " + inverter["sn"] + ")")

                        Devices[self.baseDeviceIndex + 1].Update(nValue=0, sValue=str(inverter["tempperature"]))
                        Devices[self.baseDeviceIndex + 2].Update(nValue=0, sValue=str(inverter["output_current"]))
                        Devices[self.baseDeviceIndex + 3].Update(nValue=0, sValue=str(inverter["output_voltage"]))
                        Devices[self.baseDeviceIndex + 4].Update(nValue=0, sValue=str(inverter["output_power"]) + ";" + str(inverter["etotal"]))
                        self.baseDeviceIndex += 4

                if self.powerStationIndex == (len(self.powerStationList) - 1):
                    Domoticz.Log("Disconnecting and dropping connection.")
                    self.httpConn.Disconnect()
                    self.httpConn = None
                    self.baseDeviceIndex = 0
                else:
                    Domoticz.Log("Retrieving next station data (ID: " + self.powerStationList[self.powerStationIndex] + ")")
                    self.baseDeviceIndex += 1
                    Connection.Send(self.stationDataRequest())

        elif status == 302:
            Domoticz.Log("GoodWe SEMS API returned a Page Moved Error.")
        elif status == 400:
            Domoticz.Error("GoodWe SEMS API returned a Bad Request Error.")
        elif (status == 500):
            Domoticz.Error("GoodWe SEMS API returned a Server Error.")
        else:
            Domoticz.Error("GoodWe SEMS API returned a status: " + str(status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called for connection to: " + Connection.Address + ":" + Connection.Port)

    def onHeartbeat(self):
        if self.httpConn is not None and (self.httpConn.Connecting() or self.httpConn.Connected()):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if self.httpConn is None:
                    self.httpConn = self.apiConnection()
                self.httpConn.Connect()
                self.runAgain = 6
            else:
                Domoticz.Debug("onHeartbeat called, run again in " + str(self.runAgain) + " heartbeats.")


global _plugin
_plugin = GoodWeSEMSPlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"] + "http.html", "w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details (" + str(len(httpDict)) + "):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("--->'" + x + " (" + str(len(httpDict[x])) + "):")
                for y in httpDict[x]:
                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")

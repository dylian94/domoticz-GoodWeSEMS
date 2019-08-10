Domoticz GoodWe Solar Inverter plugin (SEMS API)
===============================================
This plugin provides information about your GoodWe solar inverter too Domoticz. This plugin has been made by analysing requests made by the GoodWe SEMS Portal website and following the API documentation provided by GoodWe.

Installation and setup
----------------------
Follow the Domoticz guide on [Using Python Plugins](https://www.domoticz.com/wiki/Using_Python_plugins).

Login to a shell, go to the domoticz plugin directory and clone this repository:
```bash
cd domoticz/plugins
git clone https://github.com/dylian94/domoticz-GoodWeSEMS.git
```

Restart Domoticz server, you can try one of these commands (on Linux):
```bash
sudo systemctl restart domoticz.service
sudo service domoticz.sh restart
```

Open the Domoticz interface and go to: **Setup** > **Hardware**. You can add new Hardware add the bottom, in the list of hardware types choose for: **GoodWe inverter (via SEMS portal)**.

Follow the instructions shown in the form.

Updating
--------
Login to a shell, go to the plugin directory inside the domoticz plugin directory and execute git pull:
```bash
cd domoticz/plugins
cd domoticz-GoodWeSEMS
git pull
```

Contributing
------------
Even if you do not know how to develop software you can help by using the [GitHub Issues](https://github.com/dylian94/domoticz-GoodWeSEMS/issues)
for feature request or bug reports. If you DO know how to develop software please help improving this project by submitting pull-requests.

Current features
----------------
1. Get all stations for a specific user account
2. Automatically get data for all inverters (for one or all stations)
3. The following devices are added to Domoticz for each inverter:
    - temperature: Inverter temperature (Celcius)
    - power: Current and total output power (Watts)
    - current - Output current (ampere)
    - voltage - Output Voltage

There is a lot more information available trough the GooWe API if you would like to have a specific feature added too this plugin please submit an issue as indicated in the paragraph above. 
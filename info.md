# Home Assistant Integration for zhimi.heaters
  Modified component what was not correctly worked in HASS new version.
  Tested on zhimi.heater.mc2
  Tested on zhimi.heater.zb1
  Tested on zhimi.heater.za2 (some issues reported)



### Install through HACS:

Add a custom repository in HACS pointed to https://github.com/ee02217/homeassistant-mi-heater

The new integration for miHeater should appear under your integrations tab.

Click Install and restart Home Assistant.

### Install manually:

Copy the contents found in https://github.com/ee02217/homeassistant-mi-heater/tree/master/custom_components/miheater/ to your custom_components folder in Home Assistant.

Restart Home Assistant.

### Configuration.yaml

````
climate:
  - platform: miheater
    host: <your device ip address>
    token: <your device miio token>
    name: xiaomi_heater
    model: zhimi.heater.mc2 (optional: zhimi.heater.mc2 | zhimi.heater.zb1 | zhimi.heater.za2)
````


### Features

  supporting power on/off
  supporting setting temperature
  supporting read temperature from device



### Notice
token must got from APP miio2.db, not from "miio discover" on PC

### TODO

- make device detection in code persistent (instead of querying device everytime
- improve documentation and service description
- <s>make hacs compatible</s>

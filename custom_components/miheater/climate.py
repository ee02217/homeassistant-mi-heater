"""
    Support for Xiaomi wifi-enabled home heaters via miio.
    author: sunfang1cn@gmail.com
    modifier: ee02217
    Tested environment: HASS 0.118.5
"""
import logging

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    DOMAIN, HVAC_MODE_HEAT,HVAC_MODE_COOL, HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE)
from homeassistant.const import (
    ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, CONF_TOKEN, CONF_DEVICE_ID,
    STATE_ON, STATE_OFF, TEMP_CELSIUS)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import PlatformNotReady

from miio import Device,DeviceException



_LOGGER = logging.getLogger(__name__)

CONF_MODEL = 'model'
REQUIREMENTS = ['python-miio>=0.5.0']
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE)
SERVICE_SET_ROOM_TEMP = 'miheater_set_room_temperature'
PRECISION = 1
MIN_TEMP = 18
MAX_TEMP = 28
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_DEVICE_ID): cv.string,
    vol.Optional(CONF_MODEL, default=None): vol.In(
    ['zhimi.heater.mc2',
     'zhimi.heater.zb1',
     'zhimi.heater.za2', None]),
})

SET_ROOM_TEMP_SCHEMA = vol.Schema({
    vol.Optional('temperature'): cv.positive_int
})

DEVICE_MODEL = ""
ATTR_MODEL = 'model'
DEVICE_ID = ""

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Xiaomi heaters."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    model = config.get(CONF_MODEL)
    DEVICE_ID = config.get(CONF_DEVICE_ID)

    _LOGGER.info("Initializing Xiaomi heaters with host %s (token %s...)", host, token[:5])

    devices = []
    unique_id = None

    try:
        device = Device(host, token)
        device_info = device.info()
        
        if model is None:
            
            model = device_info.model
            DEVICE_MODEL = model

        unique_id = "{}-{}".format(model, device_info.mac_address)
        _LOGGER.warning("%s %s %s detected",
                     model,
                     device_info.firmware_version,
                     device_info.hardware_version)
        miHeater = MiHeater(device, name, model, unique_id, hass)
        devices.append(miHeater)
        add_devices(devices)


        async def set_room_temp(service):
            """Set room temp."""
            
            if DEVICE_MODEL == "zhimi.heater.mc2":
                aux = device.raw_command('get_properties', [{"siid":2,"piid":5,"did":DEVICE_ID}])
            elif DEVICE_MODEL == "zhimi.heater.zb1" or DEVICE_MODEL == "zhimi.heater.za2":
                aux = device.raw_command('get_properties', [{"siid":2,"piid":6}])
            else  :  
                _LOGGER.exception('Unsupported model: %s', DEVICE_MODEL)

            temperature=aux[0]["value"]
            await miHeater.async_set_temperature(temperature)

        hass.services.async_register(DOMAIN, SERVICE_SET_ROOM_TEMP,
                                     set_room_temp, schema=SET_ROOM_TEMP_SCHEMA)
    except DeviceException:
        _LOGGER.exception('Fail to setup Xiaomi heater')
        raise PlatformNotReady



class MiHeater(ClimateEntity):
    """Representation of a MiHeater device."""

    def __init__(self, device, name, model, unique_id, _hass):
        """Initialize the heater."""
        self._device = device
        self._name = name
        self._model = model
        self._state = None
        self.entity_id = generate_entity_id('climate.{}', unique_id, hass=_hass)
        self.getAttrData()
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def device(self):
        """Return the model of the device."""
        return self._model
        
    @property
    def hvac_mode(self):
        return HVAC_MODE_HEAT if self._state['power'] else HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]


    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS
    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    # @property
    # def precision(self):
    #     """Return the unit of measurement which this thermostat uses."""
    #     return PRECISION

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._state['target_temperature']

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._state['current_temperature']

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._state['humidity']


    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1
    def getAttrData(self):

        try: 
            _LOGGER.warning( self._device.get_properties(['current_temperature'], 1))
        except DeviceException:
            _LOGGER.exception('Fail to get_prop from Xiaomi heater')

        try:
            data = {}

            #device_info = self._device.info()
            #DEVICE_MODEL = device_info.model
               
            if self._model == "zhimi.heater.mc2":
                power=self._device.raw_command('get_properties', [{"did":DEVICE_ID,"siid":2,"piid":1}])
                target_temperature=self._device.raw_command('get_properties', [{"did":DEVICE_ID,"siid":2,"piid":5}])
                current_temperature=self._device.raw_command('get_properties', [{"did":DEVICE_ID,"siid":4,"piid":7}])
                data['humidity']  = 0
            elif self._model == "zhimi.heater.zb1" or self._model == "zhimi.heater.za2" :
                power=self._device.raw_command('get_properties', [{"siid":2,"piid":2}])
                humidity=self._device.raw_command('get_properties', [{"siid":5,"piid":7}])
                target_temperature=self._device.raw_command('get_properties', [{"siid":2,"piid":6}])
                current_temperature=self._device.raw_command('get_properties', [{"siid":5,"piid":8}])
                data['humidity'] = humidity[0]["value"]
            else:  
                _LOGGER.exception('Unsupported model: %s', self._model)

            data['power'] = power[0]["value"]
            
            data['target_temperature'] = target_temperature[0]["value"]
            data['current_temperature'] = current_temperature[0]["value"]
            self._state = data
        except DeviceException:
            _LOGGER.exception('Fail to get_prop from Xiaomi heater')
            self._state = None
            raise PlatformNotReady

    @property
    def device_state_attributes(self):
        return self._state

    @property
    def is_on(self):
        """Return true if heater is on."""
        return self._state['power']

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return MAX_TEMP

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.warning("Setting temperature: %s", int(temperature))
        if temperature is None:
            _LOGGER.error("Wrong temperature: %s", temperature)
            return

        #device_info = self._device.info()
        #DEVICE_MODEL = device_info.model      
        
        if self._model == "zhimi.heater.mc2":              
            self._device.raw_command('set_properties',[{"value":int(temperature),"siid":2,"piid":5, "did":DEVICE_ID}])
        elif self._model == "zhimi.heater.zb1" or self._model == "zhimi.heater.za2" :
            self._device.raw_command('set_properties',[{"value":int(temperature),"siid":2,"piid":6}])
        else:  
            _LOGGER.exception('Unsupported model: %s', self._model)

    async def async_turn_on(self):
        """Turn Mill unit on."""

        #device_info = self._device.info()
        #DEVICE_MODEL = device_info.model      
        
        if self._model == "zhimi.heater.mc2":              
            self._device.raw_command('set_properties',[{"value":True,"siid":2,"piid":1, "did":DEVICE_ID}])
        elif self._model == "zhimi.heater.zb1" or self._model == "zhimi.heater.za2" :
            self._device.raw_command('set_properties',[{"value":True,"siid":2,"piid":2}])
        else:  
            _LOGGER.exception('Unsupported model: %s', self._model)        
        

    async def async_turn_off(self):
        """Turn Mill unit off."""
        #device_info = self._device.info()
        #DEVICE_MODEL = device_info.model      
        
        if self._model == "zhimi.heater.mc2":              
            self._device.raw_command('set_properties',[{"value":False,"siid":2,"piid":1, "did":DEVICE_ID}])
        elif self._model == "zhimi.heater.zb1" or self._model == "zhimi.heater.za2" :
            self._device.raw_command('set_properties',[{"value":False,"siid":2,"piid":2}])
        else:  
            _LOGGER.exception('Unsupported model: %s', self._model)    
        
    async def async_update(self):
        """Retrieve latest state."""
        self.getAttrData()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        if hvac_mode  == HVAC_MODE_HEAT or hvac_mode  == HVAC_MODE_COOL:
            await self.async_turn_on()
        elif hvac_mode  == HVAC_MODE_OFF:
            await self.async_turn_off()
        else:
            _LOGGER.error("Unrecognized operation mode: %s", hvac_mode)
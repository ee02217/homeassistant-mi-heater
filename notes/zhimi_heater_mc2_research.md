# zhimi.heater.mc2 online research attempt

## Summary

Attempts to access external sources for the `zhimi.heater.mc2` MiOT spec or documentation failed with a `Forbidden` response from the network proxy. This prevented collecting the device feature list from online sources.

## Commands and outputs

```bash
curl -L "http://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:heater:0000A018:zhimi-mc2:1" -o /tmp/zhimi_mc2.json
```

Output:

```
Forbidden
```

```bash
curl -L "http://raw.githubusercontent.com/rytilahti/python-miio/master/miio/miot/specs/zhimi.heater.mc2.json" -o /tmp/zhimi_mc2.json
```

Output:

```
Forbidden
```

```bash
curl -L "http://example.com" -o /tmp/example.html
```

Output:

```
Forbidden
```

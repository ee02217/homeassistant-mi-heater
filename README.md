# Xiaomi miHeater Integration for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

Welcome to a feature-rich Xiaomi heater integration that makes your winter setup feel smart, cozy, and effortless. This custom component uses the MiOT protocol and brings rich device controls directly into Home Assistant.

## ✅ Supported models
* **zhimi.heater.mc2** — Xiaomi Smart Space Heater S
* **zhimi.heater.mc2a** — Xiaomi Smart Space Heater S (variant)
* **zhimi.heater.zb1** — Xiaomi Mi Smart Space Heater 1S
* **zhimi.heater.za2** — Xiaomi Smart Space Heater 1S
* **leshow.heater.bs1s** — Leshow Smart Heater

If your heater reports a different model, open an issue with the model string and we can add it.

## ✨ Features
**Core climate control**
* Power on/off (HVAC mode)
* Target temperature control
* Current temperature reporting
* Configurable min/max temperature range per model

**Device extras**
* Buzzer toggle (where supported)
* Child lock toggle (where supported)
* LED indicator brightness (On/Off/Dim — Dim is supported on zhimi.heater.za2)
* Delay-off timer with bounds per model
* Humidity reporting (where supported)

**Home Assistant UX**
* Config flow with automatic device model detection
* Manual model selection via a pick list of supported models
* Extra state attributes for quick access to device-specific features

![Heater UI](https://github.com/ee02217/desktop-tutorial/blob/main/heater.PNG?raw=true)

## 🧩 Installation
### Install through HACS
1. Add a custom repository in HACS: `https://github.com/ee02217/homeassistant-mi-heater`
2. Search for **miHeater** under Integrations.
3. Click **Install** and restart Home Assistant.

### Install manually
1. Copy the contents of `custom_components/miheater/` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## ⚙️ Configuration (UI)
1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **miHeater**.
3. Enter your device IP and token.
4. Choose the model from the pick list (or leave it on **auto** to detect it).

## 🛠️ Services
The integration registers a few handy services for supported models:

| Service | Description | Fields |
| --- | --- | --- |
| `miheater.set_child_lock` | Toggle child lock | `lock` (boolean) |
| `miheater.set_buzzer` | Toggle buzzer | `enabled` (boolean) |
| `miheater.set_led_brightness` | Set LED brightness | `brightness` (`on` / `off` / `dim`) |
| `miheater.set_delay_off` | Set delayed power-off | `seconds` (integer) |

The delay-off number entity is shown in minutes in Home Assistant.

> Tip: The `dim` LED mode is only supported by **zhimi.heater.za2**.

## 🔐 Token notes
The token must be obtained from the Xiaomi Mi Home app database (`miio2.db`), not from `miio discover`.

## 📌 Troubleshooting
* If your model is not detected, select it manually in the config flow.
* If a feature is not available, it will simply be hidden or ignored for that model.

---

Made with warmth and automation in mind. 🔥

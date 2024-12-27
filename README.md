# Viessmann Bridge

A simple bridge between **the Viessmann Heating device** (using Vitoconnect) data (e.g. gas consumption) and [**Domoticz**](https://www.domoticz.com/)/[**Home Assistant**](https://www.home-assistant.io/).

Tested with:

- Viessmann Vitodens 200-W
- Vitoconnect 100

## Features

- **Gas consumption** - updates the realtime values (which are used for hourly consumption calculation) and the daily consumption
- **Burner modulation** - updates the realtime value
- Multiple unit support for consumption - kWh and m3
- Focus on data correctness and reliability - especially when it comes to the data close to midnight/new day
- Easy to use
- No need to install any additional hardware or software on the Vitoconnect device, everything happens via the Viessmann API

## How to configure?

Since the bridge uses the Viessmann API, you need to have a Viessmann account and a Vitoconnect device connected to your heating system. The bridge uses the same API as the Viessmann mobile app, so if you can see the data in the app, you can use the bridge.

You need to configure the API client in the Viessmann developer portal and get the client ID.

1. Go to the [Viessmann Developer Portal](https://app.developer.viessmann.com/) and login.
2. Click on _My dashboard_, and then click _add_ in the _clients_ section.
3. Create a new client using following data:
   - Name: PyViCare
   - Google reCAPTCHA: Disabled
   - Redirect URIs: `vicare://oauth-callback/everest`
4. Copy the `Client ID` to set it in the config later.

## Disclaimer

This project is not affiliated with Viessmann, and it's not an official solution. It's a hobby project, and it's provided as-is. Use it at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Made with ❤️ by [Artur Nowak](https://github.com/Arciiix)

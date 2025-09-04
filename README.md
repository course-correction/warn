# Warn

A simple demonstrator on how to receive push notifications from MoWaS or DWD via NINA.
[NINA](https://de.wikipedia.org/wiki/Warn-App_NINA) is Germany’s public emergency alert app.

**Important** This repository is not affiliated in any way with any governmental institutions.
It uses unreliable APIs.
**NEVER** put any trust in the reliability of this script **and** do not create projects building upon this that could create such impression to people.

## Where do I get my region code?

Take a look at the JSON file containing all [region codes](https://warnung.bund.de/assets/json/converted_gemeinden.json).
Please note, that you might want to include multiple ones to include your whole ‘Kreis’.

## How does this work?

Nina uses [Firebase Cloud Messaging (FCM)](https://en.wikipedia.org/wiki/Firebase_Cloud_Messaging) to send push events to its apps.
The technical infrastructure of FCM is not only used by application developers to distribute messages.
Parts of it are shared with the infrastructure used by Google to connect Android devices and Chromium browsers to receive push events.
Such a client receives a token after initial registration.
Taking this token intended for a general device communication channel and passing it to NINAs backend server, causes the server to think it is a token that a NINA app instance generated via the FCM client SDK.
It starts sending events to the FCM backend server to forward to the app instance (Via Android, Apple, WebPush).
The FCM backend is completely happy to instead send the message to our non-app token endpoint.
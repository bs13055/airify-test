# Mobile / PWA Security Notes

## PWA Status: Ready for Demo Testing

The frontend includes PWA manifest and service worker for potential
"Add to Home Screen" installation on mobile devices.

## What PWA Provides in V1

- Offline access to static UI (cached HTML/CSS/JS)
- "Add to Home Screen" prompt on supported browsers
- Standalone window (no browser chrome)
- Theme color integration

## What PWA Does NOT Do

- No push notifications
- No background location tracking
- No geolocation permission requests
- No camera/microphone access
- No contact access
- No payment integration
- No native app capabilities

## Security Considerations

- Service worker only caches local static files
- API calls are never cached (always network-first)
- No sensitive data in service worker cache
- Service worker can be unregistered by clearing browser data
- No background sync of events

## Mobile Permissions

Airify V1 requests NO device permissions:
- No GPS/location (user enters coordinates manually)
- No notifications
- No storage beyond localStorage (session ID)
- No sensors

## Important Caveats

- This is NOT an App Store / Play Store release
- PWA install is browser-native, not a store submission
- No app review process applies
- Users can always uninstall by removing from home screen
- Installing does not validate this as a medical device

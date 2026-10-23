# A/B Testing Ethics

## Principles

1. **Transparency**: Users are shown mock data regardless of variant.
   No variant provides real health information that another lacks.
2. **No harm**: Both variants show the same quality of information,
   just in different order. No variant withholds safety-relevant data.
3. **No deception**: The platform clearly states it uses mock data.
4. **Voluntary**: Users can close the page at any time.
5. **Anonymous**: The demo does not ask for personal identity; PII-like payload keys are stripped before storage, though optional free-text feedback may still contain what a user chooses to type.
6. **Minimal data**: Only interaction events with rounded location.

## Variant Design

| Variant | Shows | Risk |
|---------|-------|------|
| risk_first | PM2.5 risk level first, then action | None — same info |
| action_first | Action recommendation first, then risk | None — same info |

Both variants:
- Show the same PM2.5 estimate
- Show the same recommendation
- Include the same disclaimer
- Use the same mock data
- Display "not medical advice"

## What We're Testing

- User preference for information ordering
- Which presentation feels more useful
- Whether users engage with feedback
- General product-market fit signal

## What We're NOT Testing

- Medical interventions
- Health outcomes
- Treatment effectiveness
- Behavioral health changes

## Data Minimization

- No name, email, phone
- Location rounded to ~100m (3 decimals)
- No exact routes or movement patterns
- No device fingerprinting
- Session ID is random UUID (not device-linked)
- All data stored locally only

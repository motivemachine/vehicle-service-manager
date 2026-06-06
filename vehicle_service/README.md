# Vehicle Service Manager for Home Assistant

Tracks service intervals, repairs, and tire wear for your vehicles – as a native HA integration with real entities and a custom Lovelace card.

---

## Features

- **Service Status** with progress bars and traffic light system (OK / Watch / Soon / Due / Overdue)
- **Registration Date** as the starting point for time intervals until a service entry is recorded
- **Inspection** requested directly when adding the vehicle, automatic service entry
- **Live Mileage** via any HA entity (OBD adapter, vehicle integration)
- **11 Service Points**: Oil Change, Inspection, Brake Fluid, Cabin Filter, Air Filter, Spark Plugs, Fuel Filter, Transmission Fluid, Haldex Oil, AC Service, Inspection (HU/AU)
- **Repairs & Wear**: Brakes, shocks, timing belt, battery, clutch, and more
- **Tire Tracking**: 4 wheel positions, tread depth, DOT age, wear projection (1/32" per 10,000 miles)
- **Manufacturer Logos** automatically recognized (30+ brands)
- **Multiple Vehicles** in parallel
- **Binary Sensors** for automations (service due)
- **HA Services** to add entries from automations

---

## Installation via HACS

### 1. Add Repository

1. Open HACS → **Integrations** → three dots → **Custom repositories**
2. URL: `https://github.com/toxictody1337/vehicle-service-manager`  
   Category: **Integration**
3. **Add** → then search and install in HACS Store
4. Restart Home Assistant

### 2. Set Up Integration

**Settings → Integrations → + Add → "Vehicle Service Manager"**

The setup wizard guides you through 3 steps:
1. **Vehicle Data**: Manufacturer, Model, Registration Date, Current Mileage, Last Inspection, optional entity for live mileage
2. **Service Points**: Select the points you want to monitor
3. **Intervals**: Adjust the mileage and time intervals

> ⚠️ The default intervals are guidelines. Please check and adjust them in your service manual or owner's handbook. If unsure, consult your service center. No liability for damages.

### 3. Add Lovelace Card

The JavaScript file is automatically registered as a Lovelace resource.  
Dashboard → **Add Card** → **Custom Cards** → **Vehicle Service Card**

Or manually in Lovelace YAML:
```yaml
type: custom:vehicle-service-card
```

---

## Entities

The following entities are created per vehicle:

| Type | Example | Description |
|------|----------|-------------|
| `sensor` | `sensor.golf_gti_oil_change` | Status: ok / watch / soon / due / overdue |
| `sensor` | `sensor.golf_gti_odometer` | Current mileage reading |
| `sensor` | `sensor.golf_gti_tire_fl` | Tread depth FL in 32nds (projected) |
| `binary_sensor` | `sensor.golf_gti_oil_change_due` | True if ≥ 90% |
| `binary_sensor` | `sensor.golf_gti_service_due` | True if anything ≥ 90% |

### Entity Attributes

Each `sensor` entity has the following attributes, among others:
```
vehicle_id, service_id, percentage, status, last_service_date,
last_service_miles, miles_left, months_left, interval_miles, interval_months
```

---

## HA Services

### `vehicle_service.add_service_entry`
```yaml
service: vehicle_service.add_service_entry
data:
  vehicle_id: "abc-123-uuid"
  entry_date: "2024-03-15"
  miles: 79500
  services:
    - oil
    - inspection
  notes: "Main Dealer, Springfield"
```

### `vehicle_service.update_miles`
```yaml
service: vehicle_service.update_miles
data:
  vehicle_id: "abc-123-uuid"
  miles: 80000
```

### `vehicle_service.add_repair`
```yaml
service: vehicle_service.add_repair
data:
  vehicle_id: "abc-123-uuid"
  entry_date: "2024-03-15"
  miles: 79500
  category: brakes_front
  description: "Textar brake pads"
  cost: 180
```

### `vehicle_service.add_tire`
```yaml
service: vehicle_service.add_tire
data:
  vehicle_id: "abc-123-uuid"
  entry_date: "2024-04-01"
  miles: 80000
  type: summer
  axle: all
  width: 205
  ratio: 55
  rim: 16
  brand: Michelin
  dot: "2323"
  vl: 8.0
  vr: 8.0
  hl: 8.0
  hr: 8.0
```

---

## Automation Examples

### Notification When Service is Due
```yaml
automation:
  - alias: "Service Due – Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.golf_gti_service_due
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "🔧 Service Due"
          message: >
            {{ states('sensor.golf_gti_service_due') }} –
            Please schedule service appointment.
```

### Automatic Mileage Update from OBD Integration
```yaml
# Alternatively to configuring in the integration:
automation:
  - alias: "Automatically Update Mileage"
    trigger:
      - platform: state
        entity_id: sensor.obd_odometer
    action:
      - service: vehicle_service.update_miles
        data:
          vehicle_id: "abc-123-uuid"
          miles: "{{ states('sensor.obd_odometer') | int }}"
```

---

## Tire Wear Calculation

The projected tread depth is calculated as:

```
current_depth = original_depth − (miles_driven × 0.189 / 10,000)
```

Recommended wear limits:
- **Summer Tires**: 3/32" (3.8 32nds)
- **Winter / All-Season Tires**: 4/32" (5.1 32nds)
- **Legal Minimum**: 2/32" (1.6 mm equivalent)

---

## Notes & Disclaimer

> The default intervals and calculations (tire wear, service due dates) are guidelines without warranty. Actual maintenance needs depend on vehicle model, driving habits, and conditions. Always consult your owner's manual or service schedule. This software is provided without warranty. No liability for damages resulting from incorrect values or data interpretation.

---

## Development & Attribution

This integration was developed with the support of **Claude (Anthropic AI)**.

### Third-Party Services Used

| Service | Usage | License/Terms |
|---------|-------|---------------|
| [logo.dev](https://logo.dev) | Manufacturer logos for vehicle cards | Free plan, own API key required |
| [Material Design Icons](https://materialdesignicons.com) | Icons via Home Assistant | Apache 2.0 |
| Home Assistant APIs | WebSocket, Config Flow, Storage | Apache 2.0 |

### logo.dev API Key

The integration uses logo.dev for automatic manufacturer logos (Skoda, VW, BMW, etc.).
The API key included in the code is a public demo key. For production use,
I recommend creating your own **free account** at [logo.dev](https://logo.dev)
and replacing the key in the JS file:

```javascript
// In vehicle-service-card.js, around line 50:
function logoUrl(d) {
  return `https://img.logo.dev/${d}?token=YOUR_OWN_KEY&size=64&format=png`;
}
```

---

## License

MIT License – see [LICENSE](LICENSE)

> This software is provided without warranty. The interval values and calculations are
> guidelines without guarantee. Please verify all information against your vehicle's service manual.
> No liability for damages caused by incorrect values or data interpretation.

## Contributing / Issues

Please report bugs or suggestions as [GitHub Issues](https://github.com/toxictody1337/vehicle-service-manager/issues).

# Feed Water Pump - Operation & Maintenance Manual

**Asset Name:** Feed Water Pump
**Asset Type:** Pump
**Location:** Boiler Room A
**Parent:** Boiler Unit 01
**Document ID:** MAN-PMP-001
**Revision:** 1.0

---

## 1. Overview

The Feed Water Pump is a centrifugal pump that supplies treated feed water to Boiler Unit 01. It draws water from the deaerator storage tank and delivers it to the boiler drum at a pressure above the boiler's maximum operating pressure. The pump is a critical component — failure results in boiler low-water level and forced shutdown.

### Key Specifications

| Parameter | Value |
|-----------|-------|
| Type | Horizontal centrifugal, multi-stage |
| Design Pressure | 20 bar (discharge) |
| Normal Discharge Pressure | 15 bar (range 12-20 bar) |
| Flow Capacity | 150 m³/h |
| Drive | Electric motor, 75 kW |
| Speed | 2950 rpm |

### Monitored Sensors

| Sensor | Type | Unit | Normal Range |
|--------|------|------|-------------|
| Vibration | vibration | mm/s | 0.5-4.5 |
| Discharge Pressure | pressure | bar | 12-20 |

---

## 2. Principle of Operation

### 2.1 Startup Procedure

1. Confirm deaerator storage tank level is above minimum (30%).
2. Open pump suction valve fully.
3. Open the casing vent valve to release trapped air — close once water flows steadily.
4. Verify mechanical seal cooling water supply is active.
5. Close the discharge valve (pump starts against closed discharge to minimize starting current).
6. Start the motor and confirm rotation direction.
7. Observe discharge pressure rising to shutoff head (above 18 bar).
8. Gradually open the discharge valve to deliver flow to the boiler.
9. Adjust discharge valve or VFD speed to maintain target pressure of 15 bar.

### 2.2 Normal Operation

- **Discharge Pressure** should be maintained at 3-5 bar above the boiler operating pressure to ensure positive flow through the feed regulating valve.
- **Vibration** should remain below 4.5 mm/s RMS. Values between 4.5-7.1 mm/s indicate an alert condition; above 7.1 mm/s requires immediate shutdown.
- Listen for smooth operation — no knocking, grinding, or cavitation noise.
- Monitor bearing temperatures by touch — should be warm but not hot (below 80°C).
- Check mechanical seal for visible leaks — minor drip is acceptable; continuous flow is not.

### 2.3 Shutdown Procedure

1. Gradually close the discharge valve to reduce flow.
2. Stop the motor.
3. Close the suction valve if the pump will be offline for maintenance.
4. Close seal cooling water if pump is to be isolated.
5. Open drain valves for extended outages (prevent stagnation and corrosion).

---

## 3. System Functions

### 3.1 Water Delivery

The pump converts motor rotational energy into fluid pressure via impeller stages. Water enters the eye of the first-stage impeller, is accelerated outward by centrifugal force, passes through a diffuser that converts velocity to pressure, and proceeds to the next stage. Multiple stages achieve the high discharge pressure required to overcome boiler pressure plus pipe friction losses.

### 3.2 Seal System

The mechanical seal prevents water from escaping along the pump shaft. Cooling water is supplied to the seal chamber to remove frictional heat. The seal faces are typically carbon vs. silicon carbide. Seal degradation leads to water loss and eventual bearing contamination.

### 3.3 Bearing Lubrication

The pump has two bearing housings (drive end and non-drive end). Bearings are oil-bath lubricated. Oil level must be maintained at the sight glass centerline. Oil should be changed every 4000 operating hours or annually, whichever comes first.

---

## 4. Failure Symptoms and Diagnostics

### 4.1 Cavitation

**Symptoms:**
- Loud crackling or rattling noise from inside the pump casing
- Vibration sensor readings fluctuating rapidly above 5 mm/s
- Discharge pressure dropping or fluctuating
- Reduced flow output despite valve position
- Pump motor drawing lower current than normal

**Root Causes:**
- Insufficient Net Positive Suction Head (NPSH) — deaerator level too low
- Suction valve partially closed or blocked strainer
- Water temperature too high (reducing NPSH available)
- Suction piping air leak

**Recommended Actions:**
1. Immediately reduce pump speed or partially close the discharge valve to reduce flow demand.
2. Check deaerator storage tank level — restore if below 30%.
3. Inspect suction strainer for debris — clean if partially blocked.
4. Verify suction valve is fully open.
5. Check for air leaks at suction flange connections (listen for hissing).
6. If cavitation persists, shut down the pump to avoid impeller damage.

---

### 4.2 Seal Failure (Related Cause: Seal Degradation)

**Symptoms:**
- Visible water leaking from the shaft seal area
- Dripping rate exceeding 10 drops per minute
- Water spraying from seal under pressure
- Rust or mineral deposits building up around the seal housing
- Bearing oil contamination (milky appearance indicates water ingress)

**Root Causes:**
- Seal Degradation — normal wear of seal faces over time
- Loss of seal cooling water causing thermal damage
- Misalignment between pump and motor shafts
- Abrasive particles in the feed water scoring the seal faces

**Recommended Actions:**
1. If leak is minor (dripping), schedule seal replacement at next planned outage.
2. If leak is significant (spraying), shut down the pump and isolate.
3. Replace mechanical seal (Mechanical Seal DN40 specification).
4. Inspect shaft sleeve for scoring — replace if grooved.
5. Verify seal cooling water supply is active before restarting.
6. Check pump-motor alignment with dial indicators (max 0.05mm offset).
7. Replace bearing oil if water-contaminated.

**Required Materials:** Mechanical Seal DN40, Gasket Material 3mm
**Required Competences:** Pump Maintenance (Advanced), Pipe Fitting (Intermediate)
**Responsible Roles:** Senior Mechanic

---

### 4.3 Bearing Wear (Related Cause: Bearing Wear)

**Symptoms:**
- Vibration readings steadily increasing over weeks (trend above 4.5 mm/s)
- Audible growling or rumbling from bearing housings
- Bearing housing temperature above 80°C (too hot to touch for more than 3 seconds)
- Oil discoloration (dark or metallic particles visible)
- Increased motor current draw

**Root Causes:**
- Bearing Wear — normal fatigue life exceeded
- Improper Lubrication — low oil level, wrong oil grade, or contaminated oil
- Misalignment causing uneven bearing loading
- Excessive pipe strain on suction or discharge flanges

**Recommended Actions:**
1. Check oil level and condition — top up or replace if discolored.
2. Verify oil grade matches specification (Turbine Oil ISO 46).
3. Measure vibration spectrum to confirm bearing defect frequencies.
4. If bearing defect confirmed, schedule pump overhaul.
5. Replace both bearings during overhaul (Bearing 6205-2RS).
6. Check pump-motor alignment after reassembly.
7. Verify pipe supports are not applying strain to flanges.

**Required Materials:** Bearing 6205-2RS, Turbine Oil ISO 46
**Required Competences:** Pump Maintenance (Advanced), Vibration Analysis (Expert)
**Responsible Roles:** Senior Mechanic

---

### 4.4 General Failure Symptoms

| Symptom | Possible Cause | Initial Check |
|---------|---------------|---------------|
| Pump won't start | Motor trip, electrical fault, coupling failure | Check motor starter, verify coupling integrity |
| Low discharge pressure | Worn impeller, internal recirculation, wrong rotation | Verify rotation direction, check impeller clearance |
| Motor overheating | Bearing overload, misalignment, voltage imbalance | Check current on all three phases, alignment |
| Pulsating pressure | Air in system, check valve chatter, impeller damage | Vent pump casing, inspect check valve |
| Noise (metallic) | Impeller rub, foreign object, bearing failure | Shut down immediately, inspect internals |

---

## 5. Preventive Maintenance Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Visual inspection | Daily | Check for leaks, unusual noise, oil level |
| Vibration reading | Weekly | Record Vibration sensor trend data |
| Oil level check | Weekly | Verify oil at sight glass centerline |
| Strainer cleaning | Monthly | Clean suction strainer |
| Oil change | 4000 hours or yearly | Replace with Turbine Oil ISO 46 |
| Seal inspection | Quarterly | Check for leakage rate, cooling water flow |
| Pump alignment check | Yearly | Dial indicator alignment with motor |
| Full overhaul | 3 years or 20000 hours | Replace bearings, seal, inspect impeller |

---

## 6. Safety Precautions

- Always isolate electrically (LOTO) before working on the pump.
- Do not operate the pump with the suction or discharge valve closed for extended periods.
- Never operate a pump that is dry — mechanical seal damage occurs within seconds.
- Relieve pressure before opening any flange or seal connection.
- Wear PPE: safety glasses, gloves, hearing protection.
- The pump and piping may be hot during operation — use thermal gloves for contact.

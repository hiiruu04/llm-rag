# Steam Turbine 01 - Operation & Maintenance Manual

**Asset Name:** Steam Turbine 01
**Asset Type:** Turbine
**Location:** Turbine Hall B
**Parent:** Power Plant
**Document ID:** MAN-TRB-001
**Revision:** 1.0

---

## 1. Overview

Steam Turbine 01 is the main power generation turbine in the plant. It receives high-pressure steam from Boiler Unit 01, expands it through multiple stages to extract mechanical energy, and drives the Generator to produce electrical power. The turbine is directly coupled to the Generator via a rigid coupling on a common shaft line.

### Key Specifications

| Parameter | Value |
|-----------|-------|
| Type | Impulse-reaction, multi-stage, condensing |
| Rated Speed | 3000 rpm (50 Hz synchronous) |
| Normal Speed Range | 2800-3200 rpm |
| Steam Inlet Pressure | 60 bar (range 50-70 bar) |
| Steam Inlet Temperature | 485°C |
| Exhaust Pressure | 0.08 bar (condenser vacuum) |
| Rated Output | 25 MW |
| Bearing Type | Sleeve (journal) + tilting-pad thrust |

### Monitored Sensors

| Sensor | Type | Unit | Normal Range |
|--------|------|------|-------------|
| RPM | speed | rpm | 2800-3200 |
| Vibration | vibration | mm/s | 0.5-4.5 |
| Bearing Temperature | temperature | °C | 55-95 |
| Steam Inlet Pressure | pressure | bar | 50-70 |

---

## 2. Principle of Operation

### 2.1 Startup Sequence

1. Verify lubricating oil system is running — oil pressure above 1.5 bar, oil temperature 35-45°C.
2. Confirm Cooling System is active — coolant flow and temperature within range.
3. Turn on turning gear to slowly rotate the rotor (approx. 5 rpm) to prevent bowing.
4. Verify all drain valves are open to remove condensate from the casing.
5. Admit steam to the casing for slow warm-up (rolling):
   - Admitting steam rate controlled to limit thermal stress (max 2°C/min temperature rise at casing).
6. Increase speed through critical resonance zones promptly (per vibration chart).
7. At 2800 rpm, synchronize with the electrical grid using the automatic synchronizer.
8. Load the unit gradually — max 5 MW/min loading rate to limit thermal stress.

### 2.2 Normal Operation

- **RPM** must remain at 3000 ± 30 rpm during loaded operation (governor control).
- **Vibration** should be below 4.5 mm/s. Values between 4.5-7.1 mm/s are alert range; above 7.1 mm/s requires trip.
- **Bearing Temperature** normal range 55-95°C. Above 95°C triggers alarm; above 105°C triggers trip.
- **Steam Inlet Pressure** maintained at 60 bar by Boiler Unit 01. Significant deviation affects turbine efficiency and output.
- Monitor oil system continuously — oil pressure, temperature, and filter differential pressure.
- Listen for unusual sounds — rubbing, knocking, or high-pitched whine indicate problems.

### 2.3 Shutdown Procedure

1. Reduce load gradually to minimum stable load (approximately 2 MW).
2. Trip the main steam stop valve (automatic or manual).
3. Rotor coasts down under reduced friction — record coast-down time (baseline ~25 minutes).
4. Engage turning gear once rotor speed drops below 50 rpm.
5. Keep lubricating oil system running for at least 4 hours after shutdown (bearing cooling).
6. Maintain turning gear operation for 24 hours on hot shutdown to prevent rotor bow.

---

## 3. System Functions

### 3.1 Steam Expansion Path

Steam enters through the main stop valve and control (throttle) valves into the high-pressure (HP) stage. Each stage consists of a row of stationary nozzles (stator blades) that accelerate the steam, followed by a row of rotating blades that extract kinetic energy. Steam pressure and temperature drop progressively through each stage. After the HP stages, steam may be extracted for feed water heating before entering the low-pressure (LP) stages. Exhaust steam enters the condenser.

### 3.2 Governor System

The governor maintains constant rotor speed (3000 rpm) under varying load conditions by modulating the steam control valves. The electronic governor compares actual RPM with the setpoint and adjusts valve position via hydraulic actuators. Overspeed protection is provided by independent emergency trip valves set at 3300 rpm (110% of rated speed).

### 3.3 Lubrication System

The lubrication system supplies oil to all journal and thrust bearings. A main shaft-driven oil pump provides oil during normal operation. An AC motor-driven auxiliary pump supplies oil during startup and shutdown. A DC emergency pump activates on loss of AC power. Oil is cooled by the Cooling System and filtered through duplex strainers.

### 3.4 Gland Sealing System

Steam seals (gland packing) prevent steam from escaping along the shaft at both ends of the turbine. Low-pressure steam is supplied to the sealing glands, with leak-off steam collected by the gland steam condenser. Worn seals result in steam loss and reduced efficiency (fault T-SSL-001).

---

## 4. Failure Symptoms and Diagnostics

### 4.1 Fault Code T-BV-001 — Bearing Vibration High (Severity: High, Status: Open)

**Symptoms:**
- Vibration sensor reading above 4.5 mm/s (alert) or 7.1 mm/s (trip)
- Audible rumbling or knocking from bearing housings
- Bearing Temperature sensor reading elevated (above 85°C)
- Oil filter collecting metallic particles
- Vibration trending upward over days/weeks

**Root Causes:**
- Bearing Wear — journal bearing babbitt fatigue or erosion
- Vibration Damage — looseness, resonance, or foundation degradation
- Rotor imbalance from blade erosion or deposit buildup
- Misalignment between turbine and Generator coupling
- Improper Lubrication — oil contamination, low pressure, or wrong viscosity

**Recommended Actions:**
1. Record vibration spectrum to identify dominant frequency (1x = imbalance, 2x = misalignment, broadband = bearing).
2. Check oil condition — pull sample for particle count and spectrographic analysis.
3. Verify oil pressure and temperature are within normal ranges.
4. If vibration is below 7.1 mm/s, reduce load and monitor trend.
5. If vibration exceeds 7.1 mm/s or is rapidly increasing, trip the turbine immediately.
6. After shutdown, inspect bearings through inspection ports.
7. Plan bearing replacement during next outage (Bearing 6205-2RS for thrust, journal bearings per OEM spec).

**Required Materials:** Bearing 6205-2RS, Turbine Oil ISO 46
**Required Competences:** Vibration Analysis (Expert), Turbine Operation (Advanced)
**Responsible Roles:** Turbine Engineer, Senior Mechanic

---

### 4.2 Fault Code T-SSL-001 — Steam Seal Leak (Severity: Medium, Status: Resolved)

**Symptoms:**
- Visible steam escaping from shaft gland areas
- Increased gland steam supply consumption
- Reduced turbine efficiency (steam bypasses blade stages)
- Condensate detected in bearing oil (steam ingress through seals)
- Higher-than-normal exhaust hood temperature

**Root Causes:**
- Seal degradation — normal wear of labyrinth seal fins
- Rotor vibration causing seal rubbing and clearance increase
- Thermal Fatigue of seal segments
- Incorrect gland steam supply pressure

**Recommended Actions:**
1. Verify gland steam supply pressure is per design (typically 0.2-0.5 bar above atmospheric).
2. If leak is minor, monitor and schedule seal replacement at next planned outage.
3. If oil contamination is detected, replace bearing oil and add moisture monitoring.
4. During outage, remove seal segments and measure clearances — replace if exceeded.
5. After seal replacement, verify rotor alignment before closing the casing.

**Responsible Roles:** Senior Mechanic, Turbine Engineer

---

### 4.3 Lubrication System Alarm (Related Down Event: Turbine Lubrication System Alarm)

**Symptoms:**
- Oil pressure dropping below 1.2 bar
- Oil temperature rising above 55°C at cooler outlet
- Bearing Temperature rising across multiple bearings simultaneously
- Oil filter differential pressure switch alarm
- Milky oil appearance (water contamination from Cooling System)

**Root Causes:**
- Improper Lubrication — oil pump wear, relief valve malfunction, filter blockage
- Oil cooler fouling or Cooling System failure
- Oil contamination (water ingress, particulate)
- Oil level too low in reservoir

**Recommended Actions:**
1. If oil pressure drops below 1.0 bar, the turbine will auto-trip. If not, reduce load immediately.
2. Switch to auxiliary oil pump to verify shaft-driven pump is the issue.
3. Check oil reservoir level — top up with Turbine Oil ISO 46 if low.
4. Switch duplex filter to the clean element if DP alarm is active.
5. Check oil cooler — verify Cooling System coolant flow and temperature.
6. Pull oil sample for analysis — check water content, particle count, viscosity.
7. If water contamination confirmed, isolate leak source (oil cooler tube leak probable).

**Required Materials:** Turbine Oil ISO 46
**Required Competences:** Turbine Operation (Advanced)
**Responsible Roles:** Turbine Engineer, Boiler Operator

---

### 4.4 General Failure Symptoms

| Symptom | Possible Cause | Initial Check |
|---------|---------------|---------------|
| Overspeed trip | Governor malfunction, load rejection | Check governor hydraulic system, trip valve |
- Reduced output at same steam flow | Blade erosion, seal wear, nozzle fouling | Compare heat rate to baseline |
| Water induction | Condensate carryover from Boiler Unit 01 | Check steam trap drains, steam quality |
| Exhaust temperature high | Condenser fouling, vacuum loss | Check condenser cooling water, air leakage |
| Shaft voltage/current | Static charge buildup | Verify grounding brush condition |

---

## 5. Preventive Maintenance Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Oil sample analysis | Monthly | Spectrographic analysis, particle count, water content |
| Vibration monitoring | Continuous | Trend Vibration sensor data, alarm at thresholds |
| Oil filter change | 2000 hours or on DP alarm | Switch duplex filter, clean offline element |
| Gland seal inspection | Quarterly | Visual inspection for steam leakage |
| Governor calibration | Yearly | Verify speed regulation and overspeed trip setting |
| Major overhaul | 5 years or 50000 hours | Open casing, inspect blades, replace bearings and seals |
| Alignment check | Yearly | Turbine-Generator coupling alignment |

---

## 6. Safety Precautions

- **NEVER** approach the turbine while it is on turning gear or coasting down — rotating parts hazard.
- **NEVER** override the overspeed trip device.
- The turbine casing and steam piping are extremely hot during operation (above 400°C) — maintain safe distance.
- Lubricating oil system must remain running during coast-down and for 4 hours after trip.
- Hearing protection is mandatory in the turbine hall (noise levels exceed 85 dB).
- LOTO procedures are required for all maintenance on the turbine or coupled equipment.
- Confined space procedures apply for any internal inspection.

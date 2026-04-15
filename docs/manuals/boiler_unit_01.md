# Boiler Unit 01 - Operation & Maintenance Manual

**Asset Name:** Boiler Unit 01
**Asset Type:** Boiler
**Location:** Boiler Room A
**Parent:** Power Plant
**Document ID:** MAN-BLR-001
**Revision:** 1.0

---

## 1. Overview

Boiler Unit 01 is the primary steam generator in the power plant. It converts feed water into high-pressure steam by burning fuel in the Combustion Chamber. The steam produced drives Steam Turbine 01 for electrical power generation. The boiler operates as a water-tube design with multiple generating tubes arranged within the furnace enclosure.

### Key Specifications

| Parameter | Value |
|-----------|-------|
| Design Pressure | 10 bar (normal operating range 8-12 bar) |
| Steam Temperature | 250°C (normal range 180-320°C) |
| Water Level | 65% (normal range 20-95%) |
| Fuel Flow Rate | 12 m³/h (normal range 5-20 m³/h) |
| Maximum Continuous Rating | 120 T/h steam output |

### Monitored Sensors

| Sensor | Type | Unit | Normal Range |
|--------|------|------|-------------|
| Temperature | temperature | °C | 180-320 |
| Pressure | pressure | bar | 6-15 |
| Water Level | level | % | 40-85 |
| Fuel Flow Rate | flow | m³/h | 5-20 |

---

## 2. Principle of Operation

### 2.1 Startup Sequence

1. Verify feed water supply from the Feed Water Pump is active and discharge pressure is above 12 bar.
2. Confirm Combustion Chamber flame scanner is operational.
3. Open the main feed water valve and fill the boiler to 50% water level.
4. Initiate the burner management system (BMS) startup sequence.
5. Purge the furnace for at least 5 air changes to remove residual combustible gases.
6. Ignite the pilot burner, then transition to main flame.
7. Gradually increase firing rate while monitoring pressure rise (max 1 bar/min during warm-up).
8. When pressure reaches 8 bar, open the main steam stop valve slowly.
9. Synchronize steam output with Steam Turbine 01 demand.

### 2.2 Normal Operation

During normal operation the following parameters must be maintained:

- **Water Level:** Maintain between 50-75%. The automatic feed water regulator controls the feed valve. If level drops below 40%, the low-level alarm activates (fault code B-LW-001).
- **Pressure:** Maintain between 8-12 bar. The burner modulates to match steam demand. If pressure exceeds 13 bar, the safety relief valve lifts. If pressure exceeds 14 bar, the high-pressure trip activates (fault code B-HP-001).
- **Temperature:** Steam temperature tracks pressure per the steam tables. A sudden drop in temperature with stable pressure indicates water carryover.
- **Fuel Flow:** Fuel flow should be proportional to steam demand. Unexplained increases in fuel consumption with steady load indicate efficiency loss, possibly due to fouled tubes.

### 2.3 Shutdown Sequence

1. Reduce firing rate gradually over 30 minutes.
2. Close main fuel valve when pressure drops to 5 bar.
3. Close main steam stop valve.
4. Allow natural cool-down. Do not open vents or drains until pressure is below 2 bar.
5. Verify water level stabilizes at 50% for lay-up.

---

## 3. System Functions

### 3.1 Steam Generation

Feed water enters the boiler drum via the downcomers. It flows through the generating tubes located in the furnace walls, where heat from the Combustion Chamber converts it to a steam-water mixture. The mixture rises back to the drum where steam separates from the water. Dry saturated steam exits through the superheater section (if equipped) to the main steam header.

### 3.2 Combustion System

Fuel is mixed with combustion air in the burner assembly. The flame is contained within the Combustion Chamber. Exhaust gases pass over the generating tubes and exit through the stack. The Exhaust Gas O2 sensor monitors combustion efficiency (optimum 3-5% O2).

### 3.3 Feed Water System

The Feed Water Pump delivers treated water to the boiler drum at a pressure above the boiler operating pressure. The automatic feed regulator maintains drum water level by adjusting the feed valve position based on the Water Level sensor reading.

### 3.4 Safety Systems

- **Safety relief valves:** Two spring-loaded valves set at 13 bar and 14 bar.
- **Low-water trip:** Cuts fuel if water level drops below 20%.
- **High-pressure trip:** Cuts fuel if pressure exceeds 14 bar (fault B-HP-001).
- **Flame failure trip:** Cuts fuel within 4 seconds if flame is lost.
- **High gas temperature trip:** Cuts fuel if exhaust gas exceeds design limit.

---

## 4. Failure Symptoms and Diagnostics

### 4.1 Fault Code B-HP-001 — High Pressure Warning (Severity: High, Status: Open)

**Symptoms:**
- Pressure sensor reads above 13 bar
- Safety relief valve lifting (audible steam discharge)
- Burner cycling on/off rapidly
- Steam pressure gauge in control room shows rising trend

**Root Causes:**
- Sudden reduction in steam demand (turbine trip or valve closure)
- Faulty pressure transmitter giving erratic readings
- Burner modulation valve stuck open
- Safety relief valve setpoint drifted too low

**Recommended Actions:**
1. Verify pressure reading on local gauge vs. sensor (Temperature/Pressure sensors).
2. If pressure is genuinely high, reduce firing rate immediately.
3. Check steam demand downstream — confirm Steam Turbine 01 is accepting steam.
4. Inspect burner modulation linkage for binding or disconnection.
5. Test safety relief valves by manual lifting.
6. If root cause is control system failure, switch to manual firing control.

**Related Causes:** Thermal Fatigue, Improper Lubrication (burner linkage)
**Responsible Roles:** Boiler Operator, Maintenance Planner

---

### 4.2 Fault Code B-LW-001 — Low Water Level (Severity: Critical, Status: Open)

**Symptoms:**
- Water Level sensor reads below 30%
- Low-water alarm sounding in control room
- Feed Water Pump running but discharge pressure dropping
- Visible drop in gauge glass level
- Steam temperature rising above normal for given pressure

**Root Causes:**
- Feed Water Pump failure or cavitation
- Feed water valve stuck closed
- Tube leak causing rapid water loss (see B-TL-001)
- Level controller malfunction
- Blowdown valve left open

**Recommended Actions:**
1. **CRITICAL:** If level drops below 20%, emergency shutdown — cut fuel immediately. Never add water to a hot, dry boiler.
2. Verify Feed Water Pump is running and discharge pressure is above 12 bar.
3. Check feed water valve position — confirm automatic controller is commanding it open.
4. Inspect blowdown valves — confirm all are closed.
5. If tube leak suspected (see B-TL-001), prepare for controlled shutdown.
6. After restoring level, perform water treatment analysis before restarting.

**Related Causes:** Corrosion (tube thinning), Improper Lubrication (pump bearings)
**Responsible Roles:** Boiler Operator, Shift Supervisor

---

### 4.3 Fault Code B-TL-001 — Tube Leak (Severity: Critical, Status: In Progress)

**Symptoms:**
- Unexplained water level drop despite normal feed water flow
- Steam escaping from casing (visible or audible hissing)
- Increased feed water consumption with no change in steam output
- White smoke or steam from boiler stack
- Sulfur smell or chemical odor near the boiler casing
- Pressure drop disproportionate to firing rate

**Root Causes:**
- Thermal Fatigue — repeated heating/cooling cycles cause tube cracking
- Corrosion — water-side pitting from inadequate water treatment
- Erosion — soot blower impingement or fly ash abrasion
- Manufacturing defect in tube material (SA213-T12)

**Recommended Actions:**
1. Confirm leak location using acoustic monitoring or thermal imaging.
2. If leak is small (minor pressure deviation), reduce load and schedule planned shutdown.
3. If leak is large (rapid water loss, audible steam), initiate emergency shutdown per Section 2.3.
4. After cool-down, perform hydrostatic test to identify affected tubes.
5. Plug or replace leaking tubes using SA213-T12 specification tubes.
6. Inspect adjacent tubes for thinning (ultrasonic thickness measurement).
7. Review water treatment logs — check pH, conductivity, and oxygen scavenger levels.
8. Document findings and update preventive maintenance schedule.

**Required Materials:** Boiler Tube SA213-T12, Welding Electrode E7018, Gasket Material 3mm
**Required Competences:** Welding (Advanced), Boiler Operation (Expert)
**Responsible Roles:** Senior Mechanic, Maintenance Planner

---

### 4.4 General Failure Symptoms (No Specific Fault Code)

| Symptom | Possible Cause | Initial Check |
|---------|---------------|---------------|
| Flame instability | Dirty burner nozzle, low fuel pressure, Combustion Chamber fouling | Inspect burner assembly, check fuel filters |
| Excessive fuel consumption | Tube fouling (soot buildup), refractory damage | Check exhaust gas temperature vs. design |
| Water hammer in steam lines | Wet steam carryover, rapid valve operation | Verify steam quality, check separator |
| Boiler drum level fluctuations | Foaming (high dissolved solids), faulty level sensor | Check water chemistry, calibrate sensor |
| Unusual vibration or rumbling | Flame impingement, refractory collapse | Visual inspection through sight glass |

---

## 5. Preventive Maintenance Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Water treatment analysis | Daily | Test pH, TDS, dissolved oxygen, hardness |
| Gauge glass blowdown | Shift | Clear gauge glass to verify true water level |
| Safety valve test | Monthly | Manual lift test on both relief valves |
| Combustion efficiency test | Monthly | Flue gas analysis (O2, CO, CO2) — target 3-5% O2 |
| Tube inspection (external) | Quarterly | Visual and thermal imaging of accessible tubes |
| Tube inspection (internal) | Yearly | Hydrostatic test and UT thickness survey |
| Burner overhaul | Yearly | Clean nozzles, inspect refractory, replace gaskets |
| Refractory repair | As needed | Patch or replace damaged refractory sections |

---

## 6. Safety Precautions

- **NEVER** enter the furnace or confined space without LOTO (Lock Out / Tag Out) and gas testing.
- **NEVER** add cold water to a hot boiler that has lost water level — risk of thermal shock and violent steam generation.
- Always wear PPE: safety glasses, heat-resistant gloves, hard hat, hearing protection.
- The boiler room must have functional gas detectors and adequate ventilation.
- Emergency shutdown procedures must be posted visibly near the boiler control panel.
- All maintenance on pressure-containing components requires a certified welder and post-repair hydrostatic test.

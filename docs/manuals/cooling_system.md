# Cooling System - Operation & Maintenance Manual

**Asset Name:** Cooling System
**Asset Type:** Cooling System
**Location:** Turbine Hall B
**Parent:** Steam Turbine 01
**Document ID:** MAN-COL-001
**Revision:** 1.0

---

## 1. Overview

The Cooling System removes waste heat from Steam Turbine 01, the Generator, and the turbine lubricating oil system. It circulates coolant (treated water with corrosion inhibitor) through heat exchangers, absorbing heat from the equipment and rejecting it to the cooling tower or air-cooled heat exchangers. The system is essential for continuous operation — loss of cooling forces immediate turbine and generator shutdown.

### Key Specifications

| Parameter | Value |
|-----------|-------|
| Type | Closed-loop treated water with cooling tower rejection |
| Coolant | Treated water + corrosion inhibitor (glycol optional for freeze protection) |
| Normal Coolant Temperature | 40°C (range 25-55°C) |
| Normal Coolant Flow Rate | 200 L/min (range 150-260 L/min) |
| System Pressure | 2-4 bar (closed loop) |
| Heat Rejection Capacity | 8 MW thermal |

### Monitored Sensors

| Sensor | Type | Unit | Normal Range |
|--------|------|------|-------------|
| Coolant Temperature | temperature | °C | 25-55 |
| Coolant Flow Rate | flow | L/min | 150-260 |

---

## 2. Principle of Operation

### 2.1 Startup Sequence

1. Verify coolant reservoir level is above minimum (60% of expansion tank).
2. Confirm all isolation valves in the coolant loop are open.
3. Start the primary coolant circulation pump.
4. Verify Coolant Flow Rate is above 150 L/min on the flow sensor.
5. Check for air in the system — vent at high-point bleed valves until solid water flow.
6. Verify Coolant Temperature is below 50°C before starting Steam Turbine 01.
7. Start the cooling tower fan or air-cooled heat exchanger fans.

### 2.2 Normal Operation

- **Coolant Temperature** should be maintained between 25-45°C during normal load. Above 50°C triggers an alarm; above 55°C requires load reduction.
- **Coolant Flow Rate** should be steady at approximately 200 L/min. Any drop below 150 L/min indicates pump issue, blockage, or air in the system.
- Monitor the temperature differential across heat exchangers — reduced differential indicates fouling.
- Check expansion tank level daily — loss of coolant indicates a leak in the system.
- Verify cooling tower fill is intact and water distribution is even.

### 2.3 Shutdown Procedure

1. The Cooling System must remain running after turbine shutdown until all equipment temperatures are below 50°C.
2. Allow circulation for at least 2 hours post-shutdown.
3. Stop coolant circulation pump.
4. Stop cooling tower fans.
5. In freezing conditions, drain exposed piping or maintain circulation to prevent freeze damage.

---

## 3. System Functions

### 3.1 Heat Exchangers

The system uses shell-and-tube or plate-type heat exchangers for each cooling load:
- **Generator coolers:** Remove I²R and core heat from Generator windings.
- **Lube oil coolers:** Remove bearing friction heat from Steam Turbine 01 lubricating oil.
- **Seal oil coolers:** Remove heat from the Generator seal oil system (if hydrogen-cooled).

Hot coolant flows through the tube side; the process fluid (oil or air) is on the shell side. Heat transfers from the process fluid to the coolant. The heated coolant then flows to the cooling tower where heat is rejected to the atmosphere.

### 3.2 Cooling Tower

The cooling tower uses evaporative cooling — hot water is sprayed over fill media while air flows counter-current. A small portion of water evaporates, absorbing latent heat and cooling the remaining water. The cooled water collects in the basin and is recirculated. Makeup water is added automatically to compensate for evaporation and blowdown losses.

### 3.3 Chemical Treatment

Coolant chemistry must be maintained to prevent corrosion, scale, and biological growth:
- **pH:** 8.5-10.5 (alkaline to prevent corrosion)
- **Corrosion inhibitor:** Maintained at manufacturer-recommended concentration
- **Biocide:** Added periodically to prevent algae and bacterial growth
- **Conductivity:** Monitored to control dissolved solids (prevents scale)

---

## 4. Failure Symptoms and Diagnostics

### 4.1 Coolant Leak (Related Down Event: Cooling System Leak)

**Symptoms:**
- Expansion tank level dropping steadily
- Coolant Flow Rate reading lower than normal (loss of system volume)
- Visible water puddles or wet spots near pipe connections, valves, or heat exchangers
- White mineral deposits at leak points (chronic small leaks)
- Pressure gauge reading lower than normal

**Root Causes:**
- Corrosion — internal pipe or heat exchanger tube corrosion causing pinhole leaks
- Loose flange connections or worn gaskets
- Heat exchanger tube failure (erosion or corrosion)
- Frost damage (if system was not properly drained or heated during freezing conditions)
- Mechanical vibration fatiguing pipe joints

**Recommended Actions:**
1. Identify the leak source — trace wet areas to the highest point (gravity flows down).
2. If leak is minor (weeping flange), tighten bolts or schedule gasket replacement.
3. If leak is from a heat exchanger, isolate and pressure-test individual tube bundles.
4. Plug leaking tubes (up to 10% of tubes can be plugged before requiring replacement).
5. Repair or replace damaged piping sections.
6. Top up coolant with treated water + inhibitor to restore proper chemistry.
7. If coolant was lost for extended period, flush system before refilling.

**Required Materials:** Gasket Material 3mm, Coolant Concentrate
**Required Competences:** Pipe Fitting (Expert)
**Responsible Roles:** Senior Mechanic

---

### 4.2 Overheating (Coolant Temperature High)

**Symptoms:**
- Coolant Temperature sensor reading above 50°C
- Generator Winding Temperature alarm (secondary effect)
- Steam Turbine 01 bearing temperature alarm (lube oil not being cooled adequately)
- Cooling tower basin water is hot to touch
- Cooling tower approach temperature (cold water vs. wet bulb) is excessive

**Root Causes:**
- Cooling tower fan failure (motor trip, belt break, or blade issue)
- Heat exchanger fouling (scale, biological growth, or debris)
- Coolant flow restriction (blocked strainer, air lock, or valve partially closed)
- Insufficient coolant volume (low expansion tank level)
- Ambient temperature too high (design exceeded)

**Recommended Actions:**
1. Check cooling tower fan operation — verify all fans are running.
2. Inspect cooling tower fill media for scale, algae, or damage.
3. Check coolant strainers — clean if blocked.
4. Verify all isolation valves are fully open.
5. Vent air from high points in the piping system.
6. If heat exchanger fouled, schedule chemical cleaning or backwash.
7. Increase blowdown rate on cooling tower to reduce dissolved solids.
8. Check chemical treatment dosing — add biocide if biological growth suspected.

**Responsible Roles:** Maintenance Planner, Senior Mechanic

---

### 4.3 Pump Failure

**Symptoms:**
- Coolant Flow Rate drops to zero or near-zero
- Pump motor current drop or trip
- Loud noise from pump (cavitation, bearing failure)
- Vibration on pump casing

**Root Causes:**
- Motor electrical fault
- Pump impeller wear or damage
- Bearing failure (see Feed Water Pump manual for bearing failure details)
- Seal failure causing pump shutdown
- Cavitation from low suction level

**Recommended Actions:**
1. Switch to standby pump if available.
2. Isolate failed pump and close suction/discharge valves.
3. Inspect pump for mechanical damage.
4. Replace bearings, seal, or impeller as required.
5. Verify system is fully vented before restarting (air causes cavitation).

---

### 4.4 General Failure Symptoms

| Symptom | Possible Cause | Initial Check |
|---------|---------------|---------------|
| Milky coolant | Oil contamination from heat exchanger tube leak | Isolate heat exchangers one by one, test coolant for oil |
| Rusty coolant | Corrosion inhibitor depleted, low pH | Test coolant chemistry, add inhibitor |
| Algae in cooling tower | Insufficient biocide dosing | Shock dose biocide, clean tower basin |
| Frozen pipes | System not protected for ambient temperature | Trace and thaw, add glycol for freeze protection |
| High cooling tower drift | Drift eliminators damaged or missing | Inspect and replace drift eliminators |

---

## 5. Preventive Maintenance Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Expansion tank level check | Daily | Verify level is between min/max marks |
| Coolant chemistry test | Weekly | pH, inhibitor concentration, conductivity |
| Strainer inspection | Monthly | Clean coolant circulation pump strainers |
| Cooling tower inspection | Monthly | Check fill, fans, basin, water distribution |
| Heat exchanger performance test | Quarterly | Measure temperature differential, compare to design |
| Cooling tower basin clean | Quarterly | Drain and clean basin, remove debris and sediment |
| Chemical flush | Yearly | Circulate cleaning solution to remove scale and biofilm |
| Complete system inspection | Yearly | Inspect all piping, valves, supports, and insulation |

---

## 6. Safety Precautions

- Do not open pressurized system components without relieving pressure first.
- Coolant may be hot during operation (up to 55°C) — wear thermal gloves.
- Chemical treatment agents (biocide, inhibitor) are hazardous — follow SDS and wear appropriate PPE.
- Cooling tower basins require confined space entry procedures.
- Electrical isolation (LOTO) required before working on pumps or fan motors.
- In freezing conditions, ensure heat tracing or continuous circulation to prevent pipe burst.

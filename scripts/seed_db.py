"""Seed the PostgreSQL database with realistic industrial asset data.

Usage:
    uv run python scripts/seed_db.py          # Seed if empty
    uv run python scripts/seed_db.py --clean  # Wipe and re-seed
"""

from __future__ import annotations

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

# Ensure project root is on sys.path so `app` is importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from sqlalchemy import func, select, text

from app.core.database import async_session_factory, engine
from app.models import Asset, Fault, MaintenanceSchedule, Sensor, SensorData, fault_cause_effect

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SENSOR_DEFINITIONS: dict[str, list[dict[str, str]]] = {
    "Boiler Unit 01": [
        {"name": "Temperature", "sensor_type": "temperature", "unit": "°C"},
        {"name": "Pressure", "sensor_type": "pressure", "unit": "bar"},
        {"name": "Water Level", "sensor_type": "level", "unit": "%"},
        {"name": "Fuel Flow Rate", "sensor_type": "flow", "unit": "m³/h"},
    ],
    "Feed Water Pump": [
        {"name": "Vibration", "sensor_type": "vibration", "unit": "mm/s"},
        {"name": "Discharge Pressure", "sensor_type": "pressure", "unit": "bar"},
    ],
    "Combustion Chamber": [
        {"name": "Flame Temperature", "sensor_type": "temperature", "unit": "°C"},
        {"name": "Exhaust Gas O2", "sensor_type": "o2", "unit": "%"},
    ],
    "Steam Turbine 01": [
        {"name": "RPM", "sensor_type": "speed", "unit": "rpm"},
        {"name": "Vibration", "sensor_type": "vibration", "unit": "mm/s"},
        {"name": "Bearing Temperature", "sensor_type": "temperature", "unit": "°C"},
        {"name": "Steam Inlet Pressure", "sensor_type": "pressure", "unit": "bar"},
    ],
    "Generator": [
        {"name": "Winding Temperature", "sensor_type": "temperature", "unit": "°C"},
        {"name": "Output Voltage", "sensor_type": "voltage", "unit": "V"},
        {"name": "Output Current", "sensor_type": "current", "unit": "A"},
    ],
    "Cooling System": [
        {"name": "Coolant Temperature", "sensor_type": "temperature", "unit": "°C"},
        {"name": "Coolant Flow Rate", "sensor_type": "flow", "unit": "L/min"},
    ],
}

# Realistic value ranges: (baseline, noise_amplitude, min, max)
SENSOR_VALUE_RANGES: dict[str, tuple[float, float, float, float]] = {
    "temperature": (250.0, 15.0, 180.0, 320.0),
    "pressure": (10.0, 1.5, 6.0, 15.0),
    "level": (65.0, 8.0, 20.0, 95.0),
    "flow": (12.0, 2.0, 5.0, 20.0),
    "vibration": (2.5, 1.0, 0.5, 8.0),
    "speed": (3000.0, 30.0, 2800.0, 3200.0),
    "o2": (3.5, 1.0, 1.0, 8.0),
    "voltage": (11000.0, 200.0, 10000.0, 12000.0),
    "current": (450.0, 30.0, 350.0, 550.0),
}

# Per-sensor overrides (when the sensor name requires different baseline)
SENSOR_NAME_OVERRIDES: dict[str, tuple[float, float, float, float]] = {
    "Flame Temperature": (1200.0, 50.0, 1000.0, 1400.0),
    "Bearing Temperature": (75.0, 5.0, 55.0, 95.0),
    "Winding Temperature": (90.0, 8.0, 65.0, 115.0),
    "Coolant Temperature": (40.0, 4.0, 25.0, 55.0),
    "Coolant Flow Rate": (200.0, 15.0, 150.0, 260.0),
    "Discharge Pressure": (15.0, 1.0, 12.0, 20.0),
    "Steam Inlet Pressure": (60.0, 3.0, 50.0, 70.0),
    "Exhaust Gas O2": (3.5, 1.0, 1.0, 8.0),
}

HOURS_OF_DATA = 24

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _generate_value(sensor_name: str, sensor_type: str) -> float:
    rng = SENSOR_NAME_OVERRIDES.get(sensor_name) or SENSOR_VALUE_RANGES.get(sensor_type)
    if rng is None:
        return round(random.uniform(0, 100), 2)
    baseline, noise, lo, hi = rng
    return round(_clamp(baseline + random.uniform(-noise, noise), lo, hi), 2)


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


async def clean_db(session: AsyncSession) -> None:
    """Delete all seeded data, respecting FK order."""
    logger.info("Cleaning existing data...")
    for table in [
        "sensor_data",
        "maintenance_schedules",
        "fault_cause_effect",
        "faults",
        "sensors",
        "assets",
    ]:
        await session.execute(text(f'DELETE FROM "{table}"'))
    await session.commit()
    logger.info("Database cleaned.")


async def seed_assets(session: AsyncSession) -> dict[str, Asset]:
    """Create the asset hierarchy. Returns name -> Asset mapping."""
    count = await session.scalar(func.count(Asset.id))
    if count and count > 0:
        logger.info(f"Assets already exist ({count}), skipping.")
        return {a.name: a for a in (await session.scalars(select(Asset))).all()}

    power_plant = Asset(
        name="Power Plant",
        description="Main power generation facility",
        asset_type="facility",
        location="Building A, Floor 1",
        status="active",
    )
    session.add(power_plant)
    await session.flush()

    boiler = Asset(
        name="Boiler Unit 01",
        description="Primary steam generation boiler",
        asset_type="boiler",
        parent_id=power_plant.id,
        location="Boiler Room A",
        status="active",
    )
    pump = Asset(
        name="Feed Water Pump",
        description="Feed water supply pump for Boiler Unit 01",
        asset_type="pump",
        parent_id=boiler.id,
        location="Boiler Room A",
        status="active",
    )
    chamber = Asset(
        name="Combustion Chamber",
        description="Combustion chamber for Boiler Unit 01",
        asset_type="chamber",
        parent_id=boiler.id,
        location="Boiler Room A",
        status="active",
    )

    turbine = Asset(
        name="Steam Turbine 01",
        description="Main steam turbine generator unit",
        asset_type="turbine",
        parent_id=power_plant.id,
        location="Turbine Hall B",
        status="active",
    )
    generator = Asset(
        name="Generator",
        description="Electrical generator coupled to Steam Turbine 01",
        asset_type="generator",
        parent_id=turbine.id,
        location="Turbine Hall B",
        status="active",
    )
    cooling = Asset(
        name="Cooling System",
        description="Cooling system for Steam Turbine 01",
        asset_type="cooling_system",
        parent_id=turbine.id,
        location="Turbine Hall B",
        status="active",
    )

    session.add_all([boiler, pump, chamber, turbine, generator, cooling])
    await session.flush()

    assets = {
        "Power Plant": power_plant,
        "Boiler Unit 01": boiler,
        "Feed Water Pump": pump,
        "Combustion Chamber": chamber,
        "Steam Turbine 01": turbine,
        "Generator": generator,
        "Cooling System": cooling,
    }
    await session.commit()
    logger.info(f"Created {len(assets)} assets.")
    return assets


async def seed_sensors(
    session: AsyncSession, assets: dict[str, Asset]
) -> dict[str, Sensor]:
    """Create sensors for each asset. Returns 'asset_name:sensor_name' -> Sensor."""
    count = await session.scalar(func.count(Sensor.id))
    if count and count > 0:
        logger.info(f"Sensors already exist ({count}), skipping.")
        sensors: dict[str, Sensor] = {}
        for s in (await session.scalars(select(Sensor))).all():
            sensors[f"{s.name}"] = s
        return sensors

    created: dict[str, Sensor] = {}
    for asset_name, defs in SENSOR_DEFINITIONS.items():
        asset = assets.get(asset_name)
        if asset is None:
            logger.warning(f"Asset '{asset_name}' not found, skipping sensors.")
            continue
        for sdef in defs:
            sensor = Sensor(
                asset_id=asset.id,
                name=sdef["name"],
                sensor_type=sdef["sensor_type"],
                unit=sdef["unit"],
                status="active",
            )
            session.add(sensor)
            created[f"{asset_name}:{sdef['name']}"] = sensor

    await session.flush()
    await session.commit()
    logger.info(f"Created {len(created)} sensors.")
    return created


async def seed_faults(
    session: AsyncSession, assets: dict[str, Asset]
) -> dict[str, Fault]:
    """Create faults with cause-effect links. Returns fault code -> Fault."""
    count = await session.scalar(func.count(Fault.id))
    if count and count > 0:
        logger.info(f"Faults already exist ({count}), skipping.")
        return {f.code: f for f in (await session.scalars(select(Fault))).all()}

    now = datetime.now(timezone.utc)

    fault_specs = [
        # (code, name, description, severity, status, asset_name, resolved)
        ("B-HP-001", "High Pressure Warning", "Boiler pressure exceeded safe threshold",
         "high", "open", "Boiler Unit 01", False),
        ("B-LW-001", "Low Water Level", "Boiler water level dropped below minimum operating range",
         "critical", "open", "Boiler Unit 01", False),
        ("B-TL-001", "Tube Leak", "Detected leakage in boiler tubes",
         "critical", "in_progress", "Boiler Unit 01", False),
        ("T-BV-001", "Bearing Vibration High", "Turbine bearing vibration exceeds acceptable limits",
         "high", "open", "Steam Turbine 01", False),
        ("T-SSL-001", "Steam Seal Leak", "Steam leaking through turbine shaft seals",
         "medium", "resolved", "Steam Turbine 01", True),
    ]

    faults: dict[str, Fault] = {}
    for code, name, desc, severity, status, asset_name, resolved in fault_specs:
        asset = assets[asset_name]
        fault = Fault(
            asset_id=asset.id,
            code=code,
            name=name,
            description=desc,
            severity=severity,
            status=status,
            detected_at=now - timedelta(hours=random.randint(48, 120)),
            resolved_at=(now - timedelta(hours=random.randint(1, 24))) if resolved else None,
        )
        session.add(fault)
        faults[code] = fault

    await session.flush()

    # Cause-effect links
    cause_effects = [
        ("B-TL-001", "B-LW-001", "causes"),
        ("B-HP-001", "B-TL-001", "contributes_to"),
        ("T-BV-001", "T-SSL-001", "causes"),
    ]
    for causing_code, affected_code, link_type in cause_effects:
        await session.execute(
            fault_cause_effect.insert().values(
                causing_fault_id=faults[causing_code].id,
                affected_fault_id=faults[affected_code].id,
                link_type=link_type,
            )
        )

    await session.commit()
    logger.info(f"Created {len(faults)} faults with {len(cause_effects)} cause-effect links.")
    return faults


async def seed_sensor_data(
    session: AsyncSession, sensors: dict[str, Sensor]
) -> None:
    """Generate 24 hours of hourly readings for every sensor."""
    count = await session.scalar(func.count(SensorData.id))
    if count and count > 0:
        logger.info(f"Sensor data already exists ({count} rows), skipping.")
        return

    now = datetime.now(timezone.utc)
    batch_size = 500
    rows: list[SensorData] = []

    total_sensors = len(sensors)
    for sensor_key, sensor in sensors.items():
        # Determine sensor name and type for value generation
        # sensor_key format: "Asset Name:Sensor Name" or just "Sensor Name" when loading existing
        parts = sensor_key.split(":")
        sensor_name = parts[-1] if ":" in sensor_key else sensor.name
        sensor_type = sensor.sensor_type

        for hour_offset in range(HOURS_OF_DATA):
            ts = now - timedelta(hours=HOURS_OF_DATA - hour_offset)
            value = _generate_value(sensor_name, sensor_type)
            rows.append(
                SensorData(
                    sensor_id=sensor.id,
                    timestamp=ts,
                    value=value,
                )
            )

            if len(rows) >= batch_size:
                session.add_all(rows)
                await session.flush()
                rows.clear()

    if rows:
        session.add_all(rows)
        await session.flush()

    await session.commit()
    logger.info(f"Created {total_sensors * HOURS_OF_DATA} sensor data rows across {total_sensors} sensors.")


async def seed_maintenance_schedules(
    session: AsyncSession, assets: dict[str, Asset], faults: dict[str, Fault]
) -> None:
    """Create maintenance schedules linked to assets and some faults."""
    count = await session.scalar(func.count(MaintenanceSchedule.id))
    if count and count > 0:
        logger.info(f"Maintenance schedules already exist ({count}), skipping.")
        return

    now = datetime.now(timezone.utc)

    schedules = [
        # (title, description, type, status, priority, asset_name, fault_code, recurrence, assigned_to, hours, days_offset)
        (
            "Boiler Annual Inspection",
            "Comprehensive annual inspection of Boiler Unit 01 including pressure vessel, safety valves, and controls",
            "preventive", "scheduled", "high",
            "Boiler Unit 01", None, "yearly", "Engineering Team A", 16.0, 30,
        ),
        (
            "Tube Leak Repair",
            "Emergency repair of detected tube leak in Boiler Unit 01",
            "corrective", "in_progress", "critical",
            "Boiler Unit 01", "B-TL-001", "none", "Repair Crew B", 8.0, 0,
        ),
        (
            "Safety Valve Calibration",
            "Calibration and testing of boiler safety relief valves",
            "preventive", "scheduled", "medium",
            "Boiler Unit 01", None, "quarterly", "Instrumentation Team", 4.0, 14,
        ),
        (
            "Feed Water Pump Overhaul",
            "Complete disassembly and inspection of feed water pump bearings and seals",
            "preventive", "scheduled", "medium",
            "Feed Water Pump", None, "yearly", "Mechanical Team", 12.0, 60,
        ),
        (
            "Combustion Efficiency Test",
            "Flue gas analysis and combustion tuning",
            "predictive", "scheduled", "low",
            "Combustion Chamber", None, "monthly", "Operations Team", 3.0, 7,
        ),
        (
            "Turbine Bearing Replacement",
            "Replacement of high-vibration turbine bearings",
            "corrective", "scheduled", "high",
            "Steam Turbine 01", "T-BV-001", "none", "Mechanical Team", 24.0, 10,
        ),
        (
            "Turbine Vibration Analysis",
            "Predictive vibration monitoring and analysis",
            "predictive", "completed", "medium",
            "Steam Turbine 01", None, "monthly", "Condition Monitoring", 2.0, -5,
        ),
        (
            "Steam Seal Replacement",
            "Replacement of worn turbine shaft seals",
            "corrective", "completed", "medium",
            "Steam Turbine 01", "T-SSL-001", "none", "Mechanical Team", 10.0, -10,
        ),
        (
            "Generator Winding Inspection",
            "Thermographic and insulation resistance testing of generator windings",
            "preventive", "scheduled", "medium",
            "Generator", None, "quarterly", "Electrical Team", 6.0, 21,
        ),
        (
            "Cooling System Flush",
            "Full coolant drain, flush, and refill with new coolant",
            "preventive", "scheduled", "low",
            "Cooling System", None, "quarterly", "Maintenance Crew C", 4.0, 45,
        ),
    ]

    for (
        title, desc, mtype, status, priority,
        asset_name, fault_code, recurrence, assigned_to, est_hours, days_offset,
    ) in schedules:
        asset = assets[asset_name]
        fault_id = faults[fault_code].id if fault_code else None
        scheduled_date = now + timedelta(days=days_offset)
        completed_date = None
        if status == "completed":
            completed_date = scheduled_date + timedelta(hours=est_hours)

        session.add(
            MaintenanceSchedule(
                asset_id=asset.id,
                fault_id=fault_id,
                title=title,
                description=desc,
                maintenance_type=mtype,
                status=status,
                priority=priority,
                scheduled_date=scheduled_date,
                completed_date=completed_date,
                assigned_to=assigned_to,
                recurrence=recurrence,
                estimated_duration_hours=est_hours,
            )
        )

    await session.commit()
    logger.info(f"Created {len(schedules)} maintenance schedules.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def run(clean: bool = False) -> None:
    logger.info("Starting database seeding...")

    async with async_session_factory() as session:
        if clean:
            await clean_db(session)

        assets = await seed_assets(session)
        sensors = await seed_sensors(session, assets)
        faults = await seed_faults(session, assets)
        await seed_sensor_data(session, sensors)
        await seed_maintenance_schedules(session, assets, faults)

    await engine.dispose()
    logger.info("Seeding complete.")


def main() -> None:
    clean = "--clean" in sys.argv
    asyncio.run(run(clean=clean))


if __name__ == "__main__":
    main()

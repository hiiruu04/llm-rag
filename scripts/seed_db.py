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
from app.models import (
    Aggregate,
    Asset,
    Cause,
    Competence,
    DownEvent,
    Fault,
    Level,
    Location,
    Material,
    Order,
    Role,
    Shift,
    System,
    Task,
    Worker,
    Sensor,
    SensorData,
    MaintenanceSchedule,
    maintenance_competence,
    asset_location,
    asset_system,
    asset_worker_assignment,
    cause_role,
    down_event_cause,
    fault_cause_effect,
    level_competence,
    order_asset,
    role_task,
    system_aggregate,
    task_competence,
    task_material,
    task_worker,
    worker_competence,
    worker_shift,
)

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
        # Junction tables first (reverse dependency order)
        "maintenance_competence",
        "task_competence",
        "task_material",
        "task_worker",
        "level_competence",
        "cause_role",
        "role_task",
        "down_event_cause",
        "order_asset",
        "asset_worker_assignment",
        "asset_location",
        "asset_system",
        "system_aggregate",
        "worker_competence",
        "worker_shift",
        # Original tables
        "sensor_data",
        "maintenance_schedules",
        "fault_cause_effect",
        "faults",
        "sensors",
        "assets",
        # New entity tables
        "down_events",
        "orders",
        "materials",
        "causes",
        "tasks",
        "workers",
        "shifts",
        "competences",
        "levels",
        "roles",
        "systems",
        "aggregates",
        "locations",
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


async def seed_sensors(session: AsyncSession, assets: dict[str, Asset]) -> dict[str, Sensor]:
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


async def seed_faults(session: AsyncSession, assets: dict[str, Asset]) -> dict[str, Fault]:
    """Create faults with cause-effect links. Returns fault code -> Fault."""
    count = await session.scalar(func.count(Fault.id))
    if count and count > 0:
        logger.info(f"Faults already exist ({count}), skipping.")
        return {f.code: f for f in (await session.scalars(select(Fault))).all()}

    now = datetime.now(timezone.utc)

    fault_specs = [
        # (code, name, description, severity, status, asset_name, resolved)
        (
            "B-HP-001",
            "High Pressure Warning",
            "Boiler pressure exceeded safe threshold",
            "high",
            "open",
            "Boiler Unit 01",
            False,
        ),
        (
            "B-LW-001",
            "Low Water Level",
            "Boiler water level dropped below minimum operating range",
            "critical",
            "open",
            "Boiler Unit 01",
            False,
        ),
        (
            "B-TL-001",
            "Tube Leak",
            "Detected leakage in boiler tubes",
            "critical",
            "in_progress",
            "Boiler Unit 01",
            False,
        ),
        (
            "T-BV-001",
            "Bearing Vibration High",
            "Turbine bearing vibration exceeds acceptable limits",
            "high",
            "open",
            "Steam Turbine 01",
            False,
        ),
        (
            "T-SSL-001",
            "Steam Seal Leak",
            "Steam leaking through turbine shaft seals",
            "medium",
            "resolved",
            "Steam Turbine 01",
            True,
        ),
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


async def seed_sensor_data(session: AsyncSession, sensors: dict[str, Sensor]) -> None:
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
    logger.info(
        f"Created {total_sensors * HOURS_OF_DATA} sensor data rows across {total_sensors} sensors."
    )


async def seed_maintenance_schedules(
    session: AsyncSession, assets: dict[str, Asset]
) -> dict[str, MaintenanceSchedule]:
    """Create maintenance schedules linked to assets."""
    count = await session.scalar(func.count(MaintenanceSchedule.id))
    if count and count > 0:
        logger.info(f"Maintenance schedules already exist ({count}), skipping.")
        return {ms.title: ms for ms in (await session.scalars(select(MaintenanceSchedule))).all()}

    now = datetime.now(timezone.utc)

    schedules = [
        # (title, description, type, status, priority, asset_name, recurrence, hours, days_offset)
        (
            "Boiler Annual Inspection",
            "Comprehensive annual inspection of Boiler Unit 01 including pressure vessel, safety valves, and controls",
            "preventive",
            "scheduled",
            "high",
            "Boiler Unit 01",
            "yearly",
            16.0,
            30,
        ),
        (
            "Tube Leak Repair",
            "Emergency repair of detected tube leak in Boiler Unit 01",
            "corrective",
            "in_progress",
            "critical",
            "Boiler Unit 01",
            "none",
            8.0,
            0,
        ),
        (
            "Safety Valve Calibration",
            "Calibration and testing of boiler safety relief valves",
            "preventive",
            "scheduled",
            "medium",
            "Boiler Unit 01",
            "quarterly",
            4.0,
            14,
        ),
        (
            "Feed Water Pump Overhaul",
            "Complete disassembly and inspection of feed water pump bearings and seals",
            "preventive",
            "scheduled",
            "medium",
            "Feed Water Pump",
            "yearly",
            12.0,
            60,
        ),
        (
            "Combustion Efficiency Test",
            "Flue gas analysis and combustion tuning",
            "predictive",
            "scheduled",
            "low",
            "Combustion Chamber",
            "monthly",
            3.0,
            7,
        ),
        (
            "Turbine Bearing Replacement",
            "Replacement of high-vibration turbine bearings",
            "corrective",
            "scheduled",
            "high",
            "Steam Turbine 01",
            "none",
            24.0,
            10,
        ),
        (
            "Turbine Vibration Analysis",
            "Predictive vibration monitoring and analysis",
            "predictive",
            "completed",
            "medium",
            "Steam Turbine 01",
            "monthly",
            2.0,
            -5,
        ),
        (
            "Steam Seal Replacement",
            "Replacement of worn turbine shaft seals",
            "corrective",
            "completed",
            "medium",
            "Steam Turbine 01",
            "none",
            10.0,
            -10,
        ),
        (
            "Generator Winding Inspection",
            "Thermographic and insulation resistance testing of generator windings",
            "preventive",
            "scheduled",
            "medium",
            "Generator",
            "quarterly",
            6.0,
            21,
        ),
        (
            "Cooling System Flush",
            "Full coolant drain, flush, and refill with new coolant",
            "preventive",
            "scheduled",
            "low",
            "Cooling System",
            "quarterly",
            4.0,
            45,
        ),
    ]

    ms_dict = {}
    for (
        title,
        desc,
        mtype,
        status,
        priority,
        asset_name,
        recurrence,
        est_hours,
        days_offset,
    ) in schedules:
        asset = assets[asset_name]
        scheduled_date = now + timedelta(days=days_offset)
        completed_date = None
        if status == "completed":
            completed_date = scheduled_date + timedelta(hours=est_hours)

        ms = MaintenanceSchedule(
            asset_id=asset.id,
            title=title,
            description=desc,
            maintenance_type=mtype,
            status=status,
            priority=priority,
            scheduled_date=scheduled_date,
            completed_date=completed_date,
            recurrence=recurrence,
            estimated_duration_hours=est_hours,
        )
        session.add(ms)
        ms_dict[title] = ms

    await session.flush()
    await session.commit()
    logger.info(f"Created {len(schedules)} maintenance schedules.")
    return ms_dict


async def seed_levels(session: AsyncSession, roles: dict[str, Role]) -> dict[str, Level]:
    count = await session.scalar(func.count(Level.id))
    if count and count > 0:
        return {l.name: l for l in (await session.scalars(select(Level))).all()}
    levels = {}
    # Role-specific levels: (name, rank, description, role_name)
    for name, rank, desc, role_name in [
        ("Junior Mechanic", 1, "Basic mechanical skills", "Senior Mechanic"),
        ("Mechanic", 2, "Solid mechanical knowledge", "Senior Mechanic"),
        ("Senior Mechanic", 3, "Expert mechanical repair", "Senior Mechanic"),
        ("Junior Electrician", 1, "Basic electrical skills", "Electrician"),
        ("Electrician", 2, "Qualified electrician", "Electrician"),
        ("Senior Electrician", 3, "Expert electrical systems", "Electrician"),
        ("Junior Boiler Operator", 1, "Basic boiler operations", "Boiler Operator"),
        ("Boiler Operator", 2, "Qualified boiler operator", "Boiler Operator"),
        ("Senior Boiler Operator", 3, "Expert boiler operations", "Boiler Operator"),
        ("Junior Turbine Engineer", 1, "Basic turbine knowledge", "Turbine Engineer"),
        ("Turbine Engineer", 2, "Qualified turbine specialist", "Turbine Engineer"),
        ("Senior Turbine Engineer", 3, "Expert turbine operations", "Turbine Engineer"),
        ("Shift Supervisor I", 1, "Junior shift coordination", "Shift Supervisor"),
        ("Shift Supervisor II", 2, "Senior shift coordination", "Shift Supervisor"),
        ("Safety Officer I", 1, "Basic safety compliance", "Safety Officer"),
        ("Safety Officer II", 2, "Senior safety compliance", "Safety Officer"),
        ("Junior Planner", 1, "Basic maintenance planning", "Maintenance Planner"),
        ("Maintenance Planner", 2, "Senior maintenance planning", "Maintenance Planner"),
        ("Instrument Tech I", 1, "Basic instrument calibration", "Instrument Technician"),
        ("Instrument Tech II", 2, "Senior instrument calibration", "Instrument Technician"),
    ]:
        level = Level(name=name, rank=rank, description=desc, role_id=roles[role_name].id)
        session.add(level)
        levels[name] = level
    await session.commit()
    logger.info(f"Created {len(levels)} levels.")
    return levels


async def seed_competences(session: AsyncSession) -> dict[str, Competence]:
    count = await session.scalar(func.count(Competence.id))
    if count and count > 0:
        return {c.name: c for c in (await session.scalars(select(Competence))).all()}
    competences = {}
    for name, desc, cat in [
        ("Boiler Operation", "Operate boiler systems", "Operations"),
        ("Pump Maintenance", "Maintain industrial pumps", "Mechanical"),
        ("Electrical Systems", "High/low voltage systems", "Electrical"),
        ("Vibration Analysis", "Vibration pattern analysis", "Diagnostics"),
        ("Welding", "Structural and pipe welding", "Fabrication"),
        ("PLC Programming", "PLC troubleshooting", "Automation"),
        ("Thermal Imaging", "Thermal camera inspection", "Diagnostics"),
        ("Pipe Fitting", "Industrial piping", "Mechanical"),
        ("Safety Procedures", "Safety protocols", "Safety"),
        ("Turbine Operation", "Steam turbine ops", "Operations"),
    ]:
        c = Competence(name=name, description=desc, category=cat)
        session.add(c)
        competences[name] = c
    await session.commit()
    logger.info(f"Created {len(competences)} competences.")
    return competences


async def seed_roles(session: AsyncSession) -> dict[str, Role]:
    count = await session.scalar(func.count(Role.id))
    if count and count > 0:
        return {r.name: r for r in (await session.scalars(select(Role))).all()}
    roles = {}
    for name, desc in [
        ("Senior Mechanic", "Leads mechanical repair"),
        ("Electrician", "Electrical systems"),
        ("Boiler Operator", "Boiler operation"),
        ("Turbine Engineer", "Turbine specialist"),
        ("Shift Supervisor", "Shift coordination"),
        ("Safety Officer", "Safety compliance"),
        ("Maintenance Planner", "Maintenance planning"),
        ("Instrument Technician", "Instrument calibration"),
    ]:
        r = Role(name=name, description=desc)
        session.add(r)
        roles[name] = r
    await session.commit()
    logger.info(f"Created {len(roles)} roles.")
    return roles


async def seed_shifts(session: AsyncSession) -> dict[str, Shift]:
    from datetime import time

    count = await session.scalar(func.count(Shift.id))
    if count and count > 0:
        return {s.name: s for s in (await session.scalars(select(Shift))).all()}
    shifts = {}
    for name, start, end, desc in [
        ("Morning Shift", time(6, 0), time(14, 0), "06:00 - 14:00"),
        ("Afternoon Shift", time(14, 0), time(22, 0), "14:00 - 22:00"),
        ("Night Shift", time(22, 0), time(6, 0), "22:00 - 06:00"),
    ]:
        s = Shift(name=name, start_time=start, end_time=end, description=desc)
        session.add(s)
        shifts[name] = s
    await session.commit()
    logger.info(f"Created {len(shifts)} shifts.")
    return shifts


async def seed_locations(session: AsyncSession) -> dict[str, Location]:
    count = await session.scalar(func.count(Location.id))
    if count and count > 0:
        return {l.name: l for l in (await session.scalars(select(Location))).all()}
    plant = Location(name="Main Plant", description="Main plant", location_type="plant")
    session.add(plant)
    await session.flush()
    building_a = Location(
        name="Building A", description="Boiler house", location_type="building", parent_id=plant.id
    )
    building_b = Location(
        name="Building B", description="Turbine hall", location_type="building", parent_id=plant.id
    )
    session.add_all([building_a, building_b])
    await session.flush()
    boiler_room = Location(
        name="Boiler Room A",
        description="Boiler area",
        location_type="room",
        parent_id=building_a.id,
    )
    turbine_hall = Location(
        name="Turbine Hall B",
        description="Turbine floor",
        location_type="room",
        parent_id=building_b.id,
    )
    control_room = Location(
        name="Control Room",
        description="Central control",
        location_type="room",
        parent_id=building_b.id,
    )
    session.add_all([boiler_room, turbine_hall, control_room])
    locs = {
        "Main Plant": plant,
        "Building A": building_a,
        "Building B": building_b,
        "Boiler Room A": boiler_room,
        "Turbine Hall B": turbine_hall,
        "Control Room": control_room,
    }
    await session.commit()
    logger.info(f"Created {len(locs)} locations.")
    return locs


async def seed_aggregates(session: AsyncSession) -> dict[str, Aggregate]:
    count = await session.scalar(func.count(Aggregate.id))
    if count and count > 0:
        return {a.name: a for a in (await session.scalars(select(Aggregate))).all()}
    aggs = {}
    for name, desc in [
        ("Steam Generation Line", "Steam gen line"),
        ("Power Generation Unit", "Turbine-gen set"),
        ("Cooling Circuit", "Cooling water circuit"),
    ]:
        a = Aggregate(name=name, description=desc)
        session.add(a)
        aggs[name] = a
    await session.commit()
    logger.info(f"Created {len(aggs)} aggregates.")
    return aggs


async def seed_systems(session: AsyncSession) -> dict[str, System]:
    count = await session.scalar(func.count(System.id))
    if count and count > 0:
        return {s.name: s for s in (await session.scalars(select(System))).all()}
    systems = {}
    for name, desc in [
        ("Feed Water System", "Feed water supply"),
        ("Combustion System", "Fuel delivery"),
        ("Steam System", "Steam piping"),
        ("Turbine System", "Turbine and governor"),
        ("Generator System", "Generator and excitation"),
        ("Cooling Water System", "Cooling pumps"),
        ("Lubrication System", "Bearing lubrication"),
    ]:
        s = System(name=name, description=desc)
        session.add(s)
        systems[name] = s
    await session.commit()
    logger.info(f"Created {len(systems)} systems.")
    return systems


async def seed_workers(session, competences, levels, shifts):
    count = await session.scalar(func.count(Worker.id))
    if count and count > 0:
        return {w.name: w for w in (await session.scalars(select(Worker))).all()}
    workers = {}
    worker_specs = [
        ("John Smith", "EMP-001", "john.smith@plant.com", "active", "Senior Boiler Operator"),
        ("Maria Garcia", "EMP-002", "maria.garcia@plant.com", "active", "Senior Electrician"),
        ("Robert Chen", "EMP-003", "robert.chen@plant.com", "active", "Senior Turbine Engineer"),
        ("Sarah Johnson", "EMP-004", "sarah.johnson@plant.com", "active", "Mechanic"),
        ("Ahmed Hassan", "EMP-005", "ahmed.hassan@plant.com", "active", "Electrician"),
        ("Lisa Wong", "EMP-006", "lisa.wong@plant.com", "on_leave", "Safety Officer II"),
        ("James Brown", "EMP-007", "james.brown@plant.com", "active", "Senior Mechanic"),
    ]
    for name, eid, email, st, lname in worker_specs:
        w = Worker(
            name=name,
            employee_id=eid,
            email=email,
            status=st,
            level_id=levels.get(lname, {}).id if lname in levels else None,
        )
        session.add(w)
        workers[name] = w
    await session.flush()
    # Assign competences
    comp_map = [
        ("John Smith", [("Boiler Operation", "Advanced"), ("Safety Procedures", "Expert")]),
        (
            "Maria Garcia",
            [("Electrical Systems", "Advanced"), ("PLC Programming", "Intermediate")],
        ),
        ("Robert Chen", [("Vibration Analysis", "Expert"), ("Turbine Operation", "Advanced")]),
        ("Sarah Johnson", [("Pump Maintenance", "Advanced"), ("Welding", "Intermediate")]),
        (
            "Ahmed Hassan",
            [("Thermal Imaging", "Advanced"), ("Electrical Systems", "Intermediate")],
        ),
        ("Lisa Wong", [("Safety Procedures", "Advanced")]),
        ("James Brown", [("Pipe Fitting", "Expert"), ("Welding", "Advanced")]),
    ]
    for wname, comps in comp_map:
        for cname, lname in comps:
            await session.execute(
                worker_competence.insert().values(
                    worker_id=workers[wname].id,
                    competence_id=competences[cname].id,
                    level_id=levels.get(lname, {}).id if lname in levels else None,
                )
            )
    # Assign shifts
    for wname, sname in [
        ("John Smith", "Morning Shift"),
        ("Maria Garcia", "Morning Shift"),
        ("Robert Chen", "Afternoon Shift"),
        ("Sarah Johnson", "Afternoon Shift"),
        ("Ahmed Hassan", "Night Shift"),
        ("James Brown", "Morning Shift"),
    ]:
        await session.execute(
            worker_shift.insert().values(worker_id=workers[wname].id, shift_id=shifts[sname].id)
        )
    await session.commit()
    logger.info(f"Created {len(workers)} workers.")
    return workers


async def seed_tasks(session, maintenance_schedules, shifts):
    count = await session.scalar(func.count(Task.id))
    if count and count > 0:
        return {t.name: t for t in (await session.scalars(select(Task))).all()}
    tasks = {}
    # (name, desc, ttype, st, hrs, doc, schedule_title, shift_name, assigned_to, action_type, seq_order)
    task_specs = [
        (
            "Bearing Replacement",
            "Replace turbine bearings",
            "repair",
            "pending",
            24.0,
            "/docs/bearing-replace.pdf",
            "Turbine Bearing Replacement",
            "Morning Shift",
            "Mechanical Team",
            "repair",
            0,
        ),
        ("Safety Valve Testing", "Test safety valves", "inspection", "pending", 4.0, None, "Safety Valve Calibration", "Morning Shift", "Instrumentation Team", "inspection", 0),
        (
            "Boiler Tube Inspection",
            "Internal tube inspection",
            "inspection",
            "completed",
            8.0,
            "/docs/tube-inspect.pdf",
            "Boiler Annual Inspection",
            "Afternoon Shift",
            "Engineering Team A",
            "inspection",
            1,
        ),
        ("Pump Seal Replacement", "Replace pump seals", "repair", "in_progress", 6.0, None, "Feed Water Pump Overhaul", "Morning Shift", "Mechanical Team", "repair", 0),
        ("Combustion Tuning", "Optimize combustion", "calibration", "pending", 3.0, None, "Combustion Efficiency Test", "Afternoon Shift", "Operations Team", "calibration", 0),
        ("Generator Winding Test", "Winding insulation test", "inspection", "pending", 6.0, None, "Generator Winding Inspection", "Morning Shift", "Electrical Team", "inspection", 0),
        ("Turbine Alignment", "Turbine-generator alignment", "calibration", "pending", 12.0, None, "Turbine Bearing Replacement", "Morning Shift", "Mechanical Team", "verification", 1),
    ]
    for name, desc, ttype, st, hrs, doc, schedule_title, shift_name, assigned_to, action_type, seq_order in task_specs:
        ms = maintenance_schedules.get(schedule_title)
        shift = shifts.get(shift_name)
        t = Task(
            name=name,
            description=desc,
            task_type=ttype,
            status=st,
            estimated_duration_hours=hrs,
            doc_link=doc,
            maintenance_schedule_id=ms.id if ms else None,
            shift_id=shift.id if shift else None,
            assigned_to=assigned_to,
            action_type=action_type,
            sequence_order=seq_order,
        )
        session.add(t)
        tasks[name] = t
    await session.commit()
    logger.info(f"Created {len(tasks)} tasks.")
    return tasks




async def seed_causes(session):
    count = await session.scalar(func.count(Cause.id))
    if count and count > 0:
        return {c.name: c for c in (await session.scalars(select(Cause))).all()}
    causes = {}
    for name, desc, cat, sev in [
        ("Bearing Wear", "Prolonged operation wear", "mechanical", "medium"),
        ("Corrosion", "Chemical corrosion", "chemical", "high"),
        ("Thermal Fatigue", "Thermal cycling cracks", "thermal", "high"),
        ("Improper Lubrication", "Wrong lubricant", "operational", "medium"),
        ("Vibration Damage", "Excessive vibration", "mechanical", "critical"),
        ("Electrical Fault", "Insulation failure", "electrical", "critical"),
        ("Seal Degradation", "Material degradation", "mechanical", "low"),
        ("Foreign Object Damage", "Debris in system", "operational", "medium"),
    ]:
        c = Cause(name=name, description=desc, category=cat, severity=sev)
        session.add(c)
        causes[name] = c
    await session.commit()
    logger.info(f"Created {len(causes)} causes.")
    return causes


async def seed_materials(session):
    count = await session.scalar(func.count(Material.id))
    if count and count > 0:
        return {m.name: m for m in (await session.scalars(select(Material))).all()}
    materials = {}
    for name, pn, desc, qty, unit in [
        ("Bearing 6205-2RS", "SKF-6205", "Ball bearing", 12, "pcs"),
        ("Mechanical Seal DN40", "CRN-DN40", "Seal for DN40", 4, "pcs"),
        ("Boiler Tube SA213-T12", "BT-T12-50", "Boiler tube 50mm", 20, "m"),
        ("Gasket Material 3mm", "GLD-003", "Fiber gasket sheet", 5, "m2"),
        ("Turbine Oil ISO 46", "TO-46-200", "Lubricating oil", 3, "barrel"),
        ("Safety Valve Spring", "SVS-150", "Valve spring", 6, "pcs"),
        ("Welding Electrode E7018", "WE-7018", "Welding electrode", 50, "kg"),
        ("Coolant Concentrate", "CC-EG-25", "Ethylene glycol", 10, "L"),
    ]:
        m = Material(name=name, part_number=pn, description=desc, quantity_in_stock=qty, unit=unit)
        session.add(m)
        materials[name] = m
    await session.commit()
    logger.info(f"Created {len(materials)} materials.")
    return materials


async def seed_down_events(session, assets, causes, faults, maintenance_schedules):
    count = await session.scalar(func.count(DownEvent.id))
    if count and count > 0:
        return {}
    now = datetime.now(timezone.utc)
    events = {}
    # (desc, asset_name, duration, severity, status, cause_names, fault_code, schedule_title)
    for desc, aname, dur, sev, st, cnames, fault_code, schedule_title in [
        (
            "Boiler emergency shutdown",
            "Boiler Unit 01",
            180,
            "high",
            "resolved",
            ["Thermal Fatigue", "Corrosion"],
            "B-TL-001",
            "Tube Leak Repair",
        ),
        (
            "Turbine vibration trip",
            "Steam Turbine 01",
            360,
            "critical",
            "active",
            ["Vibration Damage", "Bearing Wear"],
            "T-BV-001",
            "Turbine Bearing Replacement",
        ),
        ("Pump seal failure", "Feed Water Pump", 90, "medium", "resolved", ["Seal Degradation"], "B-TL-001", None),
        (
            "Generator overheat",
            "Generator",
            240,
            "high",
            "active",
            ["Thermal Fatigue", "Electrical Fault"],
            "B-HP-001",
            None,
        ),
        ("Cooling system leak", "Cooling System", 60, "low", "resolved", ["Corrosion"], "B-TL-001", None),
        # Unresolved down events -- still ongoing
        (
            "Boiler low water level trip",
            "Boiler Unit 01",
            0,
            "critical",
            "active",
            ["Corrosion", "Improper Lubrication"],
            "B-LW-001",
            "Boiler Annual Inspection",
        ),
        (
            "Combustion chamber flame failure",
            "Combustion Chamber",
            0,
            "critical",
            "active",
            ["Foreign Object Damage"],
            "B-TL-001",
            None,
        ),
        (
            "Feed water pump cavitation",
            "Feed Water Pump",
            0,
            "high",
            "active",
            ["Bearing Wear", "Seal Degradation"],
            "B-LW-001",
            "Feed Water Pump Overhaul",
        ),
        (
            "Turbine lubrication system alarm",
            "Steam Turbine 01",
            0,
            "high",
            "active",
            ["Improper Lubrication", "Bearing Wear"],
            "T-BV-001",
            None,
        ),
    ]:
        started = now - timedelta(hours=random.randint(1, 48))
        ended = started + timedelta(minutes=dur) if st == "resolved" else None
        actual_dur = dur if st == "resolved" else None
        fault = faults[fault_code]
        fault.name = desc
        fault_id = fault.id
        ms_id = maintenance_schedules.get(schedule_title).id if schedule_title and maintenance_schedules.get(schedule_title) else None
        e = DownEvent(
            asset_id=assets[aname].id,
            fault_id=fault_id,
            maintenance_schedule_id=ms_id,
            started_at=started,
            ended_at=ended,
            downtime_minutes=actual_dur,
            severity=sev,
            status=st,
        )
        session.add(e)
        events[desc] = e
    await session.flush()
    # Re-link cause associations from the expanded list
    cause_map = {
        "Boiler emergency shutdown": ["Thermal Fatigue", "Corrosion"],
        "Turbine vibration trip": ["Vibration Damage", "Bearing Wear"],
        "Pump seal failure": ["Seal Degradation"],
        "Generator overheat": ["Thermal Fatigue", "Electrical Fault"],
        "Cooling system leak": ["Corrosion"],
        "Boiler low water level trip": ["Corrosion", "Improper Lubrication"],
        "Combustion chamber flame failure": ["Foreign Object Damage"],
        "Feed water pump cavitation": ["Bearing Wear", "Seal Degradation"],
        "Turbine lubrication system alarm": ["Improper Lubrication", "Bearing Wear"],
    }
    for desc, cnames in cause_map.items():
        for cn in cnames:
            await session.execute(
                down_event_cause.insert().values(
                    down_event_id=events[desc].id,
                    cause_id=causes[cn].id,
                )
            )
    await session.commit()
    logger.info(f"Created {len(events)} down events.")
    return events


async def seed_orders(session, assets):
    count = await session.scalar(func.count(Order.id))
    if count and count > 0:
        return {}
    now = datetime.now(timezone.utc)
    orders = {}
    links = {
        "WO-2025-001": ["Boiler Unit 01"],
        "WO-2025-002": ["Steam Turbine 01"],
        "WO-2025-003": ["Boiler Unit 01"],
        "WO-2025-004": ["Feed Water Pump"],
        "WO-2025-005": ["Generator"],
        "WO-2025-006": ["Cooling System"],
        # Orders linked to unresolved down events
        "WO-2025-007": ["Boiler Unit 01"],
        "WO-2025-008": ["Combustion Chamber"],
        "WO-2025-009": ["Feed Water Pump"],
        "WO-2025-010": ["Steam Turbine 01"],
    }
    for num, title, desc, otype, st, pri in [
        (
            "WO-2025-001",
            "Boiler Tube Repair",
            "Emergency tube repair",
            "repair",
            "in_progress",
            "critical",
        ),
        (
            "WO-2025-002",
            "Turbine Bearing Inspection",
            "Bearing inspection",
            "inspection",
            "open",
            "high",
        ),
        (
            "WO-2025-003",
            "Annual Boiler Inspection",
            "Scheduled inspection",
            "maintenance",
            "open",
            "medium",
        ),
        (
            "WO-2025-004",
            "Pump Seal Replacement",
            "Seal replacement",
            "repair",
            "completed",
            "medium",
        ),
        (
            "WO-2025-005",
            "Generator Thermography",
            "Thermographic survey",
            "inspection",
            "open",
            "low",
        ),
        ("WO-2025-006", "Cooling System Flush", "Quarterly flush", "maintenance", "open", "low"),
        # Orders for unresolved down events
        (
            "WO-2025-007",
            "Boiler Low Water Emergency",
            "Investigate and resolve low water level trip",
            "repair",
            "in_progress",
            "critical",
        ),
        (
            "WO-2025-008",
            "Combustion Chamber Flame Restore",
            "Restore combustion after flame failure",
            "repair",
            "open",
            "critical",
        ),
        (
            "WO-2025-009",
            "Pump Cavitation Investigation",
            "Diagnose and fix feed water pump cavitation",
            "inspection",
            "open",
            "high",
        ),
        (
            "WO-2025-010",
            "Turbine Lube System Overhaul",
            "Overhaul turbine lubrication system after alarm",
            "repair",
            "in_progress",
            "high",
        ),
    ]:
        o = Order(
            order_number=num,
            title=title,
            description=desc,
            order_type=otype,
            status=st,
            priority=pri,
            requested_date=now + timedelta(days=random.randint(0, 14)),
        )
        session.add(o)
        orders[num] = o
    await session.flush()
    for num, anames in links.items():
        for aname in anames:
            await session.execute(
                order_asset.insert().values(
                    order_id=orders[num].id,
                    asset_id=assets[aname].id,
                )
            )
    await session.commit()
    logger.info(f"Created {len(orders)} orders.")
    return orders


async def seed_associations(
    session,
    assets,
    workers,
    systems,
    aggregates,
    locations,
    competences,
    tasks,
    materials,
    causes,
    roles,
    maintenance_schedules,
    levels,
):
    # Asset <-> Worker (every asset has assigned workers)
    for aname, wname in [
        ("Boiler Unit 01", "John Smith"),
        ("Boiler Unit 01", "Sarah Johnson"),
        ("Steam Turbine 01", "Robert Chen"),
        ("Steam Turbine 01", "Ahmed Hassan"),
        ("Generator", "Maria Garcia"),
        ("Feed Water Pump", "Sarah Johnson"),
        ("Feed Water Pump", "James Brown"),
        ("Cooling System", "James Brown"),
        ("Combustion Chamber", "John Smith"),
        ("Combustion Chamber", "Ahmed Hassan"),
        ("Power Plant", "Lisa Wong"),
    ]:
        await session.execute(
            asset_worker_assignment.insert().values(
                asset_id=assets[aname].id,
                worker_id=workers[wname].id,
            )
        )
    # Asset <-> System (every asset connected to its systems)
    for aname, snames in [
        (
            "Boiler Unit 01",
            [
                "Feed Water System",
                "Combustion System",
                "Steam System",
            ],
        ),
        (
            "Steam Turbine 01",
            [
                "Steam System",
                "Turbine System",
                "Lubrication System",
            ],
        ),
        ("Generator", ["Generator System", "Cooling Water System"]),
        ("Feed Water Pump", ["Feed Water System"]),
        ("Cooling System", ["Cooling Water System"]),
        ("Combustion Chamber", ["Combustion System"]),
    ]:
        for sn in snames:
            await session.execute(
                asset_system.insert().values(
                    asset_id=assets[aname].id,
                    system_id=systems[sn].id,
                )
            )
    # System <-> Aggregate
    for sn, agg in [
        ("Feed Water System", "Steam Generation Line"),
        ("Combustion System", "Steam Generation Line"),
        ("Steam System", "Steam Generation Line"),
        ("Turbine System", "Power Generation Unit"),
        ("Generator System", "Power Generation Unit"),
        ("Cooling Water System", "Cooling Circuit"),
        ("Lubrication System", "Power Generation Unit"),
    ]:
        await session.execute(
            system_aggregate.insert().values(
                system_id=systems[sn].id,
                aggregate_id=aggregates[agg].id,
            )
        )
    # Asset <-> Location (every asset has a physical location)
    for aname, loc in [
        ("Boiler Unit 01", "Boiler Room A"),
        ("Feed Water Pump", "Boiler Room A"),
        ("Combustion Chamber", "Boiler Room A"),
        ("Steam Turbine 01", "Turbine Hall B"),
        ("Generator", "Turbine Hall B"),
        ("Cooling System", "Turbine Hall B"),
        ("Power Plant", "Main Plant"),
    ]:
        await session.execute(
            asset_location.insert().values(
                asset_id=assets[aname].id,
                location_id=locations[loc].id,
            )
        )
    # Cause <-> Role (all 8 causes linked to responsible roles)
    for cn, rn in [
        ("Bearing Wear", "Senior Mechanic"),
        ("Corrosion", "Maintenance Planner"),
        ("Thermal Fatigue", "Senior Mechanic"),
        ("Vibration Damage", "Turbine Engineer"),
        ("Electrical Fault", "Electrician"),
        ("Seal Degradation", "Senior Mechanic"),
        ("Foreign Object Damage", "Shift Supervisor"),
        ("Improper Lubrication", "Boiler Operator"),
    ]:
        await session.execute(
            cause_role.insert().values(
                cause_id=causes[cn].id,
                role_id=roles[rn].id,
            )
        )
    # Role <-> Task (all roles linked to tasks they can perform)
    for rn, tn in [
        ("Senior Mechanic", "Bearing Replacement"),
        ("Senior Mechanic", "Pump Seal Replacement"),
        ("Senior Mechanic", "Boiler Tube Inspection"),
        ("Instrument Technician", "Safety Valve Testing"),
        ("Electrician", "Generator Winding Test"),
        ("Turbine Engineer", "Turbine Alignment"),
        ("Boiler Operator", "Combustion Tuning"),
        ("Safety Officer", "Safety Valve Testing"),
    ]:
        await session.execute(
            role_task.insert().values(
                role_id=roles[rn].id,
                task_id=tasks[tn].id,
            )
        )
    # Task <-> Competence (all tasks linked to required competences)
    for tn, cn in [
        ("Bearing Replacement", "Vibration Analysis"),
        ("Bearing Replacement", "Turbine Operation"),
        ("Safety Valve Testing", "Boiler Operation"),
        ("Pump Seal Replacement", "Pump Maintenance"),
        ("Combustion Tuning", "Boiler Operation"),
        ("Generator Winding Test", "Electrical Systems"),
        ("Turbine Alignment", "Turbine Operation"),
        ("Boiler Tube Inspection", "Welding"),
        ("Boiler Tube Inspection", "Thermal Imaging"),
    ]:
        await session.execute(
            task_competence.insert().values(
                task_id=tasks[tn].id,
                competence_id=competences[cn].id,
            )
        )
    # Task <-> Material
    for tn, mn, qty in [
        ("Bearing Replacement", "Bearing 6205-2RS", 2),
        ("Pump Seal Replacement", "Mechanical Seal DN40", 1),
        ("Boiler Tube Inspection", "Boiler Tube SA213-T12", 2),
        ("Safety Valve Testing", "Safety Valve Spring", 1),
        ("Bearing Replacement", "Turbine Oil ISO 46", 1),
        ("Pump Seal Replacement", "Gasket Material 3mm", 2),
        ("Boiler Tube Inspection", "Welding Electrode E7018", 5),
        ("Turbine Alignment", "Turbine Oil ISO 46", 1),
    ]:
        await session.execute(
            task_material.insert().values(
                task_id=tasks[tn].id,
                material_id=materials[mn].id,
                quantity_required=qty,
            )
        )
    # MaintenanceSchedule <-> Competence
    for ms_title, cn in [
        ("Boiler Annual Inspection", "Vibration Analysis"),
        ("Boiler Annual Inspection", "Thermal Imaging"),
        ("Tube Leak Repair", "Welding"),
        ("Tube Leak Repair", "Pipe Fitting"),
        ("Safety Valve Calibration", "Safety Procedures"),
        ("Turbine Bearing Replacement", "Turbine Operation"),
        ("Combustion Efficiency Test", "Boiler Operation"),
        ("Feed Water Pump Overhaul", "Pipe Fitting"),
    ]:
        ms = maintenance_schedules.get(ms_title)
        if ms:
            await session.execute(
                maintenance_competence.insert().values(
                    maintenance_schedule_id=ms.id,
                    competence_id=competences[cn].id,
                )
            )
    # Task <-> Worker
    for tn, wname in [
        ("Bearing Replacement", "Robert Chen"),
        ("Bearing Replacement", "James Brown"),
        ("Safety Valve Testing", "John Smith"),
        ("Boiler Tube Inspection", "Sarah Johnson"),
        ("Boiler Tube Inspection", "John Smith"),
        ("Pump Seal Replacement", "Sarah Johnson"),
        ("Pump Seal Replacement", "James Brown"),
        ("Combustion Tuning", "John Smith"),
        ("Generator Winding Test", "Maria Garcia"),
        ("Turbine Alignment", "Robert Chen"),
    ]:
        await session.execute(
            task_worker.insert().values(
                task_id=tasks[tn].id,
                worker_id=workers[wname].id,
            )
        )
    # Level <-> Competence
    for lname, cnames in [
        ("Junior Mechanic", ["Safety Procedures", "Pipe Fitting"]),
        ("Mechanic", ["Safety Procedures", "Pump Maintenance", "Pipe Fitting", "Welding"]),
        ("Senior Mechanic", ["Pump Maintenance", "Welding", "Pipe Fitting", "Thermal Imaging"]),
        ("Junior Electrician", ["Safety Procedures", "Electrical Systems"]),
        ("Electrician", ["Electrical Systems", "PLC Programming"]),
        ("Senior Electrician", ["Electrical Systems", "PLC Programming", "Thermal Imaging"]),
        ("Junior Boiler Operator", ["Safety Procedures", "Boiler Operation"]),
        ("Boiler Operator", ["Boiler Operation", "Safety Procedures"]),
        ("Senior Boiler Operator", ["Boiler Operation", "Thermal Imaging", "Safety Procedures"]),
        ("Junior Turbine Engineer", ["Safety Procedures", "Turbine Operation"]),
        ("Turbine Engineer", ["Turbine Operation", "Vibration Analysis"]),
        ("Senior Turbine Engineer", ["Vibration Analysis", "Turbine Operation", "Thermal Imaging"]),
        ("Shift Supervisor I", ["Safety Procedures"]),
        ("Shift Supervisor II", ["Safety Procedures", "Boiler Operation"]),
        ("Safety Officer I", ["Safety Procedures"]),
        ("Safety Officer II", ["Safety Procedures", "Thermal Imaging"]),
        ("Junior Planner", ["Safety Procedures", "Pipe Fitting"]),
        ("Maintenance Planner", ["Pipe Fitting", "Boiler Operation"]),
        ("Instrument Tech I", ["Safety Procedures"]),
        ("Instrument Tech II", ["Safety Procedures", "PLC Programming", "Thermal Imaging"]),
    ]:
        for cn in cnames:
            await session.execute(
                level_competence.insert().values(
                    level_id=levels[lname].id,
                    competence_id=competences[cn].id,
                )
            )
    await session.commit()
    logger.info("Created all association links.")


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
        competences = await seed_competences(session)
        roles = await seed_roles(session)
        levels = await seed_levels(session, roles)
        shifts = await seed_shifts(session)
        locations = await seed_locations(session)
        aggregates = await seed_aggregates(session)
        systems = await seed_systems(session)
        workers = await seed_workers(session, competences, levels, shifts)
        causes = await seed_causes(session)
        materials = await seed_materials(session)
        maintenance_schedules = await seed_maintenance_schedules(session, assets)
        tasks = await seed_tasks(session, maintenance_schedules, shifts)
        down_events = await seed_down_events(session, assets, causes, faults, maintenance_schedules)
        orders = await seed_orders(session, assets)
        await seed_sensor_data(session, sensors)
        await seed_associations(
            session,
            assets,
            workers,
            systems,
            aggregates,
            locations,
            competences,
            tasks,
            materials,
            causes,
            roles,
            maintenance_schedules,
            levels,
        )

    await engine.dispose()
    logger.info("Seeding complete.")


def main() -> None:
    clean = "--clean" in sys.argv
    asyncio.run(run(clean=clean))


if __name__ == "__main__":
    main()

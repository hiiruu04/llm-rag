"""MCP tools for querying the knowledge graph entities."""

from uuid import UUID

from sqlalchemy import select

from app.core.database import async_session_factory
from app.mcp.server import mcp_server
from app.models.asset import Asset
from app.models.cause import Cause
from app.models.competence import Competence
from app.models.down_event import DownEvent
from app.models.level import Level
from app.models.material import Material
from app.models.order import Order
from app.models.role import Role
from app.models.task import Task
from app.models.worker import Worker


@mcp_server.tool()
async def query_equipment(name: str = None, status: str = None, asset_type: str = None) -> str:
    """Query equipment (assets) by name, status, or type.

    Args:
        name: Filter by asset name (partial match)
        status: Filter by status (active, inactive, etc.)
        asset_type: Filter by asset type
    """
    async with async_session_factory() as db:
        query = select(Asset)
        if name:
            query = query.where(Asset.name.ilike(f"%{name}%"))
        if status:
            query = query.where(Asset.status == status)
        if asset_type:
            query = query.where(Asset.asset_type == asset_type)
        result = await db.execute(query.limit(20))
        assets = result.scalars().all()
        if not assets:
            return "No equipment found matching the criteria."
        lines = []
        for a in assets:
            lines.append(
                f"- {a.name} (type={a.asset_type}, "
                f"status={a.status}, location={a.location})"
            )
        return f"Found {len(assets)} equipment:\n" + "\n".join(lines)


@mcp_server.tool()
async def get_equipment_details(asset_id: str) -> str:
    """Get detailed information about a specific piece of equipment (asset).

    Args:
        asset_id: The UUID of the asset
    """
    async with async_session_factory() as db:
        result = await db.execute(select(Asset).where(Asset.id == UUID(asset_id)))
        asset = result.scalar_one_or_none()
        if not asset:
            return f"Asset {asset_id} not found."
        d = asset.to_dict()
        return (
            f"Equipment: {d['name']}\n"
            f"Type: {d['asset_type']}\n"
            f"Status: {d['status']}\n"
            f"Location: {d['location']}\n"
            f"Description: {d['description']}\n"
            f"Parent ID: {d.get('parent_id', 'None')}"
        )


@mcp_server.tool()
async def query_workers(name: str = None, status: str = None) -> str:
    """Query workers by name or status.

    Args:
        name: Filter by worker name (partial match)
        status: Filter by status (active, inactive, on_leave)
    """
    async with async_session_factory() as db:
        query = select(Worker)
        if name:
            query = query.where(Worker.name.ilike(f"%{name}%"))
        if status:
            query = query.where(Worker.status == status)
        result = await db.execute(query.limit(20))
        workers = result.scalars().all()
        if not workers:
            return "No workers found matching the criteria."
        lines = []
        for w in workers:
            lines.append(f"- {w.name} (employee_id={w.employee_id}, status={w.status})")
        return f"Found {len(workers)} workers:\n" + "\n".join(lines)


@mcp_server.tool()
async def get_worker_competences(worker_id: str) -> str:
    """Get competences and proficiency levels for a specific worker.

    Args:
        worker_id: The UUID of the worker
    """
    from app.models.graph_associations import worker_competence

    async with async_session_factory() as db:
        result = await db.execute(select(Worker).where(Worker.id == UUID(worker_id)))
        worker = result.scalar_one_or_none()
        if not worker:
            return f"Worker {worker_id} not found."

        stmt = (
            select(Competence, Level)
            .join(worker_competence, worker_competence.c.competence_id == Competence.id)
            .outerjoin(Level, worker_competence.c.level_id == Level.id)
            .where(worker_competence.c.worker_id == UUID(worker_id))
        )
        result = await db.execute(stmt)
        rows = result.all()
        if not rows:
            return f"Worker {worker.name} has no recorded competences."
        lines = [f"Worker: {worker.name}"]
        for comp, level in rows:
            level_str = f" ({level.name}, rank={level.rank})" if level else ""
            lines.append(f"  - {comp.name} [{comp.category}]{level_str}")
        return "\n".join(lines)


@mcp_server.tool()
async def find_qualified_workers(competence_name: str) -> str:
    """Find workers who have a specific competence.

    Args:
        competence_name: Name of the competence to search for (partial match)
    """
    from app.models.graph_associations import worker_competence

    async with async_session_factory() as db:
        stmt = (
            select(Worker, Competence)
            .join(worker_competence, worker_competence.c.worker_id == Worker.id)
            .join(Competence, worker_competence.c.competence_id == Competence.id)
            .where(Competence.name.ilike(f"%{competence_name}%"))
            .where(Worker.status == "active")
        )
        result = await db.execute(stmt)
        rows = result.all()
        if not rows:
            return f"No active workers found with competence '{competence_name}'."
        lines = [f"Workers with competence matching '{competence_name}':"]
        for w, c in rows:
            lines.append(f"  - {w.name} ({w.employee_id}, competence: {c.name})")
        return "\n".join(lines)


@mcp_server.tool()
async def analyze_down_events(severity: str = None, status: str = None) -> str:
    """Analyze down events, optionally filtered by severity or status.

    Args:
        severity: Filter by severity (low, medium, high, critical)
        status: Filter by status (active, resolved)
    """
    async with async_session_factory() as db:
        query = select(DownEvent)
        if severity:
            query = query.where(DownEvent.severity == severity)
        if status:
            query = query.where(DownEvent.status == status)
        query = query.order_by(DownEvent.started_at.desc()).limit(20)
        result = await db.execute(query)
        events = result.scalars().all()
        if not events:
            return "No down events found matching the criteria."
        total_downtime = sum(e.downtime_minutes for e in events)
        lines = [f"Found {len(events)} down events (total downtime: {total_downtime} min):"]
        for e in events:
            lines.append(
                f"  - Started: {e.started_at}, Duration: {e.downtime_minutes}min, "
                f"Severity: {e.severity}, Status: {e.status}"
            )
        return "\n".join(lines)


@mcp_server.tool()
async def get_task_details(task_id: str) -> str:
    """Get detailed information about a specific task including requirements.

    Args:
        task_id: The UUID of the task
    """
    from app.models.graph_associations import task_competence, task_material

    async with async_session_factory() as db:
        result = await db.execute(select(Task).where(Task.id == UUID(task_id)))
        task = result.scalar_one_or_none()
        if not task:
            return f"Task {task_id} not found."

        comp_stmt = (
            select(Competence.name)
            .join(task_competence, task_competence.c.competence_id == Competence.id)
            .where(task_competence.c.task_id == UUID(task_id))
        )
        comp_result = await db.execute(comp_stmt)
        competences = [r[0] for r in comp_result.all()]

        mat_stmt = (
            select(Material.name)
            .join(task_material, task_material.c.material_id == Material.id)
            .where(task_material.c.task_id == UUID(task_id))
        )
        mat_result = await db.execute(mat_stmt)
        materials = [r[0] for r in mat_result.all()]

        return (
            f"Task: {task.name}\n"
            f"Type: {task.task_type}\n"
            f"Status: {task.status}\n"
            f"Description: {task.description}\n"
            f"Estimated Duration: {task.estimated_duration_hours}h\n"
            f"Required Competences: {', '.join(competences) or 'None'}\n"
            f"Required Materials: {', '.join(materials) or 'None'}"
        )


@mcp_server.tool()
async def track_orders(status: str = None, priority: str = None) -> str:
    """Track work orders, optionally filtered by status or priority.

    Args:
        status: Filter by status (open, in_progress, completed, cancelled)
        priority: Filter by priority (low, medium, high, critical)
    """
    async with async_session_factory() as db:
        query = select(Order)
        if status:
            query = query.where(Order.status == status)
        if priority:
            query = query.where(Order.priority == priority)
        query = query.order_by(Order.priority.desc()).limit(20)
        result = await db.execute(query)
        orders = result.scalars().all()
        if not orders:
            return "No orders found matching the criteria."
        lines = [f"Found {len(orders)} orders:"]
        for o in orders:
            lines.append(
                f"  - {o.order_number}: {o.title} "
                f"(type={o.order_type}, status={o.status}, priority={o.priority})"
            )
        return "\n".join(lines)


@mcp_server.tool()
async def get_cause_chain(cause_name: str) -> str:
    """Get information about a cause and the roles/tasks needed to resolve it.

    Args:
        cause_name: Name of the cause to search for (partial match)
    """
    from app.models.graph_associations import cause_role

    async with async_session_factory() as db:
        cause_stmt = select(Cause).where(Cause.name.ilike(f"%{cause_name}%"))
        cause_result = await db.execute(cause_stmt)
        causes = cause_result.scalars().all()
        if not causes:
            return f"No causes found matching '{cause_name}'."

        lines = []
        for cause in causes:
            lines.append(
                f"Cause: {cause.name} "
                f"(severity={cause.severity}, category={cause.category})"
            )
            role_stmt = (
                select(Role.name)
                .join(cause_role, cause_role.c.role_id == Role.id)
                .where(cause_role.c.cause_id == cause.id)
            )
            role_result = await db.execute(role_stmt)
            roles = [r[0] for r in role_result.all()]
            if roles:
                lines.append(f"  Required roles: {', '.join(roles)}")
            else:
                lines.append("  No required roles defined.")
        return "\n".join(lines)


@mcp_server.tool()
async def get_material_planning(material_name: str = None) -> str:
    """Get material planning information including stock levels and planned tasks.

    Args:
        material_name: Filter by material name (partial match)
    """
    from app.models.graph_associations import task_material

    async with async_session_factory() as db:
        query = select(Material)
        if material_name:
            query = query.where(Material.name.ilike(f"%{material_name}%"))
        result = await db.execute(query.limit(20))
        materials = result.scalars().all()
        if not materials:
            return "No materials found matching the criteria."

        lines = [f"Found {len(materials)} materials:"]
        for m in materials:
            task_stmt = (
                select(Task.name)
                .join(task_material, task_material.c.task_id == Task.id)
                .where(task_material.c.material_id == m.id)
            )
            task_result = await db.execute(task_stmt)
            tasks = [r[0] for r in task_result.all()]
            tasks_str = ", ".join(tasks) if tasks else "None"
            lines.append(
                f"  - {m.name} (part={m.part_number}, stock={m.quantity_in_stock} {m.unit or ''}, "
                f"planned_for: {tasks_str})"
            )
        return "\n".join(lines)

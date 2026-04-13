from typing import Optional

# Predefined Cypher query templates keyed by query_type.
# Each template function takes extracted entities and returns (cypher, params).

TEMPLATES = {}


def register(query_type: str):
    def decorator(fn):
        TEMPLATES[query_type] = fn
        return fn
    return decorator


@register("asset_tree")
def asset_tree(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "MATCH (root:Asset) WHERE root.name CONTAINS $name "
            "MATCH (root)<-[:HAS_PARENT*0..]-(descendant:Asset) "
            "RETURN root, descendant",
            params,
        )
    if entities.get("asset_types"):
        params["asset_type"] = entities["asset_types"][0]
        return (
            "MATCH (root:Asset {asset_type: $asset_type}) "
            "MATCH (root)<-[:HAS_PARENT*0..]-(descendant:Asset) "
            "RETURN root, descendant",
            params,
        )
    return (
        "MATCH (root:Asset) "
        "MATCH (root)<-[:HAS_PARENT*0..]-(descendant:Asset) "
        "RETURN root, descendant LIMIT 50",
        params,
    )


@register("fault_chain")
def fault_chain(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("fault_codes"):
        params["code"] = entities["fault_codes"][0]
        return (
            "MATCH path = (root:Fault {code: $code})-[:CAUSES*1..5]->(downstream:Fault) "
            "RETURN path, root, downstream",
            params,
        )
    if entities.get("fault_severities"):
        params["severity"] = entities["fault_severities"][0]
        return (
            "MATCH (f:Fault {severity: $severity}) "
            "OPTIONAL MATCH path = (f)-[:CAUSES*1..5]->(downstream:Fault) "
            "RETURN f, path, downstream",
            params,
        )
    return (
        "MATCH (f:Fault) WHERE f.status IN ['open', 'investigating'] "
        "OPTIONAL MATCH path = (f)-[:CAUSES*1..5]->(downstream:Fault) "
        "RETURN f, path, downstream LIMIT 50",
        params,
    )


@register("sensor_status")
def sensor_status(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "MATCH (a:Asset)-[:HAS_SENSOR]->(s:Sensor)"
            "-[:HAS_SUMMARY]->(sum:SensorSummary) "
            "WHERE a.name CONTAINS $name "
            "RETURN a.name AS asset, s.name AS sensor, "
            "s.sensor_type AS type, "
            "sum.window, sum.avg_value, sum.min_value, "
            "sum.max_value, sum.stddev, sum.sample_count, "
            "sum.anomaly_flag "
            "ORDER BY s.name, sum.window",
            params,
        )
    if entities.get("sensor_types"):
        params["sensor_type"] = entities["sensor_types"][0]
        return (
            "MATCH (s:Sensor {sensor_type: $sensor_type})"
            "-[:HAS_SUMMARY]->(sum:SensorSummary) "
            "RETURN s.name AS sensor, s.sensor_type AS type, "
            "sum.window, sum.avg_value, sum.min_value, "
            "sum.max_value, sum.stddev, sum.sample_count, "
            "sum.anomaly_flag "
            "ORDER BY s.name, sum.window",
            params,
        )
    return (
        "MATCH (s:Sensor)-[:HAS_SUMMARY]->(sum:SensorSummary) "
        "WHERE sum.anomaly_flag = true "
        "RETURN s.name AS sensor, s.sensor_type AS type, "
        "sum.window, sum.avg_value, sum.min_value, "
        "sum.max_value, sum.stddev, sum.sample_count, "
        "sum.anomaly_flag "
        "ORDER BY s.name LIMIT 50",
        params,
    )


@register("maintenance_schedule")
def maintenance_schedule(entities: dict) -> tuple[str, dict]:
    params = {}
    conditions = []
    if entities.get("maintenance_statuses"):
        params["status"] = entities["maintenance_statuses"][0]
        conditions.append("m.status = $status")
    if entities.get("maintenance_types"):
        params["mtype"] = entities["maintenance_types"][0]
        conditions.append("m.maintenance_type = $mtype")
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        conditions.append("a.name CONTAINS $name")

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions) + " "

    return (
        f"MATCH (a:Asset)-[:HAS_MAINTENANCE]->(m:MaintenanceSchedule) "
        f"{where}"
        f"RETURN a.name AS asset, m.title, m.maintenance_type, m.status, "
        f"m.priority, m.scheduled_date, m.assigned_to "
        f"ORDER BY m.scheduled_date LIMIT 50",
        params,
    )


@register("relationship")
def relationship(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "MATCH (a:Asset) WHERE a.name CONTAINS $name "
            "OPTIONAL MATCH (a)-[:HAS_SENSOR]->(s:Sensor) "
            "OPTIONAL MATCH (a)-[:HAS_FAULT]->(f:Fault) "
            "WHERE f.status IN ['open','investigating'] "
            "OPTIONAL MATCH (a)-[:HAS_MAINTENANCE]"
            "->(m:MaintenanceSchedule) "
            "RETURN a, collect(DISTINCT s) AS sensors, "
            "collect(DISTINCT f) AS faults, "
            "collect(DISTINCT m) AS maintenance",
            params,
        )
    return (
        "MATCH (a:Asset)-[r]->(target) "
        "RETURN a.name, type(r) AS rel_type, labels(target) AS target_labels, "
        "properties(target) AS target_props LIMIT 50",
        params,
    )


@register("statistics")
def statistics(entities: dict) -> tuple[str, dict]:
    params = {}
    return (
        "MATCH (a:Asset) "
        "OPTIONAL MATCH (a)-[:HAS_FAULT]->(f:Fault) "
        "WHERE f.status IN ['open','investigating'] "
        "OPTIONAL MATCH (a)-[:HAS_MAINTENANCE]"
        "->(m:MaintenanceSchedule) "
        "WHERE m.status = 'overdue' "
        "RETURN a.name AS asset, a.status, a.asset_type, "
        "count(DISTINCT f) AS open_faults, "
        "count(DISTINCT m) AS overdue_count "
        "ORDER BY open_faults DESC LIMIT 50",
        params,
    )


@register("search")
def search(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "CALL db.index.fulltext.queryNodes("
            "'asset_name_search', $name) "
            "YIELD node, score "
            "RETURN labels(node) AS labels, "
            "properties(node) AS props, score "
            "LIMIT 10",
            params,
        )
    if entities.get("fault_codes"):
        params["code"] = entities["fault_codes"][0]
        return (
            "MATCH (f:Fault) WHERE f.code CONTAINS $code "
            "RETURN f LIMIT 10",
            params,
        )
    return (
        "MATCH (n) RETURN labels(n) AS labels, "
        "properties(n) AS props LIMIT 20",
        params,
    )


@register("worker_competences")
def worker_competences(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("worker_names"):
        params["name"] = entities["worker_names"][0]
        return (
            "MATCH (w:Worker) WHERE w.name CONTAINS $name "
            "OPTIONAL MATCH (w)-[:has]->(c:Competence) "
            "OPTIONAL MATCH (c)-[:typeOf]->(l:Level) "
            "RETURN w.name AS worker, c.name AS competence, "
            "c.category AS category, l.name AS level, l.rank AS rank",
            params,
        )
    return (
        "MATCH (w:Worker)-[:has]->(c:Competence)-[:typeOf]->(l:Level) "
        "RETURN w.name AS worker, c.name AS competence, "
        "c.category AS category, l.name AS level, l.rank AS rank "
        "LIMIT 50",
        params,
    )


@register("equipment_workers")
def equipment_workers(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "MATCH (a:Asset)-[:assigned_to]->(w:Worker) "
            "WHERE a.name CONTAINS $name "
            "OPTIONAL MATCH (w)-[:works_in]->(s:Shift) "
            "RETURN a.name AS asset, w.name AS worker, "
            "w.employee_id AS employee_id, w.status AS worker_status, "
            "s.name AS shift, s.start_time AS shift_start, s.end_time AS shift_end",
            params,
        )
    return (
        "MATCH (a:Asset)-[:assigned_to]->(w:Worker) "
        "OPTIONAL MATCH (w)-[:works_in]->(s:Shift) "
        "RETURN a.name AS asset, w.name AS worker, "
        "w.employee_id AS employee_id, w.status AS worker_status, "
        "s.name AS shift LIMIT 50",
        params,
    )


@register("task_requirements")
def task_requirements(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("task_names"):
        params["name"] = entities["task_names"][0]
        return (
            "MATCH (t:Task) WHERE t.name CONTAINS $name "
            "OPTIONAL MATCH (t)-[:requires]->(c:Competence) "
            "OPTIONAL MATCH (r:Role)-[:enables]->(t) "
            "OPTIONAL MATCH (m:Material)-[:planned_in]->(t) "
            "RETURN t.name AS task, t.task_type AS type, t.status AS status, "
            "collect(DISTINCT c.name) AS competences, "
            "collect(DISTINCT r.name) AS roles, "
            "collect(DISTINCT m.name) AS materials",
            params,
        )
    return (
        "MATCH (t:Task) "
        "OPTIONAL MATCH (t)-[:requires]->(c:Competence) "
        "OPTIONAL MATCH (r:Role)-[:enables]->(t) "
        "RETURN t.name AS task, t.task_type AS type, t.status AS status, "
        "collect(DISTINCT c.name) AS competences, "
        "collect(DISTINCT r.name) AS roles LIMIT 50",
        params,
    )


@register("down_event_analysis")
def down_event_analysis(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "MATCH (a:Asset) WHERE a.name CONTAINS $name "
            "OPTIONAL MATCH (de:DownEvent) WHERE de.asset_id = a.pg_id "
            "OPTIONAL MATCH (de)-[:has]->(c:Cause)-[:requires]->(r:Role) "
            "RETURN a.name AS asset, de.started_at AS started, "
            "de.downtime_minutes AS downtime, c.name AS cause, "
            "c.severity AS severity, r.name AS required_role "
            "ORDER BY de.started_at DESC LIMIT 20",
            params,
        )
    return (
        "MATCH (de:DownEvent)-[:has]->(c:Cause)-[:requires]->(r:Role) "
        "RETURN de.started_at AS started, de.downtime_minutes AS downtime, "
        "de.severity AS severity, c.name AS cause, r.name AS required_role "
        "ORDER BY de.started_at DESC LIMIT 50",
        params,
    )


@register("equipment_hierarchy")
def equipment_hierarchy(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("asset_names"):
        params["name"] = entities["asset_names"][0]
        return (
            "MATCH (a:Asset) WHERE a.name CONTAINS $name "
            "OPTIONAL MATCH (a)-[:consists_of]->(s:System) "
            "OPTIONAL MATCH (s)-[:part_of]->(ag:Aggregate) "
            "OPTIONAL MATCH (a)-[:is_at]->(l:Location) "
            "RETURN a.name AS asset, a.status AS status, "
            "collect(DISTINCT s.name) AS systems, "
            "collect(DISTINCT ag.name) AS aggregates, "
            "collect(DISTINCT l.name) AS locations",
            params,
        )
    return (
        "MATCH (a:Asset) "
        "OPTIONAL MATCH (a)-[:consists_of]->(s:System)-[:part_of]->(ag:Aggregate) "
        "OPTIONAL MATCH (a)-[:is_at]->(l:Location) "
        "RETURN a.name AS asset, a.status AS status, "
        "collect(DISTINCT s.name) AS systems, "
        "collect(DISTINCT l.name) AS locations "
        "LIMIT 50",
        params,
    )


@register("worker_availability")
def worker_availability(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("competence_names"):
        params["comp"] = entities["competence_names"][0]
        return (
            "MATCH (w:Worker)-[:has]->(c:Competence) "
            "WHERE c.name CONTAINS $comp AND w.status = 'active' "
            "OPTIONAL MATCH (w)-[:works_in]->(s:Shift) "
            "RETURN w.name AS worker, w.employee_id AS employee_id, "
            "c.name AS competence, s.name AS shift "
            "ORDER BY w.name",
            params,
        )
    return (
        "MATCH (w:Worker {status: 'active'})-[:has]->(c:Competence) "
        "OPTIONAL MATCH (w)-[:works_in]->(s:Shift) "
        "RETURN w.name AS worker, w.employee_id AS employee_id, "
        "collect(DISTINCT c.name) AS competences, s.name AS shift "
        "ORDER BY w.name LIMIT 50",
        params,
    )


@register("cause_analysis")
def cause_analysis(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("cause_names"):
        params["name"] = entities["cause_names"][0]
        return (
            "MATCH (c:Cause) WHERE c.name CONTAINS $name "
            "OPTIONAL MATCH (c)-[:requires]->(r:Role)-[:enables]->(t:Task) "
            "RETURN c.name AS cause, c.category AS category, c.severity AS severity, "
            "collect(DISTINCT r.name) AS required_roles, "
            "collect(DISTINCT t.name) AS enabled_tasks",
            params,
        )
    return (
        "MATCH (c:Cause) "
        "OPTIONAL MATCH (c)-[:requires]->(r:Role)-[:enables]->(t:Task) "
        "RETURN c.name AS cause, c.category AS category, c.severity AS severity, "
        "collect(DISTINCT r.name) AS required_roles, "
        "collect(DISTINCT t.name) AS enabled_tasks LIMIT 50",
        params,
    )


@register("order_tracking")
def order_tracking(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("order_numbers"):
        params["num"] = entities["order_numbers"][0]
        return (
            "MATCH (o:Order) WHERE o.order_number CONTAINS $num "
            "OPTIONAL MATCH (o)-[:booked_on]->(a:Asset) "
            "RETURN o.order_number AS order_num, o.title AS title, "
            "o.status AS status, o.priority AS priority, "
            "o.order_type AS type, collect(DISTINCT a.name) AS assets",
            params,
        )
    conditions = []
    if entities.get("order_statuses"):
        params["status"] = entities["order_statuses"][0]
        conditions.append("o.status = $status")
    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions) + " "
    return (
        f"MATCH (o:Order) {where}"
        "OPTIONAL MATCH (o)-[:booked_on]->(a:Asset) "
        "RETURN o.order_number AS order_num, o.title AS title, "
        "o.status AS status, o.priority AS priority, "
        "collect(DISTINCT a.name) AS assets "
        "ORDER BY o.priority DESC LIMIT 50",
        params,
    )


@register("material_planning")
def material_planning(entities: dict) -> tuple[str, dict]:
    params = {}
    if entities.get("material_names"):
        params["name"] = entities["material_names"][0]
        return (
            "MATCH (m:Material) WHERE m.name CONTAINS $name "
            "OPTIONAL MATCH (m)-[:planned_in]->(t:Task) "
            "RETURN m.name AS material, m.part_number AS part_number, "
            "m.quantity_in_stock AS in_stock, m.unit AS unit, "
            "collect(DISTINCT t.name) AS planned_tasks",
            params,
        )
    return (
        "MATCH (m:Material) "
        "OPTIONAL MATCH (m)-[:planned_in]->(t:Task) "
        "RETURN m.name AS material, m.part_number AS part_number, "
        "m.quantity_in_stock AS in_stock, m.unit AS unit, "
        "collect(DISTINCT t.name) AS planned_tasks "
        "LIMIT 50",
        params,
    )


def get_template(query_type: str) -> Optional[callable]:
    return TEMPLATES.get(query_type)

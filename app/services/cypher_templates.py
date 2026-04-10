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


def get_template(query_type: str) -> Optional[callable]:
    return TEMPLATES.get(query_type)

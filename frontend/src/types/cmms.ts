// ── Workers ──────────────────────────────────────────────
export type WorkerStatus = "active" | "inactive" | "on_leave";

export interface Worker {
  id: string;
  name: string;
  employee_id: string;
  email: string | null;
  phone: string | null;
  status: WorkerStatus;
  level_id: string | null;
  level_name: string | null;
  role_id: string | null;
  role_name: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkerCreate {
  name: string;
  employee_id: string;
  email?: string;
  phone?: string;
  status?: WorkerStatus;
  level_id?: string;
}

export interface WorkerUpdate {
  name?: string;
  employee_id?: string;
  email?: string;
  phone?: string;
  status?: WorkerStatus;
  level_id?: string;
}

// ── Roles ───────────────────────────────────────────────
export interface LevelBrief {
  id: string;
  name: string;
  rank: number;
  description: string | null;
}

export interface Role {
  id: string;
  name: string;
  description: string | null;
  levels: LevelBrief[] | null;
  level_count: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface RoleCreate {
  name: string;
  description?: string;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
}

// ── Competences ─────────────────────────────────────────
export interface Competence {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CompetenceCreate {
  name: string;
  description?: string;
  category?: string;
}

export interface CompetenceUpdate {
  name?: string;
  description?: string;
  category?: string;
}

// ── Levels ──────────────────────────────────────────────
export interface Level {
  id: string;
  name: string;
  rank: number;
  description: string | null;
  role_id: string | null;
  role_name: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LevelCreate {
  name: string;
  rank: number;
  description?: string;
  role_id?: string;
}

export interface LevelUpdate {
  name?: string;
  rank?: number;
  description?: string;
  role_id?: string;
}

// ── Tasks ───────────────────────────────────────────────
export type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";
export type TaskType = "general" | "inspection" | "repair" | "installation" | "calibration";

export interface Task {
  id: string;
  name: string;
  description: string | null;
  task_type: TaskType;
  status: TaskStatus;
  estimated_duration_hours: number | null;
  doc_link: string | null;
  maintenance_schedule_id: string;
  shift_id: string | null;
  assigned_to: string | null;
  action_type: string;
  sequence_order: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskCreate {
  name: string;
  description?: string;
  task_type: TaskType;
  status?: TaskStatus;
  estimated_duration_hours?: number;
  doc_link?: string;
  maintenance_schedule_id: string;
  shift_id?: string;
  assigned_to?: string;
  action_type?: string;
  sequence_order?: number;
}

export interface TaskUpdate {
  name?: string;
  description?: string;
  task_type?: TaskType;
  status?: TaskStatus;
  estimated_duration_hours?: number;
  doc_link?: string;
  maintenance_schedule_id?: string;
  shift_id?: string;
  assigned_to?: string;
  action_type?: string;
  sequence_order?: number;
}

export interface TaskCompetenceAdd {
  competence_id: string;
  level_id: string;
}

export interface TaskMaterialAdd {
  material_id: string;
  quantity: number;
}

// ── Causes ──────────────────────────────────────────────
export type CauseSeverity = "low" | "medium" | "high" | "critical";

export interface Cause {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  severity: CauseSeverity | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CauseCreate {
  name: string;
  description?: string;
  category?: string;
  severity?: CauseSeverity;
}

export interface CauseUpdate {
  name?: string;
  description?: string;
  category?: string;
  severity?: CauseSeverity;
}

// ── Materials ───────────────────────────────────────────
export interface Material {
  id: string;
  name: string;
  part_number: string | null;
  description: string | null;
  quantity_in_stock: number | null;
  unit: string | null;
  order_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MaterialCreate {
  name: string;
  part_number?: string;
  description?: string;
  quantity_in_stock?: number;
  unit?: string;
  order_id?: string;
}

export interface MaterialUpdate {
  name?: string;
  part_number?: string;
  description?: string;
  quantity_in_stock?: number;
  unit?: string;
  order_id?: string;
}

// ── Shifts ──────────────────────────────────────────────
export interface Shift {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ShiftCreate {
  name: string;
  start_time?: string;
  end_time?: string;
  description?: string;
}

export interface ShiftUpdate {
  name?: string;
  start_time?: string;
  end_time?: string;
  description?: string;
}

// ── Down Events ─────────────────────────────────────────
export type DownEventSeverity = "low" | "medium" | "high" | "critical";
export type DownEventStatus = "active" | "resolved";

export interface DownEvent {
  id: string;
  asset_id: string | null;
  fault_id: string;
  fault_name: string | null;
  maintenance_schedule_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  downtime_minutes: number | null;
  severity: DownEventSeverity | null;
  status: DownEventStatus | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DownEventCreate {
  asset_id?: string;
  fault_id: string;
  maintenance_schedule_id?: string;
  downtime_minutes?: number;
  severity?: DownEventSeverity;
  status?: DownEventStatus;
}

export interface DownEventUpdate {
  asset_id?: string;
  fault_id?: string;
  maintenance_schedule_id?: string;
  downtime_minutes?: number;
  severity?: DownEventSeverity;
  status?: DownEventStatus;
}

export interface DownEventStatistics {
  total_events: number;
  active_events: number;
  resolved_events: number;
  total_downtime_minutes: number;
  by_severity: Record<string, number>;
}

// ── Orders ──────────────────────────────────────────────
export type OrderStatus = "open" | "in_progress" | "completed" | "cancelled";
export type OrderPriority = "low" | "medium" | "high" | "critical";
export type OrderType = "maintenance" | "repair" | "inspection" | "installation";

export interface Order {
  id: string;
  order_number: string | null;
  title: string;
  description: string | null;
  order_type: OrderType | null;
  status: OrderStatus | null;
  priority: OrderPriority | null;
  requested_date: string | null;
  maintenance_schedule_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface OrderCreate {
  order_number?: string;
  title: string;
  description?: string;
  order_type?: OrderType;
  status?: OrderStatus;
  priority?: OrderPriority;
  requested_date?: string;
  maintenance_schedule_id?: string;
}

export interface OrderUpdate {
  order_number?: string;
  title?: string;
  description?: string;
  order_type?: OrderType;
  status?: OrderStatus;
  priority?: OrderPriority;
  requested_date?: string;
  maintenance_schedule_id?: string;
}

// ── Locations ───────────────────────────────────────────
export interface Location {
  id: string;
  name: string;
  description: string | null;
  location_type: string | null;
  parent_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LocationCreate {
  name: string;
  description?: string;
  location_type?: string;
  parent_id?: string;
}

export interface LocationUpdate {
  name?: string;
  description?: string;
  location_type?: string;
  parent_id?: string;
}

export interface LocationTreeNode {
  id: string;
  name: string;
  location_type: string | null;
  children: LocationTreeNode[];
}

// ── Systems ─────────────────────────────────────────────
export interface System {
  id: string;
  name: string;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SystemCreate {
  name: string;
  description?: string;
}

export interface SystemUpdate {
  name?: string;
  description?: string;
}

// ── Aggregates ──────────────────────────────────────────
export interface Aggregate {
  id: string;
  name: string;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AggregateCreate {
  name: string;
  description?: string;
}

export interface AggregateUpdate {
  name?: string;
  description?: string;
}

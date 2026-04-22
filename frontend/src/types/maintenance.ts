export type MaintenanceType = "preventive" | "corrective" | "predictive";
export type MaintenanceStatus = "scheduled" | "in_progress" | "completed" | "cancelled" | "overdue";
export type MaintenancePriority = "low" | "medium" | "high" | "critical";
export type MaintenanceRecurrence = "none" | "daily" | "weekly" | "monthly" | "quarterly" | "yearly";

export interface MaintenanceSchedule {
  id: string;
  asset_id: string;
  title: string;
  description: string | null;
  maintenance_type: MaintenanceType;
  status: MaintenanceStatus;
  priority: MaintenancePriority;
  scheduled_date: string | null;
  completed_date: string | null;
  recurrence: MaintenanceRecurrence;
  estimated_duration_hours: number | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MaintenanceScheduleDetail extends MaintenanceSchedule {
  asset: {
    id: string;
    name: string;
    description: string | null;
    asset_type: string;
    parent_id: string | null;
    status: string;
    location: string | null;
  } | null;
  down_events: {
    id: string;
    asset_id: string | null;
    fault_id: string;
    fault_name: string | null;
    maintenance_schedule_id: string | null;
    started_at: string | null;
    ended_at: string | null;
    downtime_minutes: number | null;
    severity: string | null;
    status: string | null;
  }[];
  order: {
    id: string;
    order_number: string | null;
    description: string | null;
    status: string | null;
    priority: string | null;
  } | null;
  tasks: {
    id: string;
    title: string;
    description: string | null;
    status: string | null;
    priority: string | null;
  }[];
}

export interface ScheduleCreate {
  title: string;
  description?: string;
  maintenance_type?: MaintenanceType;
  priority?: MaintenancePriority;
  scheduled_date: string;
  recurrence?: MaintenanceRecurrence;
  estimated_duration_hours?: number;
  notes?: string;
}

export interface ScheduleUpdate {
  title?: string;
  description?: string;
  maintenance_type?: MaintenanceType;
  status?: MaintenanceStatus;
  priority?: MaintenancePriority;
  scheduled_date?: string;
  recurrence?: MaintenanceRecurrence;
  estimated_duration_hours?: number;
  notes?: string;
}

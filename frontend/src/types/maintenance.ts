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

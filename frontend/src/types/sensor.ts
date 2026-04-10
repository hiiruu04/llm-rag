export type SensorStatus = "active" | "inactive" | "faulty";

export interface Sensor {
  id: string;
  asset_id: string;
  name: string;
  sensor_type: string;
  unit: string | null;
  status: SensorStatus;
  created_at: string | null;
  updated_at: string | null;
}

export interface SensorCreate {
  name: string;
  sensor_type: string;
  unit?: string;
  status?: SensorStatus;
}

export interface SensorUpdate {
  name?: string;
  sensor_type?: string;
  unit?: string;
  status?: SensorStatus;
}

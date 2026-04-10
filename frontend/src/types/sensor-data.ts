export interface SensorData {
  id: number;
  sensor_id: string;
  timestamp: string | null;
  value: number;
}

export interface SensorDataCreate {
  timestamp?: string;
  value: number;
}

export interface SensorDataBatchCreate {
  readings: SensorDataCreate[];
}

export interface BatchInsertResponse {
  count: number;
}

export interface DeletedCountResponse {
  deleted_count: number;
}

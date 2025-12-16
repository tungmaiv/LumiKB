/**
 * System configuration types.
 */

export type ConfigDataType = "integer" | "float" | "boolean" | "string";

export type ConfigCategory = "Security" | "Processing" | "Rate Limits";

export interface ConfigSetting {
  key: string;
  name: string;
  value: number | boolean | string;
  default_value: number | boolean | string;
  data_type: ConfigDataType;
  description: string;
  category: ConfigCategory;
  min_value?: number;
  max_value?: number;
  requires_restart: boolean;
  last_modified: string | null;
  last_modified_by: string | null;
}

export interface ConfigUpdateRequest {
  value: number | boolean | string;
}

export interface ConfigUpdateResponse {
  setting: ConfigSetting;
  restart_required: string[]; // List of setting keys requiring restart
}

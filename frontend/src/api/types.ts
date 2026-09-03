export type Role = "patient" | "clinician" | "chw" | "pharmacist" | "admin";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  phone: string;
  clinic: number | null;
  clinic_name: string | null;
  patient_profile?: {
    allergies: string[];
    insurance_provider: string;
    insurance_member_id: string;
    medication_history: string[];
    address: string;
  } | null;
}

export interface Slot {
  id: number;
  provider: number;
  provider_name: string;
  clinic: number;
  clinic_name: string;
  start: string;
  end: string;
  is_booked: boolean;
}

export interface Triage {
  acuity: string;
  priority_level: number;
  recommendation: string;
  matched_terms: string[];
  model: string;
}

export interface Appointment {
  id: number;
  patient: number;
  patient_name: string;
  provider: number | null;
  provider_name: string | null;
  clinic_name: string | null;
  scheduled_start: string;
  mode: string;
  status: string;
  symptom_note: string;
  intake: Record<string, unknown>;
  triage: Triage;
  wait_seconds: number | null;
}

export interface JoinInfo {
  provider: "webrtc" | "managed";
  room: string;
  mode: string;
  iceServers?: RTCIceServer[];
  signalUrl?: string;
  role?: "provider" | "patient";
  polite?: boolean;
  vendor?: string;
  roomName?: string;
  token?: string;
  live?: boolean;
}

export interface Consultation {
  id: number;
  appointment: number;
  patient_name: string;
  provider_name: string | null;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  note_finalised: boolean;
}

export interface Medication {
  id: number;
  name: string;
  form: string;
  strength: string;
  drug_class: string;
  allergen_groups: string[];
  label: string;
}

export interface SafetyAlert {
  type: "allergy" | "interaction";
  severity: string;
  medication: string;
  against: string;
  detail: string;
}

export interface SafetyReport {
  blocking: boolean;
  alerts: SafetyAlert[];
  checked_medications: string[];
  patient_allergies: string[];
}

export interface Prescription {
  id: number;
  consultation: number;
  patient_name: string;
  prescriber_name: string | null;
  pharmacy_name: string | null;
  status: string;
  fulfilment: string;
  allergen_alert_triggered: boolean;
  safety_report: SafetyReport | Record<string, never>;
  override_reason: string;
  medication_list: string[];
  items: {
    id: number;
    medication: number;
    medication_detail: Medication;
    dose: string;
    frequency: string;
    duration: string;
  }[];
  sent_to_pharmacy_at: string | null;
  ready_at: string | null;
  dispensed_at: string | null;
}

export interface Metrics {
  generated_at: string;
  note: string;
  funnel: {
    bookings: number;
    completed_visits: number;
    prescriptions_issued: number;
    prescriptions_filled: number;
    conversion: Record<string, number>;
  };
  speed: Record<string, number>;
  unit_economics: Record<string, number>;
  retention: Record<string, number>;
  market_wedge: string;
}

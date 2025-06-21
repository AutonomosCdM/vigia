export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: 'M' | 'F';
  roomNumber?: string;
  admissionDate: string;
  lastAssessment?: string;
  riskLevel: 'low' | 'medium' | 'high';
  lppDetections: LPPDetection[];
  vitals?: {
    bloodPressure: string;
    heartRate: number;
    temperature: number;
    oxygenSaturation: number;
  };
}

export interface LPPDetection {
  id: string;
  patientId: string;
  imageUrl: string;
  grade: 0 | 1 | 2 | 3 | 4;
  confidence: number;
  anatomicalLocation: string;
  detectedAt: string;
  recommendations: string[];
  status: 'new' | 'reviewing' | 'treated';
}

export interface DashboardStats {
  totalPatients: number;
  activePatients: number;
  lppDetected: number;
  riskAlerts: number;
  todaysScans: number;
}
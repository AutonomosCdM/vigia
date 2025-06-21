import { create } from 'zustand';
import { Patient, LPPDetection, DashboardStats } from '@/types/patient';

interface PatientStore {
  patients: Patient[];
  selectedPatient: Patient | null;
  dashboardStats: DashboardStats;
  isLoading: boolean;
  setSelectedPatient: (patient: Patient | null) => void;
  addPatient: (patient: Patient) => void;
  updatePatient: (id: string, updates: Partial<Patient>) => void;
  addLPPDetection: (detection: LPPDetection) => void;
  setLoading: (loading: boolean) => void;
  updateDashboardStats: () => void;
}

// Mock data for demo
const mockPatients: Patient[] = [
  {
    id: '1',
    name: 'María García',
    age: 75,
    gender: 'F',
    roomNumber: '305',
    admissionDate: '2024-06-15',
    lastAssessment: '2024-06-20T10:30:00Z',
    riskLevel: 'high',
    lppDetections: [
      {
        id: 'lpp1',
        patientId: '1',
        imageUrl: '/mock-wound-1.jpg',
        grade: 2,
        confidence: 0.94,
        anatomicalLocation: 'Sacrum',
        detectedAt: '2024-06-20T10:30:00Z',
        recommendations: [
          'Immediate pressure relief',
          'Wound care specialist consultation',
          'Nutritional assessment'
        ],
        status: 'new'
      }
    ],
    vitals: {
      bloodPressure: '132/87 mmHg',
      heartRate: 82,
      temperature: 100.4,
      oxygenSaturation: 96
    }
  },
  {
    id: '2',
    name: 'Juan López',
    age: 68,
    gender: 'M',
    roomNumber: '312',
    admissionDate: '2024-06-18',
    lastAssessment: '2024-06-20T09:15:00Z',
    riskLevel: 'medium',
    lppDetections: [
      {
        id: 'lpp2',
        patientId: '2',
        imageUrl: '/mock-wound-2.jpg',
        grade: 1,
        confidence: 0.87,
        anatomicalLocation: 'Heel',
        detectedAt: '2024-06-20T09:15:00Z',
        recommendations: [
          'Pressure redistribution',
          'Skin assessment every shift',
          'Heel elevation'
        ],
        status: 'reviewing'
      }
    ],
    vitals: {
      bloodPressure: '125/82 mmHg',
      heartRate: 76,
      temperature: 98.6,
      oxygenSaturation: 98
    }
  },
  {
    id: '3',
    name: 'Ana Rodríguez',
    age: 82,
    gender: 'F',
    roomNumber: '301',
    admissionDate: '2024-06-12',
    riskLevel: 'low',
    lppDetections: [],
    vitals: {
      bloodPressure: '118/75 mmHg',
      heartRate: 68,
      temperature: 98.2,
      oxygenSaturation: 99
    }
  }
];

export const usePatientStore = create<PatientStore>((set, get) => ({
  patients: mockPatients,
  selectedPatient: null,
  dashboardStats: {
    totalPatients: 0,
    activePatients: 0,
    lppDetected: 0,
    riskAlerts: 0,
    todaysScans: 0
  },
  isLoading: false,

  setSelectedPatient: (patient) => set({ selectedPatient: patient }),

  addPatient: (patient) => set((state) => ({
    patients: [...state.patients, patient]
  })),

  updatePatient: (id, updates) => set((state) => ({
    patients: state.patients.map(p => 
      p.id === id ? { ...p, ...updates } : p
    )
  })),

  addLPPDetection: (detection) => set((state) => ({
    patients: state.patients.map(p => 
      p.id === detection.patientId 
        ? { ...p, lppDetections: [...p.lppDetections, detection] }
        : p
    )
  })),

  setLoading: (loading) => set({ isLoading: loading }),

  updateDashboardStats: () => {
    const { patients } = get();
    const totalPatients = patients.length;
    const activePatients = patients.filter(p => p.lastAssessment).length;
    const lppDetected = patients.reduce((acc, p) => acc + p.lppDetections.length, 0);
    const riskAlerts = patients.filter(p => p.riskLevel === 'high').length;
    const todaysScans = patients.filter(p => {
      const today = new Date().toDateString();
      return p.lastAssessment && new Date(p.lastAssessment).toDateString() === today;
    }).length;

    set({
      dashboardStats: {
        totalPatients,
        activePatients,
        lppDetected,
        riskAlerts,
        todaysScans
      }
    });
  }
}));
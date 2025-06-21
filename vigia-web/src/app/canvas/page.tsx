"use client";

import { useState } from "react";
import { VIGIAMedicalCard, VitalSignMetric, MedicalGoal } from "@/components/ui/vigia-medical-card";

export default function MedicalCanvas() {
  const [selectedPatient, setSelectedPatient] = useState("maria-garcia");
  const [aiAssistantOpen, setAiAssistantOpen] = useState(true);

  const patients = [
    {
      id: "maria-garcia",
      name: "María García",
      age: 75,
      room: "305",
      risk: "High",
      lastScan: "2 hours ago",
      lppGrade: 2,
      confidence: 94,
      vitalSigns: [
        {
          label: "Heart Rate",
          value: "82",
          trend: 75,
          unit: "bpm" as const,
          normalRange: "60-100",
          status: "normal" as const
        },
        {
          label: "Blood Pressure", 
          value: "132/87",
          trend: 65,
          unit: "mmHg" as const,
          normalRange: "<120/80",
          status: "warning" as const
        },
        {
          label: "Temperature",
          value: "100.4",
          trend: 85,
          unit: "°C" as const,
          normalRange: "36.1-37.2",
          status: "warning" as const
        },
        {
          label: "O2 Saturation",
          value: "96",
          trend: 90,
          unit: "%" as const,
          normalRange: "95-100",
          status: "normal" as const
        }
      ] as VitalSignMetric[],
      medicalGoals: [
        {
          id: "goal-1",
          title: "Pressure relief protocol every 2 hours",
          isCompleted: false,
          priority: "high" as const
        },
        {
          id: "goal-2", 
          title: "Wound care specialist consultation",
          isCompleted: false,
          priority: "high" as const
        },
        {
          id: "goal-3",
          title: "Nutritional assessment",
          isCompleted: true,
          priority: "medium" as const
        },
        {
          id: "goal-4",
          title: "Daily skin assessment",
          isCompleted: false,
          priority: "medium" as const
        }
      ] as MedicalGoal[]
    },
    {
      id: "juan-lopez", 
      name: "Juan López",
      age: 68,
      room: "312",
      risk: "Medium",
      lastScan: "6 hours ago",
      lppGrade: 1,
      confidence: 87,
      vitalSigns: [
        {
          label: "Heart Rate",
          value: "76",
          trend: 80,
          unit: "bpm" as const,
          normalRange: "60-100",
          status: "normal" as const
        },
        {
          label: "Blood Pressure",
          value: "125/78",
          trend: 60,
          unit: "mmHg" as const,
          normalRange: "<120/80",
          status: "normal" as const
        },
        {
          label: "Temperature",
          value: "98.6",
          trend: 70,
          unit: "°C" as const,
          normalRange: "36.1-37.2",
          status: "normal" as const
        },
        {
          label: "O2 Saturation",
          value: "98",
          trend: 95,
          unit: "%" as const,
          normalRange: "95-100",
          status: "normal" as const
        }
      ] as VitalSignMetric[],
      medicalGoals: [
        {
          id: "goal-1",
          title: "Mobility improvement exercises",
          isCompleted: true,
          priority: "medium" as const
        },
        {
          id: "goal-2",
          title: "Pressure redistribution schedule",
          isCompleted: false,
          priority: "medium" as const
        }
      ] as MedicalGoal[]
    },
    {
      id: "ana-rodriguez",
      name: "Ana Rodríguez", 
      age: 82,
      room: "301",
      risk: "Low",
      lastScan: "1 day ago",
      lppGrade: 0,
      confidence: 98,
      vitalSigns: [
        {
          label: "Heart Rate",
          value: "74",
          trend: 78,
          unit: "bpm" as const,
          normalRange: "60-100",
          status: "normal" as const
        },
        {
          label: "Blood Pressure",
          value: "118/76",
          trend: 55,
          unit: "mmHg" as const,
          normalRange: "<120/80",
          status: "normal" as const
        },
        {
          label: "Temperature",
          value: "98.2",
          trend: 68,
          unit: "°C" as const,
          normalRange: "36.1-37.2",
          status: "normal" as const
        },
        {
          label: "O2 Saturation",
          value: "99",
          trend: 98,
          unit: "%" as const,
          normalRange: "95-100",
          status: "normal" as const
        }
      ] as VitalSignMetric[],
      medicalGoals: [
        {
          id: "goal-1",
          title: "Routine skin inspection",
          isCompleted: true,
          priority: "low" as const
        },
        {
          id: "goal-2",
          title: "Maintain current mobility",
          isCompleted: false,
          priority: "low" as const
        }
      ] as MedicalGoal[]
    }
  ];

  const currentPatient = patients.find(p => p.id === selectedPatient);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Patient Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-medium text-sm">V</span>
            </div>
            <h1 className="text-lg font-medium tracking-tight">VIGIA Canvas</h1>
          </div>
          <p className="text-sm text-gray-600 mt-1">AI-Powered Medical Collaboration</p>
        </div>

        <div className="p-4 border-b border-gray-200">
          <button className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            New Patient Analysis
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3 tracking-tight">Active Patients</h3>
          <div className="space-y-2">
            {patients.map((patient) => (
              <div 
                key={patient.id}
                onClick={() => setSelectedPatient(patient.id)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedPatient === patient.id 
                    ? 'bg-blue-50 border border-blue-200' 
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-sm tracking-tight">{patient.name}</p>
                    <p className="text-xs text-gray-600">{patient.age}y, Room {patient.room}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        patient.risk === 'High' ? 'bg-red-100 text-red-800' :
                        patient.risk === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {patient.risk} Risk
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {patient.lastScan}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-medium tracking-tight">{currentPatient?.name}</h2>
              <p className="text-sm text-gray-600">LPP Analysis Session • Room {currentPatient?.room}</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
                Share Session
              </button>
              <button 
                onClick={() => setAiAssistantOpen(!aiAssistantOpen)}
                className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                AI Assistant
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 flex gap-6">
          {/* Medical Card */}
          <div className="w-96">
            {currentPatient && (
              <VIGIAMedicalCard
                patientId={currentPatient.id.toUpperCase()}
                patientName={currentPatient.name}
                vitalSigns={currentPatient.vitalSigns}
                medicalGoals={currentPatient.medicalGoals}
                onAddGoal={() => console.log("Add goal clicked")}
                onToggleGoal={(goalId) => console.log("Toggle goal:", goalId)}
                onViewDetails={() => console.log("View details clicked")}
                className="h-full"
              />
            )}
          </div>

          {/* Canvas Content */}
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg border border-gray-200 h-full p-6">
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-4 tracking-tight">Current LPP Assessment</h3>
                
                {/* LPP Detection Result */}
                <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                      ⚠️
                    </div>
                    <div>
                      <h4 className="font-semibold text-red-900">Grade {currentPatient?.lppGrade} LPP Detected</h4>
                      <p className="text-red-700 text-sm mt-1">Sacrum region • {currentPatient?.confidence}% confidence</p>
                      <p className="text-red-600 text-sm mt-2">Requires immediate pressure relief and wound care specialist consultation</p>
                    </div>
                  </div>
                </div>

                {/* Medical Canvas Workspace */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <div className="max-w-md mx-auto">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2 tracking-tight">Medical Image Analysis</h3>
                    <p className="text-gray-600 mb-4">Upload patient images for AI-powered LPP detection and collaborative analysis</p>
                    
                    <button className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 mb-4">
                      Upload Medical Images
                    </button>
                    
                    <div className="text-sm text-gray-500">
                      Supports: JPG, PNG, DICOM • Max 10MB
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="mt-6 grid grid-cols-2 gap-4">
                  <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                        📊
                      </div>
                      <div>
                        <p className="font-medium text-sm tracking-tight">Generate Clinical Summary</p>
                        <p className="text-xs text-gray-600">AI-powered patient report</p>
                      </div>
                    </div>
                  </button>
                  
                  <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                        📅
                      </div>
                      <div>
                        <p className="font-medium text-sm tracking-tight">Schedule Follow-up</p>
                        <p className="text-xs text-gray-600">Plan next assessment</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* AI Assistant Sidebar */}
          {aiAssistantOpen && (
            <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium tracking-tight">AI Medical Assistant</h3>
                  <button 
                    onClick={() => setAiAssistantOpen(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div className="flex-1 p-4 overflow-y-auto">
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs font-bold">AI</span>
                      </div>
                      <div className="text-sm">
                        <p className="font-medium text-blue-900 mb-1">Clinical Insights</p>
                        <p className="text-blue-800">Based on the Grade 2 LPP detection, I recommend implementing immediate pressure redistribution protocols. The sacral location suggests prolonged immobility.</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs font-bold">📋</span>
                      </div>
                      <div className="text-sm">
                        <p className="font-medium text-yellow-900 mb-1">Treatment Protocol</p>
                        <p className="text-yellow-800">Consider specialized mattress, 2-hour turning schedule, and wound care specialist consultation within 24 hours.</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs font-bold">📊</span>
                      </div>
                      <div className="text-sm">
                        <p className="font-medium text-gray-900 mb-1">Patient History</p>
                        <p className="text-gray-800">Previous assessment 3 days ago showed Stage 1 progression. Current Grade 2 indicates advancement requiring immediate intervention.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 border-t border-gray-200">
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    placeholder="Ask AI about this patient..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
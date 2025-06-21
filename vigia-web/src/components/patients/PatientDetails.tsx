import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatientStore } from "@/store/patientStore";
import { Camera, Upload, Activity, Calendar, MapPin, Thermometer, Heart, Droplets } from "lucide-react";
import { useState } from "react";

export function PatientDetails() {
  const { selectedPatient } = usePatientStore();
  const [activeTab, setActiveTab] = useState("overview");

  if (!selectedPatient) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent>
          <div className="text-center">
            <p className="text-muted-foreground">Select a patient to view details</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const tabs = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "lpp", label: "LPP Analysis", icon: Camera },
    { id: "timeline", label: "Timeline", icon: Calendar }
  ];

  const getGradeColor = (grade: number) => {
    if (grade >= 3) return "text-red-600 bg-red-50";
    if (grade >= 2) return "text-orange-600 bg-orange-50";
    if (grade >= 1) return "text-yellow-600 bg-yellow-50";
    return "text-green-600 bg-green-50";
  };

  return (
    <div className="space-y-6">
      {/* Patient Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-gray-200 flex items-center justify-center">
                <span className="text-lg font-medium">
                  {selectedPatient.name.split(' ').map(n => n[0]).join('')}
                </span>
              </div>
              <div>
                <CardTitle>{selectedPatient.name}</CardTitle>
                <p className="text-muted-foreground">
                  {selectedPatient.age} years old • {selectedPatient.gender === 'M' ? 'Male' : 'Female'}
                </p>
                <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    Room {selectedPatient.roomNumber}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Admitted {new Date(selectedPatient.admissionDate).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
            <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              <Upload className="h-4 w-4" />
              Upload Image
            </button>
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <div className="flex space-x-1 border-b">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Vitals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Vital Signs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedPatient.vitals && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Droplets className="h-4 w-4 text-red-500" />
                      Blood Pressure
                    </span>
                    <span className="font-medium">{selectedPatient.vitals.bloodPressure}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Heart className="h-4 w-4 text-pink-500" />
                      Heart Rate
                    </span>
                    <span className="font-medium">{selectedPatient.vitals.heartRate} bpm</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Thermometer className="h-4 w-4 text-orange-500" />
                      Temperature
                    </span>
                    <span className="font-medium">{selectedPatient.vitals.temperature}°F</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-blue-500" />
                      O2 Saturation
                    </span>
                    <span className="font-medium">{selectedPatient.vitals.oxygenSaturation}%</span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Risk Assessment */}
          <Card>
            <CardHeader>
              <CardTitle>Risk Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span>LPP Risk Level</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      selectedPatient.riskLevel === 'high' ? 'bg-red-100 text-red-800' :
                      selectedPatient.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {selectedPatient.riskLevel.charAt(0).toUpperCase() + selectedPatient.riskLevel.slice(1)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        selectedPatient.riskLevel === 'high' ? 'bg-red-500 w-5/6' :
                        selectedPatient.riskLevel === 'medium' ? 'bg-yellow-500 w-1/2' :
                        'bg-green-500 w-1/4'
                      }`}
                    />
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  <p>Risk factors: Immobility, advanced age, existing pressure injuries</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === "lpp" && (
        <div className="space-y-6">
          {selectedPatient.lppDetections.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-muted-foreground">No LPP detections yet</p>
                <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                  Upload First Image
                </button>
              </CardContent>
            </Card>
          ) : (
            selectedPatient.lppDetections.map((detection) => (
              <Card key={detection.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>LPP Detection - {detection.anatomicalLocation}</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getGradeColor(detection.grade)}`}>
                      Grade {detection.grade}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-2">Analysis Results</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Confidence:</span>
                          <span className="font-medium">{Math.round(detection.confidence * 100)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Location:</span>
                          <span className="font-medium">{detection.anatomicalLocation}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Detected:</span>
                          <span className="font-medium">{new Date(detection.detectedAt).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            detection.status === 'new' ? 'bg-blue-100 text-blue-800' :
                            detection.status === 'reviewing' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {detection.status}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Recommendations</h4>
                      <ul className="space-y-1 text-sm">
                        {detection.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <span className="text-blue-500 mt-1">•</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === "timeline" && (
        <Card>
          <CardHeader>
            <CardTitle>Patient Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="h-2 w-2 bg-blue-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium">Patient Admitted</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(selectedPatient.admissionDate).toLocaleDateString()}
                  </p>
                </div>
              </div>
              {selectedPatient.lppDetections.map((detection) => (
                <div key={detection.id} className="flex items-start gap-4">
                  <div className={`h-2 w-2 rounded-full mt-2 ${
                    detection.grade >= 3 ? 'bg-red-500' :
                    detection.grade >= 2 ? 'bg-orange-500' :
                    'bg-yellow-500'
                  }`}></div>
                  <div>
                    <p className="font-medium">LPP Grade {detection.grade} Detected</p>
                    <p className="text-sm text-muted-foreground">
                      {detection.anatomicalLocation} • {new Date(detection.detectedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatientStore } from "@/store/patientStore";
import { Search, Plus, Users } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function PatientList() {
  const { patients, selectedPatient, setSelectedPatient } = usePatientStore();
  const [searchTerm, setSearchTerm] = useState("");

  const filteredPatients = patients.filter(patient =>
    patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.roomNumber?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRiskBadge = (risk: string) => {
    const colors = {
      high: "bg-red-100 text-red-800",
      medium: "bg-yellow-100 text-yellow-800", 
      low: "bg-green-100 text-green-800"
    };
    return (
      <span className={cn("px-2 py-1 rounded-full text-xs font-medium", colors[risk as keyof typeof colors])}>
        {risk.charAt(0).toUpperCase() + risk.slice(1)} Risk
      </span>
    );
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Patient List
            <span className="text-sm font-normal text-muted-foreground">
              ({filteredPatients.length})
            </span>
          </div>
          <button className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm">
            <Plus className="h-4 w-4" />
            Add Patient
          </button>
        </CardTitle>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search patients..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="space-y-1 max-h-96 overflow-y-auto">
          {filteredPatients.map((patient) => (
            <div
              key={patient.id}
              className={cn(
                "p-4 hover:bg-gray-50 cursor-pointer transition-colors border-l-4",
                selectedPatient?.id === patient.id ? "bg-blue-50 border-l-blue-500" : "border-l-transparent"
              )}
              onClick={() => setSelectedPatient(patient)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-sm font-medium">
                      {patient.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{patient.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {patient.age}y, {patient.gender} • Room {patient.roomNumber}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {getRiskBadge(patient.riskLevel)}
                  <p className="text-xs text-muted-foreground mt-1">
                    {patient.lppDetections.length} detection{patient.lppDetections.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
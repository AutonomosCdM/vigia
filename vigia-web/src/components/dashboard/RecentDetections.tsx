import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePatientStore } from "@/store/patientStore";
import { Eye, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export function RecentDetections() {
  const { patients, setSelectedPatient } = usePatientStore();
  
  // Get all detections and sort by date
  const allDetections = patients
    .flatMap(patient => 
      patient.lppDetections.map(detection => ({
        ...detection,
        patientName: patient.name,
        patient
      }))
    )
    .sort((a, b) => new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime())
    .slice(0, 5);

  const getGradeBadge = (grade: number) => {
    if (grade >= 3) return <Badge variant="destructive" className="bg-red-100 text-red-800">Grade {grade}</Badge>;
    if (grade >= 2) return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Grade {grade}</Badge>;
    if (grade >= 1) return <Badge variant="default" className="bg-blue-100 text-blue-800">Grade {grade}</Badge>;
    return <Badge variant="outline" className="bg-gray-100 text-gray-800">No LPP</Badge>;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return "text-green-600";
    if (confidence >= 0.8) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Recent LPP Detections
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {allDetections.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              No recent detections
            </p>
          ) : (
            allDetections.map((detection) => (
              <div
                key={detection.id}
                className="flex items-center justify-between p-4 rounded-lg border hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setSelectedPatient(detection.patient)}
              >
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-sm font-medium">
                      {detection.patientName.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{detection.patientName}</p>
                    <p className="text-sm text-muted-foreground">
                      {detection.anatomicalLocation} • {new Date(detection.detectedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {getGradeBadge(detection.grade)}
                  <span className={cn("text-sm font-medium", getConfidenceColor(detection.confidence))}>
                    {Math.round(detection.confidence * 100)}%
                  </span>
                  <button className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm">
                    <Eye className="h-4 w-4" />
                    View
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
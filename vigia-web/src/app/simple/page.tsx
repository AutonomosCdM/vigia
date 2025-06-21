"use client";

export default function SimpleDashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">V</span>
            </div>
            <h1 className="text-xl font-semibold">Vigia Medical Dashboard</h1>
          </div>
          <div className="text-sm">Dr. Rodriguez</div>
        </div>
      </header>

      <div className="p-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Patients</p>
                <p className="text-2xl font-bold">3</p>
              </div>
              <div className="h-12 w-12 bg-blue-50 rounded-lg flex items-center justify-center">
                👥
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">LPP Detected</p>
                <p className="text-2xl font-bold">2</p>
              </div>
              <div className="h-12 w-12 bg-red-50 rounded-lg flex items-center justify-center">
                ⚠️
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">High Risk</p>
                <p className="text-2xl font-bold">1</p>
              </div>
              <div className="h-12 w-12 bg-yellow-50 rounded-lg flex items-center justify-center">
                🏥
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Today&apos;s Scans</p>
                <p className="text-2xl font-bold">5</p>
              </div>
              <div className="h-12 w-12 bg-green-50 rounded-lg flex items-center justify-center">
                📱
              </div>
            </div>
          </div>
        </div>

        {/* Patient List */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">Patient List</h2>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                <div className="h-10 w-10 bg-blue-200 rounded-full flex items-center justify-center">
                  MG
                </div>
                <div>
                  <p className="font-medium">María García</p>
                  <p className="text-sm text-gray-600">75y, Room 305</p>
                  <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">High Risk</span>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg">
                <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                  JL
                </div>
                <div>
                  <p className="font-medium">Juan López</p>
                  <p className="text-sm text-gray-600">68y, Room 312</p>
                  <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Medium Risk</span>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg">
                <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                  AR
                </div>
                <div>
                  <p className="font-medium">Ana Rodríguez</p>
                  <p className="text-sm text-gray-600">82y, Room 301</p>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Low Risk</span>
                </div>
              </div>
            </div>
          </div>

          {/* Patient Details */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">Patient Details - María García</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium mb-4">LPP Detection</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Grade:</span>
                      <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm">Grade 2</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Confidence:</span>
                      <span className="font-medium">94%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Location:</span>
                      <span className="font-medium">Sacrum</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">New</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-4">Vital Signs</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Blood Pressure:</span>
                      <span className="font-medium">132/87 mmHg</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Heart Rate:</span>
                      <span className="font-medium">82 bpm</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Temperature:</span>
                      <span className="font-medium">100.4°F</span>
                    </div>
                    <div className="flex justify-between">
                      <span>O2 Saturation:</span>
                      <span className="font-medium">96%</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6">
                <h3 className="font-medium mb-3">Recommendations</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>Immediate pressure relief</li>
                  <li>Wound care specialist consultation</li>
                  <li>Nutritional assessment</li>
                </ul>
              </div>
              
              <div className="mt-6 flex gap-3">
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                  Upload New Image
                </button>
                <button className="border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50">
                  Generate Report
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
"use client";

export default function Home() {
  return (
    <div className="flex h-screen bg-slate-50">
      {/* Dark Sidebar */}
      <div className="w-16 bg-slate-700 flex flex-col items-center py-4">
        {/* Navigation Icons */}
        <div className="flex flex-col space-y-4 mb-auto">
          {/* Dashboard - Active */}
          <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
            </svg>
          </div>
          
          {/* Users */}
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
            </svg>
          </div>
          
          {/* Documents */}
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
            </svg>
          </div>
          
          {/* Messages */}
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
            </svg>
          </div>
          
          {/* Trash */}
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          
          {/* Analytics */}
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
            </svg>
          </div>
          
          {/* Canvas */}
          <a href="/canvas" className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500 transition-colors">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
            </svg>
          </a>
          
          {/* Settings */}
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-500">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
        
        {/* User Avatar */}
        <div className="w-10 h-10 bg-teal-500 rounded-full flex items-center justify-center">
          <span className="text-white font-semibold text-sm">JS</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-medium text-gray-900 tracking-tighter">ACG Dashboard</h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                <input type="text" placeholder="Search..." className="border-0 focus:ring-0 text-sm" />
              </div>
              <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
                Admin Config
              </button>
              <button className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600">
                Action Hub
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 overflow-auto">
          {/* Top Summary Cards */}
          <div className="grid grid-cols-4 gap-6 mb-6">
            {/* US Elderly Model Card */}
            <div className="bg-green-50 rounded-lg p-4 relative">
              <div className="absolute top-4 right-4">
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                </svg>
              </div>
              <div className="text-sm text-gray-600 mb-1">US Elderly</div>
              <div className="text-sm text-gray-600 mb-2">Model</div>
              <div className="text-3xl font-medium text-gray-900 mb-1 tracking-tight">530</div>
              <div className="text-sm text-gray-600">Members</div>
            </div>

            {/* Average Risk Card */}
            <div className="bg-blue-50 rounded-lg p-4 relative">
              <div className="absolute top-4 right-4">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-3xl font-medium text-gray-900 mb-2 tracking-tight">2.19</div>
              <div className="text-sm text-gray-600">Average Risk</div>
            </div>

            {/* Observation Period Card */}
            <div className="bg-amber-50 rounded-lg p-4 relative">
              <div className="absolute top-4 right-4">
                <svg className="w-5 h-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-2xl font-medium text-gray-900 mb-2 tracking-tight">Jan - Dec 2023</div>
              <div className="text-sm text-gray-600">Observation Period</div>
            </div>

            {/* Model Run Date Card */}
            <div className="bg-pink-50 rounded-lg p-4 relative">
              <div className="absolute top-4 right-4">
                <svg className="w-5 h-5 text-pink-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-2xl font-medium text-gray-900 mb-2 tracking-tight">26 Mar, 2024</div>
              <div className="text-sm text-gray-600">Model Run Date</div>
            </div>
          </div>

          {/* Resource Utilization Section */}
          <div className="bg-white rounded-lg shadow-sm border mb-6">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium tracking-tight">Resource Utilization Band (RUB) Distribution</h2>
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                  </svg>
                  <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="p-4">
              <div className="flex space-x-4">
                <span className="bg-slate-800 text-white px-3 py-1 rounded-full text-sm font-medium">All Utilizers 539</span>
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">Non - Utilizers 35</span>
                <span className="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm">Healthy Utilizers 145</span>
                <span className="bg-yellow-200 text-yellow-800 px-3 py-1 rounded-full text-sm">Low Utilizers 200</span>
                <span className="bg-orange-200 text-orange-800 px-3 py-1 rounded-full text-sm">Moderate Utilizers 294</span>
                <span className="bg-red-200 text-red-800 px-3 py-1 rounded-full text-sm">High Utilizers 212</span>
              </div>
            </div>
          </div>

          {/* Morbidity Marker Section */}
          <div className="grid grid-cols-12 gap-6">
            {/* Left Sidebar */}
            <div className="col-span-3 space-y-6">
              {/* Morbidity Marker Filters */}
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="font-medium tracking-tight">Morbidity Marker</h3>
                  <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input type="radio" name="morbidity" className="mr-2 text-emerald-500" />
                    <span className="text-sm">ACG</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="morbidity" className="mr-2 text-emerald-500" />
                    <span className="text-sm">ACG+MADGs</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="morbidity" className="mr-2 text-emerald-500" checked />
                    <span className="text-sm">MEDC/EDC</span>
                  </label>
                  <label className="flex items-center">
                    <input type="radio" name="morbidity" className="mr-2 text-emerald-500" />
                    <span className="text-sm">MEDC+MADGs</span>
                  </label>
                </div>
              </div>

              {/* Category List */}
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="p-4 border-b">
                  <div className="grid grid-cols-2 gap-4 text-sm font-medium text-gray-600">
                    <span>Category</span>
                    <span>Patient Count</span>
                  </div>
                </div>
                <div className="p-4 space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span>Administrative</span>
                    <span className="font-medium">202</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Allergy</span>
                    <span className="font-medium">32</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Cardiovascular</span>
                    <span className="font-medium">165</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Dental</span>
                    <span className="font-medium">127</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ear, Nose, Throat</span>
                    <span className="font-medium">40</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Hashimoto&apos;s Thyroiditis</span>
                    <span className="font-medium">55</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Endocrine</span>
                    <span className="font-medium">27</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Hyperthyroidism</span>
                    <span className="font-medium">89</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Type 1 Diabetes Mellitus</span>
                    <span className="font-medium">62</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Type 2 Diabetes Mellitus</span>
                    <span className="font-medium">142</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Table */}
            <div className="col-span-9">
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-4 py-3 text-left">
                          <input type="checkbox" className="rounded" />
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Account</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Patient Name</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">DOB</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">PCP</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Insurance</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">ACG Risk</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Annual Inpatient Stay</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Half-Year Inpatient Stay</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Open Days</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Projected Days</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      <tr className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <input type="checkbox" className="rounded" />
                        </td>
                        <td className="px-4 py-3 text-sm">10067</td>
                        <td className="px-4 py-3 text-sm font-medium">Nancy Adams</td>
                        <td className="px-4 py-3 text-sm">09/28/1973</td>
                        <td className="px-4 py-3 text-sm">Wade Warren</td>
                        <td className="px-4 py-3 text-sm">Acme Co.</td>
                        <td className="px-4 py-3 text-sm font-medium">3.8</td>
                        <td className="px-4 py-3 text-sm">12</td>
                        <td className="px-4 py-3 text-sm">18</td>
                        <td className="px-4 py-3 text-sm text-blue-600 font-medium">18</td>
                        <td className="px-4 py-3 text-sm">$25,000 - $50,000</td>
                      </tr>
                      <tr className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <input type="checkbox" className="rounded" />
                        </td>
                        <td className="px-4 py-3 text-sm">10068</td>
                        <td className="px-4 py-3 text-sm font-medium">Wade Warren</td>
                        <td className="px-4 py-3 text-sm">09/12/1990</td>
                        <td className="px-4 py-3 text-sm">Cody Fisher</td>
                        <td className="px-4 py-3 text-sm">Abstrego Ltd.</td>
                        <td className="px-4 py-3 text-sm font-medium">1.2</td>
                        <td className="px-4 py-3 text-sm">9</td>
                        <td className="px-4 py-3 text-sm">3</td>
                        <td className="px-4 py-3 text-sm text-blue-600 font-medium">8</td>
                        <td className="px-4 py-3 text-sm">$27,000 - $52,000</td>
                      </tr>
                      <tr className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <input type="checkbox" className="rounded" />
                        </td>
                        <td className="px-4 py-3 text-sm">10069</td>
                        <td className="px-4 py-3 text-sm font-medium">Guy Hawkins</td>
                        <td className="px-4 py-3 text-sm">08/28/1985</td>
                        <td className="px-4 py-3 text-sm">Kristin Watson</td>
                        <td className="px-4 py-3 text-sm">Barone LLC</td>
                        <td className="px-4 py-3 text-sm font-medium">3.2</td>
                        <td className="px-4 py-3 text-sm">2</td>
                        <td className="px-4 py-3 text-sm">11</td>
                        <td className="px-4 py-3 text-sm text-blue-600 font-medium">10</td>
                        <td className="px-4 py-3 text-sm">$15,000 - $50,000</td>
                      </tr>
                      <tr className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <input type="checkbox" className="rounded" />
                        </td>
                        <td className="px-4 py-3 text-sm">30289</td>
                        <td className="px-4 py-3 text-sm font-medium">Darrell Steward</td>
                        <td className="px-4 py-3 text-sm">12/31/1981</td>
                        <td className="px-4 py-3 text-sm">Ronald Richards</td>
                        <td className="px-4 py-3 text-sm">Abstrego Ltd.</td>
                        <td className="px-4 py-3 text-sm font-medium">4.1</td>
                        <td className="px-4 py-3 text-sm">11</td>
                        <td className="px-4 py-3 text-sm">7</td>
                        <td className="px-4 py-3 text-sm text-blue-600 font-medium">2</td>
                        <td className="px-4 py-3 text-sm">$25,000 - $50,000</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Analytics Sections */}
          <div className="grid grid-cols-3 gap-6 mt-6">
            {/* ACG Risk Score */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="text-3xl font-bold text-gray-900 mb-2">4.1</div>
              <div className="text-sm text-gray-600 mb-4">ACG Risk Score</div>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">RUB Assignment</span>
                </div>
                <div>
                  <span className="font-medium">High Utilizer (RUB 4)</span>
                </div>
                <div>
                  <span className="text-gray-600">Description:</span>
                </div>
                <div>
                  <span className="text-gray-600">4-5 Other ACG Combinations</span>
                </div>
              </div>
            </div>

            {/* ADGs */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="text-lg font-semibold mb-4">ADGs</div>
              <div className="space-y-2 text-sm">
                <div>ADG 1: Time Limited: Minor</div>
                <div>ADG 3: Time Limited: Major</div>
                <div>ADG 7: Likely to Recur: Discrete</div>
                <div>ADG 11: Chronic Medical: Unstable</div>
                <div>ADG 32: Administrative</div>
              </div>
            </div>

            {/* HCC Risk Score */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="text-3xl font-bold text-gray-900 mb-2">1.94</div>
              <div className="text-sm text-gray-600 mb-4">HCC Risk Score</div>
              
              <div className="space-y-4 text-sm">
                <div>
                  <div className="font-medium mb-2">HCC Gaps (2)</div>
                  <ul className="space-y-1 text-gray-600">
                    <li>• Long-term use of anticoagulants</li>
                    <li>• Congestive heart failure (2)</li>
                  </ul>
                </div>
                
                <div>
                  <div className="font-medium mb-2">CDM Non-Compliant Measures (3)</div>
                  <ul className="space-y-1 text-gray-600">
                    <li>• Diabetes A1C Control (&lt;8%)</li>
                    <li>• Diabetes LDL-C Control (&lt;100)</li>
                    <li>• Pneumococcal Vaccine (+65)</li>
                  </ul>
                </div>
                
                <div>
                  <div className="font-medium mb-2">Compliant Measures (2)</div>
                  <ul className="space-y-1 text-gray-600">
                    <li>• Adult Wellness Visit (02/02/2023)</li>
                    <li>• Adult BMI Visit (02/02/2023)</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Pagination */}
          <div className="flex justify-center items-center mt-8 space-x-2">
            <button className="p-2 rounded-lg border hover:bg-gray-50">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </button>
            
            <button className="px-3 py-2 bg-emerald-500 text-white rounded-lg font-medium">1</button>
            <button className="px-3 py-2 rounded-lg border hover:bg-gray-50">2</button>
            <button className="px-3 py-2 rounded-lg border hover:bg-gray-50">3</button>
            <button className="px-3 py-2 rounded-lg border hover:bg-gray-50">4</button>
            <button className="px-3 py-2 rounded-lg border hover:bg-gray-50">5</button>
            <span className="px-2 text-gray-500">...</span>
            <button className="px-3 py-2 rounded-lg border hover:bg-gray-50">9</button>
            <button className="px-3 py-2 rounded-lg border hover:bg-gray-50">10</button>
            
            <button className="p-2 rounded-lg border hover:bg-gray-50">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
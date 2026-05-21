import { useState, useEffect, useRef } from 'react';
import { 
  User, WifiOff, AlertTriangle, MapPin, 
  Target, Bug, PackageMinus, Sparkles, Quote, 
  CheckCircle, AlertCircle, LayoutDashboard, Settings, RefreshCcw,
  Send, Bot, MessageSquare, X
} from 'lucide-react';

const getUrgencyColors = (urgency) => {
  if (urgency === 'critical') return { bg: 'bg-rose-500', text: 'text-rose-700', badge: 'bg-rose-100 text-rose-800' };
  if (urgency === 'high') return { bg: 'bg-orange-500', text: 'text-orange-700', badge: 'bg-orange-100 text-orange-800' };
  return { bg: 'bg-yellow-400', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-800' };
};

export default function FieldCoPilot() {
  const [visitsData, setVisitsData] = useState([]);
  const [activeVisit, setActiveVisit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState('All Locations');
  const [availableLocations, setAvailableLocations] = useState(['All Locations']);
  
  const [selectedTehsil, setSelectedTehsil] = useState('All Tehsils');
  const [availableTehsils, setAvailableTehsils] = useState(['All Tehsils']);

  // Chat State
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Fetch Available Locations (Districts) on Mount
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/locations');
        if (response.ok) {
          const data = await response.json();
          setAvailableLocations(['All Locations', ...data]);
        }
      } catch (err) {
        console.error("Failed to fetch locations", err);
      }
    };
    fetchLocations();
  }, []);

  // Fetch Available Tehsils when District changes
  useEffect(() => {
    const fetchTehsils = async () => {
      if (selectedLocation === 'All Locations') {
        setAvailableTehsils(['All Tehsils']);
        setSelectedTehsil('All Tehsils');
        return;
      }
      
      try {
        const response = await fetch(`http://localhost:8000/api/tehsils?district=${selectedLocation}`);
        if (response.ok) {
          const data = await response.json();
          setAvailableTehsils(['All Tehsils', ...data]);
          setSelectedTehsil('All Tehsils');
        }
      } catch (err) {
        console.error("Failed to fetch tehsils", err);
      }
    };
    fetchTehsils();
  }, [selectedLocation]);

  // Fetch Dashboard Data whenever selectedLocation or selectedTehsil changes
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        let url = 'http://localhost:8000/api/routes';
        const params = new URLSearchParams();
        
        if (selectedLocation !== 'All Locations') {
          params.append('district', selectedLocation);
        }
        if (selectedTehsil !== 'All Tehsils') {
          params.append('tehsil', selectedTehsil);
        }
        
        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;
          
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setVisitsData(data);
        
        if (data.length > 0) {
          setActiveVisit(data[0]);
        } else {
          setActiveVisit(null);
        }
        
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedLocation, selectedTehsil]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || !activeVisit) return;

    const newMessage = { role: 'user', text: userInput };
    setChatMessages(prev => [...prev, newMessage]);
    setUserInput("");
    setChatLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userInput,
          context: activeVisit
        })
      });
      
      const data = await response.json();
      setChatMessages(prev => [...prev, { role: 'assistant', text: data.reply }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', text: "Connection to AI Brain lost. Check backend." }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading && visitsData.length === 0) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-100">
        <div className="text-center">
          <RefreshCcw className="w-12 h-12 text-emerald-600 animate-spin mx-auto mb-4" />
          <p className="text-slate-600 font-medium">Syncing with Syngenta Cloud...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-100">
        <div className="bg-white p-8 rounded-2xl shadow-xl border border-rose-100 text-center max-w-md">
          <WifiOff className="w-16 h-16 text-rose-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Connection Failed</h2>
          <p className="text-slate-600 mb-6">Unable to reach the backend server. Please ensure the FastAPI server is running on port 8000.</p>
          <button 
            onClick={() => window.location.reload()}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-lg transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-slate-100 font-sans text-slate-800 overflow-hidden">
      
      {/* =========================================
          LEFT SIDEBAR: Navigation & List
      ========================================= */}
      <div className="w-full lg:w-[450px] bg-white border-r border-slate-200 flex flex-col h-full z-10 shadow-sm shrink-0">
        
        {/* Top Branding / Nav */}
        <div className="bg-emerald-800 text-white p-4 flex justify-between items-center shrink-0">
          <div className="flex items-center space-x-3">
            <LayoutDashboard className="w-6 h-6 text-emerald-300" />
            <h1 className="font-bold text-xl tracking-wide">Syngenta Co-Pilot</h1>
          </div>
          <div className="flex space-x-4">
            <Settings className="w-5 h-5 text-emerald-300 cursor-pointer hover:text-white transition" />
            <User className="w-5 h-5 text-emerald-300 cursor-pointer hover:text-white transition" />
          </div>
        </div>

{/* System Status & Alert Banner */}
        <div className="bg-slate-900 text-white p-4 shrink-0 shadow-inner">
          <div className="flex justify-between items-center font-semibold mb-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-sm tracking-widest uppercase text-slate-300">System Live</span>
            </div>
            <span className="text-emerald-400 text-xs font-normal">Cloud Connected</span>
          </div>
          
          <div className="flex items-start space-x-3 bg-black/20 p-3 rounded-lg border border-slate-700/50">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-yellow-400" />
            <p className="text-sm leading-relaxed text-slate-200">
              <span className="font-bold text-yellow-400">REGIONAL ALERT:</span> Heavy rainfall detected in East District. FAW hatch probability: 85% in next 48 hrs.
            </p>
          </div>
        </div>

        {/* Scrollable List */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-50">
          {/* Multi-Level Filter Area */}
          <div className="space-y-4 mb-8 px-1">
            <div>
              <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-2">District Selection</h2>
              <div className="relative">
                <select 
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg py-2.5 pl-3 pr-10 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 appearance-none shadow-sm cursor-pointer"
                >
                  {availableLocations.map(loc => (
                    <option key={loc} value={loc}>{loc}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                  <MapPin className="w-4 h-4" />
                </div>
              </div>
            </div>

            {selectedLocation !== 'All Locations' && (
              <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-2">Tehsil Filter</h2>
                <div className="relative">
                  <select 
                    value={selectedTehsil}
                    onChange={(e) => setSelectedTehsil(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg py-2.5 pl-3 pr-10 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 appearance-none shadow-sm cursor-pointer"
                  >
                    {availableTehsils.map(teh => (
                      <option key={teh} value={teh}>{teh}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                    <Target className="w-4 h-4" />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between items-end mb-4 px-1">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Route Schedule</h2>
            <div className="flex items-center space-x-2">
              {loading && <RefreshCcw className="w-3.5 h-3.5 text-emerald-600 animate-spin" />}
              <span className="text-xs font-bold text-slate-400">{visitsData.length} Stops</span>
            </div>
          </div>
          
          <div className="space-y-4 pb-6">
            {visitsData.map((visit) => {
              const colors = getUrgencyColors(visit.urgency);
              const isActive = activeVisit?.id === visit.id;
              
              return (
                <div 
                  key={visit.id}
                  onClick={() => setActiveVisit(visit)}
                  className={`relative rounded-xl shadow-sm border transition-all cursor-pointer overflow-hidden
                    ${isActive ? 'bg-emerald-50/50 border-emerald-500 ring-2 ring-emerald-500/20 translate-x-1' : 'bg-white border-slate-200 hover:border-emerald-300 hover:shadow-md'}`}
                >
                  <div className={`absolute top-0 left-0 bottom-0 w-1.5 ${colors.bg}`}></div>
                  <div className="p-4 pl-6">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 block">{visit.type}</span>
                        <h3 className="font-bold text-slate-800 text-lg">{visit.name}</h3>
                        <p className="text-xs text-slate-500 mt-1 flex items-center">
                          <MapPin className="w-3 h-3 mr-1" /> {visit.location}
                        </p>
                      </div>
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${colors.badge}`}>
                        {visit.urgency.toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="bg-white/50 rounded-lg p-3 mt-3 border border-slate-100">
                      <p className={`text-xs font-semibold ${colors.text} mb-1 flex items-center`}>
                        <AlertCircle className="w-3.5 h-3.5 mr-1" /> Threat: {visit.threat}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* =========================================
          RIGHT MAIN PANEL: Detail View
      ========================================= */}
      <div className="hidden lg:flex flex-1 flex-col h-full bg-slate-100 overflow-y-auto relative">
        {activeVisit ? (
          <div className="max-w-4xl w-full mx-auto p-8 space-y-8 pb-20">
            
            <div className="flex justify-between items-end border-b border-slate-200 pb-6">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 mb-2 block">
                  {activeVisit.type} Profile
                </span>
                <h1 className="text-3xl font-extrabold text-slate-900">{activeVisit.name}</h1>
                <div className="flex items-center space-x-4 mt-3 text-slate-500 text-sm font-medium">
                  <span className="flex items-center"><MapPin className="w-4 h-4 mr-1"/> {activeVisit.location}</span>
                  <span>•</span>
                  <span>ID: {activeVisit.id}0084A</span>
                </div>
              </div>
              <div className="flex space-x-3">
                <button 
                  onClick={() => setChatOpen(true)}
                  className="bg-white border border-emerald-600 text-emerald-600 hover:bg-emerald-50 font-bold py-3 px-6 rounded-lg shadow-sm transition flex items-center space-x-2"
                >
                  <MessageSquare className="w-5 h-5" />
                  <span>Explain Metrics</span>
                </button>
                <button className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-lg shadow transition flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5" />
                  <span>Log Visit</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">AI Next Best Action</h3>
                <div className="flex items-start space-x-3">
                  <Target className="w-6 h-6 text-emerald-600 mt-1" />
                  <div>
                    <p className="text-lg font-bold text-slate-800">{activeVisit.action}</p>
                    <p className="text-sm text-emerald-600 font-medium mt-1">{activeVisit.details.closeProb}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Financial Context</h3>
                <p className="text-2xl font-bold text-slate-800">{activeVisit.riskValue}</p>
                <p className="text-sm text-slate-500 mt-1">Based on CRM & Predictive Modeling</p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">Data Fusion Justification</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="p-1.5 bg-rose-100 rounded-lg shrink-0"><Bug className="w-5 h-5 text-rose-600" /></div>
                    <span className="font-bold text-slate-800 leading-tight">Biological Threat</span>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{activeVisit.details.threatData}</p>
                </div>
                
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="p-1.5 bg-orange-100 rounded-lg shrink-0"><PackageMinus className="w-5 h-5 text-orange-600" /></div>
                    <span className="font-bold text-slate-800 leading-tight">
                      {activeVisit.type === 'Retailer' ? 'Inventory Status' : 'Grower Activity'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{activeVisit.details.inventoryData}</p>
                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                      {activeVisit.type === 'Retailer' ? 'Stock as of' : 'Last Scanned'}
                    </span>
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                      {activeVisit.type === 'Retailer' ? activeVisit.details.inventoryDate : activeVisit.details.activityDate}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 text-purple-600" /> Auto-Generated Pitch Script
                </h3>
                <div className="bg-slate-900 rounded-2xl shadow-lg p-8 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-6 opacity-10">
                    <Quote className="w-24 h-24" />
                  </div>
                  <p className="text-lg leading-relaxed text-slate-200 italic relative z-10 max-w-3xl">
                    "{activeVisit.details.script}"
                  </p>
                </div>
              </div>

              <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 px-6 rounded-xl shadow-lg transition flex items-center justify-center space-x-2 group">
                <CheckCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
                <span className="text-lg">Complete and Log Visit</span>
              </button>
            </div>

          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <LayoutDashboard className="w-16 h-16 mb-4 opacity-20" />
            <p className="text-lg font-medium">Select a visit from the schedule to view details.</p>
          </div>
        )}

        {/* =========================================
            AI CHAT SLIDE-OVER
        ========================================= */}
        {chatOpen && (
          <div className="absolute inset-y-0 right-0 w-96 bg-white shadow-2xl border-l border-slate-200 z-50 flex flex-col animate-in slide-in-from-right duration-300">
            {/* Chat Header */}
            <div className="p-4 bg-emerald-800 text-white flex justify-between items-center shrink-0">
              <div className="flex items-center space-x-2">
                <Bot className="w-6 h-6 text-emerald-300" />
                <h2 className="font-bold">Co-Pilot Insight</h2>
              </div>
              <button onClick={() => setChatOpen(false)} className="hover:bg-emerald-700 p-1 rounded transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
              {chatMessages.length === 0 && (
                <div className="text-center py-10 px-6">
                  <Sparkles className="w-10 h-10 text-emerald-200 mx-auto mb-3" />
                  <p className="text-slate-500 text-sm italic">
                    I'm synced with the ML model for <span className="font-bold text-slate-700">{activeVisit.name}</span>. Ask me anything about the risk prediction!
                  </p>
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl p-3 text-sm shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-emerald-600 text-white rounded-br-none' 
                      : 'bg-white border border-slate-200 text-slate-700 rounded-bl-none'
                  }`}>
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none p-3 shadow-sm">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <form onSubmit={handleSendMessage} className="p-4 bg-white border-t border-slate-100 shrink-0">
              <div className="relative">
                <input 
                  type="text"
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="Ask why risk is high..."
                  className="w-full bg-slate-100 border-none rounded-xl py-3 pl-4 pr-12 text-sm focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all shadow-inner"
                />
                <button 
                  type="submit" 
                  disabled={chatLoading}
                  className="absolute right-2 top-1.5 p-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

    </div>
  );
}

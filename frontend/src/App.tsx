import { useState, useEffect } from 'react';
import { Upload, Send, Bot, User, Briefcase, MapPin, Loader2, Link } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

export function App() {
  const [messages, setMessages] = useState([
    { id: 1, type: 'agent', text: "Hello! I'm InternPilot. I can help you find, evaluate, and apply to internships. Have you uploaded your resume yet?" }
  ]);
  const [inputText, setInputText] = useState('');
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [status, setStatus] = useState<'idle' | 'searching' | 'search_completed' | 'no_results' | 'search_failed' | 'llm_unavailable'>('idle');
  const [workflowStatusMsg, setWorkflowStatusMsg] = useState('');

  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  useEffect(() => {
    let interval: any;
    if (workflowId && status === 'searching') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}`);
          if (res.ok) {
            const data = await res.json();
            
            if (data.status === 'completed' || data.status === 'partial_success') {
              setStatus('search_completed');
              const oppsRes = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/opportunities`);
              if (oppsRes.ok) {
                const oppsData = await oppsRes.json();
                setOpportunities(oppsData.opportunities || []);
                setMessages(prev => [...prev, { 
                  id: Date.now(), 
                  type: 'agent', 
                  text: `I have discovered ${oppsData.opportunities?.length || 0} matching internship opportunities for you.` 
                }]);
              }
              clearInterval(interval);
            } else if (data.status === 'no_results') {
              setStatus('no_results');
              clearInterval(interval);
            } else if (data.status === 'failed' || data.status === 'search_failed' || data.status === 'cancelled') {
              setStatus('search_failed');
              clearInterval(interval);
            } else {
              setWorkflowStatusMsg(`Workflow running: ${data.current_stage.replace('_', ' ')}...`);
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [workflowId, status]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    
    const textToSend = inputText;
    setMessages(prev => [...prev, { id: Date.now(), type: 'user', text: textToSend }]);
    setInputText('');
    setStatus('searching');
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/agent/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend, session_id: sessionId, student_id: 'demo-student-123' })
      });
      
      const data = await response.json();
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }
      
      if (data.action === "error") {
        setStatus('search_failed');
      } else if (data.response?.includes("API Error") || data.response?.includes("offline")) {
        setStatus('llm_unavailable');
      } else if (data.opportunities && data.opportunities.length > 0) {
        setOpportunities(data.opportunities);
        setStatus('search_completed');
      } else if (data.opportunities && data.opportunities.length === 0) {
        setStatus('no_results');
      } else {
        setStatus('idle');
      }
      
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        type: 'agent', 
        text: data.response || "Sorry, I couldn't understand that."
      }]);
    } catch (error) {
      console.error('Error communicating with backend:', error);
      setStatus('search_failed');
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        type: 'agent', 
        text: "Error communicating with the agentic backend. Make sure it's running on localhost:8000." 
      }]);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('student_id', 'demo-student-123');
    formData.append('file', file);

    setMessages(prev => [...prev, { 
      id: Date.now(), 
      type: 'agent', 
      text: `Uploading and analyzing ${file.name}...` 
    }]);

    try {
      const response = await fetch('http://localhost:8000/api/v1/resumes/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();
      
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        type: 'agent', 
        text: `Successfully uploaded ${file.name} and extracted your profile. Automatic background workflow started...` 
      }]);
      
      if (data.workflow_id) {
        setWorkflowId(data.workflow_id);
        setStatus('searching');
        setWorkflowStatusMsg("Starting autonomous workflow...");
      }

    } catch (error) {
      console.error('Error uploading file:', error);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        type: 'agent', 
        text: `Error uploading ${file.name}. Please ensure the backend is running.` 
      }]);
    }
  };

  return (
    <div className="app-layout">
      {/* LEFT SIDEBAR - Profile & Controls */}
      <motion.aside 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="glass sidebar"
      >
        <div className="brand">
          <Bot size={32} color="#3b82f6" />
          <span>InternPilot</span>
        </div>
        
        <div className="profile-section">
          <h3>Your Profile</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            Upload your resume to let the agent extract your skills and match you to better opportunities.
          </p>
          <label className="upload-btn" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
            <Upload size={24} color="var(--accent)" />
            <span>Drop your resume here</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>PDF, DOCX, TXT</span>
            <input 
              type="file" 
              accept=".pdf,.docx,.txt" 
              style={{ display: 'none' }} 
              onChange={handleFileUpload}
            />
          </label>
        </div>
      </motion.aside>

      {/* CENTER - Chat Interface */}
      <motion.main 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass chat-container"
      >
        <div className="chat-header">
          <Bot size={24} color="var(--accent)" />
          <h2>Agentic Coordinator</h2>
        </div>
        
        <div className="chat-messages">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div 
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`message ${msg.type}`}
              >
                <div className="avatar">
                  {msg.type === 'agent' ? <Bot size={20} color="white" /> : <User size={20} color="white" />}
                </div>
                <div className="bubble">
                  {msg.type === 'agent' ? <ReactMarkdown>{msg.text}</ReactMarkdown> : msg.text}
                </div>
              </motion.div>
            ))}
            {status === 'searching' && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="message agent"
              >
                <div className="avatar"><Bot size={20} color="white" /></div>
                <div className="bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Loader2 size={16} className="spinner" /> 
                  {workflowStatusMsg || "Searching for opportunities..."}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        <div className="chat-input-wrapper">
          <form className="chat-input" onSubmit={handleSend}>
            <input 
              type="text" 
              placeholder="Ask me to find internships or analyze a role..." 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <button type="submit">
              <Send size={18} />
            </button>
          </form>
        </div>
      </motion.main>

      {/* RIGHT SIDEBAR - Opportunities */}
      <motion.aside 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="glass opp-panel"
      >
        <div className="opp-header">
          <h2>Discovered Opportunities</h2>
          {status === 'searching' && <span style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>{workflowStatusMsg || 'Searching...'}</span>}
          {status === 'no_results' && <span style={{ fontSize: '0.8rem', color: '#ff4444' }}>No results found</span>}
          {status === 'search_failed' && <span style={{ fontSize: '0.8rem', color: '#ff4444' }}>Search Failed</span>}
          {status === 'llm_unavailable' && <span style={{ fontSize: '0.8rem', color: '#ff4444' }}>LLM Offline</span>}
        </div>
        <div className="opp-list">
          {opportunities.length === 0 ? (
            <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--text-secondary)' }}>
              <Briefcase size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
              <p>Opportunities will appear here once the agent starts searching.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {opportunities.map((opp, idx) => (
                <div key={idx} style={{ background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '1.1rem' }}>{opp.role}</h3>
                    <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>
                      {opp.source === 'adzuna' ? 'Adzuna' : opp.source === 'web_search' ? 'Web Search' : opp.source}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                    <Briefcase size={16} /> <span>{opp.company}</span>
                    <MapPin size={16} style={{ marginLeft: '8px' }} /> <span>{opp.location || 'Remote/Unknown'}</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '16px', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {opp.description}
                  </p>
                  {opp.application_url && (
                    <a href={opp.application_url} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'var(--accent)', color: 'white', padding: '8px 16px', borderRadius: '6px', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>
                      <Link size={14} /> Apply Now
                    </a>
                  )}
                  {!opp.application_url && (
                    <span style={{ fontSize: '0.8rem', color: '#ff4444' }}>No Application Link Available</span>
                  )}
                  {opp.overall_score && (
                    <div style={{ marginTop: '12px', padding: '8px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '6px', fontSize: '0.85rem' }}>
                      <strong style={{ color: 'var(--accent)' }}>Match Reasoning:</strong>
                      <p style={{ marginTop: '4px', marginBottom: 0, color: 'var(--text-secondary)' }}>{opp.explanation}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.aside>
    </div>
  );
}

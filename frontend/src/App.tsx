import { useState, useEffect, useRef } from 'react';
import { Upload, Send, Bot, User, Briefcase, MapPin, Loader2, ExternalLink, CheckCircle2, XCircle, AlertCircle, Zap, Target, Search, Award, ChevronRight, GraduationCap, Code2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

const API = 'http://localhost:8000/api/v1';

interface ParsedProfile {
  name?: string;
  email?: string;
  skills: string[];
  inferred_roles: string[];
  education: any[];
  cgpa?: number;
  projects: any[];
  experience: string[];
}

interface Recommendation {
  company: string;
  role: string;
  location?: string;
  description: string;
  application_url?: string;
  source: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  eligibility: string;
  rationale: string;
}

export function App() {
  const [messages, setMessages] = useState([
    { id: 1, type: 'agent', text: "Hello! I'm **InternPilot**. Upload your resume to get personalized internship recommendations powered by AI agents." }
  ]);
  const [inputText, setInputText] = useState('');
  const [profile, setProfile] = useState<ParsedProfile | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [agentTrace, setAgentTrace] = useState<string[]>([]);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'pipeline_running' | 'completed' | 'failed'>('idle');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [studentId] = useState('demo-student-123');
  const [activeTab, setActiveTab] = useState<'recommendations' | 'trace'>('recommendations');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Poll workflow status
  useEffect(() => {
    let interval: any;
    if (workflowId && status === 'pipeline_running') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API}/workflows/${workflowId}`);
          if (!res.ok) return;
          const data = await res.json();

          if (data.status === 'completed' || data.status === 'partial_success') {
            clearInterval(interval);
            // Fetch results via one-shot endpoint
            const pipelineRes = await fetch(`${API}/workflows/run`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ student_id: studentId })
            });
            if (pipelineRes.ok) {
              const pipelineData = await pipelineRes.json();
              setRecommendations(pipelineData.recommendations || []);
              setAgentTrace(pipelineData.agent_trace || []);
              if (pipelineData.resume_profile) {
                setProfile(prev => prev || pipelineData.resume_profile);
              }
              setMessages(prev => [...prev, {
                id: Date.now(), type: 'agent',
                text: `✅ Pipeline complete! Found **${pipelineData.recommendations?.length || 0}** internship recommendations ranked by match score.`
              }]);
            }
            setStatus('completed');
          } else if (data.status === 'failed' || data.status === 'cancelled') {
            clearInterval(interval);
            setStatus('failed');
            setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: '❌ The agent pipeline encountered an error. Please try again.' }]);
          }
        } catch (e) { console.error(e); }
      }, 2500);
    }
    return () => { if (interval) clearInterval(interval); };
  }, [workflowId, status]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setStatus('uploading');
    setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: `📄 Uploading and analyzing **${file.name}**...` }]);

    const formData = new FormData();
    formData.append('student_id', studentId);
    formData.append('file', file);

    try {
      const response = await fetch(`${API}/resumes/upload`, { method: 'POST', body: formData });
      if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
      const data = await response.json();

      // Set parsed profile immediately
      if (data.parsed_profile) {
        setProfile(data.parsed_profile);
        const skillCount = data.parsed_profile.skills?.length || 0;
        const roleCount = data.parsed_profile.inferred_roles?.length || 0;
        setMessages(prev => [...prev, {
          id: Date.now(), type: 'agent',
          text: `✅ Resume parsed! Found **${skillCount} skills** and inferred **${roleCount} target roles**.\n\n🤖 Agents are now searching for matching internships...`
        }]);
      }

      if (data.workflow_id) {
        setWorkflowId(data.workflow_id);
        setStatus('pipeline_running');
      }
    } catch (error) {
      console.error(error);
      setStatus('failed');
      setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: `❌ Error uploading ${file.name}. Check that the backend is running.` }]);
    }
  };

  const handleRunPipeline = async () => {
    if (!profile) return;
    setStatus('pipeline_running');
    setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: '🔍 Running agent pipeline...' }]);

    try {
      const res = await fetch(`${API}/workflows/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId })
      });
      if (!res.ok) throw new Error('Pipeline failed');
      const data = await res.json();
      setRecommendations(data.recommendations || []);
      setAgentTrace(data.agent_trace || []);
      setStatus('completed');
      setMessages(prev => [...prev, {
        id: Date.now(), type: 'agent',
        text: `✅ Found **${data.recommendations?.length || 0}** internship matches ranked by relevance!`
      }]);
    } catch (e) {
      setStatus('failed');
      setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: '❌ Pipeline error. Please try again.' }]);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    const text = inputText;
    setMessages(prev => [...prev, { id: Date.now(), type: 'user', text }]);
    setInputText('');

    try {
      const res = await fetch(`${API}/agent/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId, student_id: studentId })
      });
      const data = await res.json();
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      if (data.opportunities?.length) setRecommendations(data.opportunities);
      setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: data.response || "I couldn't process that." }]);
    } catch {
      setMessages(prev => [...prev, { id: Date.now(), type: 'agent', text: "Backend connection error. Make sure it's running." }]);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return '#22c55e';
    if (score >= 45) return '#3b82f6';
    if (score >= 25) return '#f59e0b';
    return '#6b7280';
  };

  const getScoreBg = (score: number) => {
    if (score >= 70) return 'rgba(34,197,94,0.15)';
    if (score >= 45) return 'rgba(59,130,246,0.15)';
    if (score >= 25) return 'rgba(245,158,11,0.15)';
    return 'rgba(107,114,128,0.15)';
  };

  return (
    <div className="app-layout">
      {/* LEFT SIDEBAR */}
      <motion.aside initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="glass sidebar">
        <div className="brand">
          <Zap size={28} color="#3b82f6" />
          <span>InternPilot</span>
        </div>

        {/* Upload Section */}
        <div className="profile-section">
          <h3><Upload size={16} /> Resume Upload</h3>
          <label className="upload-btn" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '20px', border: '2px dashed rgba(59,130,246,0.4)', borderRadius: '12px', transition: 'border-color 0.2s' }}>
            <Upload size={28} color="var(--accent)" />
            <span style={{ fontSize: '0.9rem' }}>Drop resume here</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>PDF, TXT supported</span>
            <input type="file" accept=".pdf,.txt,.docx" style={{ display: 'none' }} onChange={handleFileUpload} />
          </label>
        </div>

        {/* Extracted Profile */}
        {profile && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="profile-section" style={{ marginTop: '16px' }}>
            <h3><Target size={16} /> Extracted Profile</h3>
            {profile.name && <p style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '6px' }}>{profile.name}</p>}
            {profile.cgpa && <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}><GraduationCap size={12} /> CGPA: {profile.cgpa}</p>}

            {profile.skills.length > 0 && (
              <div style={{ marginBottom: '12px' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Skills ({profile.skills.length})</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {profile.skills.slice(0, 20).map((s, i) => (
                    <span key={i} style={{ fontSize: '0.7rem', background: 'rgba(59,130,246,0.2)', color: '#93c5fd', padding: '2px 8px', borderRadius: '10px' }}>{s}</span>
                  ))}
                  {profile.skills.length > 20 && <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>+{profile.skills.length - 20} more</span>}
                </div>
              </div>
            )}

            {profile.inferred_roles.length > 0 && (
              <div style={{ marginBottom: '12px' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Target Roles</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {profile.inferred_roles.map((r, i) => (
                    <span key={i} style={{ fontSize: '0.75rem', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <ChevronRight size={10} /> {r}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <button onClick={handleRunPipeline} disabled={status === 'pipeline_running'}
              style={{ width: '100%', padding: '10px', background: status === 'pipeline_running' ? '#4b5563' : 'var(--accent)', color: 'white', border: 'none', borderRadius: '8px', cursor: status === 'pipeline_running' ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              {status === 'pipeline_running' ? <><Loader2 size={14} className="spinner" /> Running...</> : <><Search size={14} /> Find Internships</>}
            </button>
          </motion.div>
        )}
      </motion.aside>

      {/* CENTER — Chat + Agent Trace */}
      <motion.main initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass chat-container">
        <div className="chat-header">
          <Bot size={22} color="var(--accent)" />
          <h2>Agent Console</h2>
          {agentTrace.length > 0 && (
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
              <button onClick={() => setActiveTab('recommendations')}
                style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '6px', border: 'none', cursor: 'pointer', background: activeTab === 'recommendations' ? 'var(--accent)' : 'rgba(255,255,255,0.1)', color: 'white' }}>
                Chat
              </button>
              <button onClick={() => setActiveTab('trace')}
                style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '6px', border: 'none', cursor: 'pointer', background: activeTab === 'trace' ? 'var(--accent)' : 'rgba(255,255,255,0.1)', color: 'white' }}>
                Agent Trace ({agentTrace.length})
              </button>
            </div>
          )}
        </div>

        {activeTab === 'recommendations' ? (
          <>
            <div className="chat-messages">
              <AnimatePresence>
                {messages.map((msg) => (
                  <motion.div key={msg.id} initial={{ opacity: 0, y: 10, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} className={`message ${msg.type}`}>
                    <div className="avatar">
                      {msg.type === 'agent' ? <Bot size={18} color="white" /> : <User size={18} color="white" />}
                    </div>
                    <div className="bubble">
                      {msg.type === 'agent' ? <ReactMarkdown>{msg.text}</ReactMarkdown> : msg.text}
                    </div>
                  </motion.div>
                ))}
                {status === 'pipeline_running' && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="message agent">
                    <div className="avatar"><Bot size={18} color="white" /></div>
                    <div className="bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Loader2 size={14} className="spinner" /> Agents working: Coordinator → Discovery → Eligibility...
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={chatEndRef} />
            </div>

            <div className="chat-input-wrapper">
              <form className="chat-input" onSubmit={handleSend}>
                <input type="text" placeholder="Ask about skills, career paths, or type 'find internships'..." value={inputText} onChange={(e) => setInputText(e.target.value)} />
                <button type="submit"><Send size={16} /></button>
              </form>
            </div>
          </>
        ) : (
          /* Agent Trace Panel */
          <div className="chat-messages" style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
            {agentTrace.map((entry, i) => {
              const isCoord = entry.startsWith('Coordinator');
              const isDisc = entry.startsWith('Discovery');
              const isElig = entry.startsWith('Eligibility');
              const color = isCoord ? '#f59e0b' : isDisc ? '#3b82f6' : isElig ? '#22c55e' : '#9ca3af';
              const icon = isCoord ? '🎯' : isDisc ? '🔍' : isElig ? '✅' : '📋';
              return (
                <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                  style={{ padding: '8px 12px', borderLeft: `3px solid ${color}`, marginBottom: '4px', background: 'rgba(255,255,255,0.03)', borderRadius: '0 6px 6px 0' }}>
                  <span>{icon} </span>
                  <span style={{ color }}>{entry}</span>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.main>

      {/* RIGHT SIDEBAR — Recommendations */}
      <motion.aside initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="glass opp-panel">
        <div className="opp-header">
          <h2><Award size={18} /> Recommendations</h2>
          {status === 'completed' && recommendations.length > 0 && (
            <span style={{ fontSize: '0.75rem', color: '#22c55e' }}>{recommendations.length} matches</span>
          )}
        </div>
        <div className="opp-list">
          {recommendations.length === 0 ? (
            <div style={{ textAlign: 'center', marginTop: '60px', color: 'var(--text-secondary)' }}>
              <Briefcase size={48} style={{ opacity: 0.15, marginBottom: '16px' }} />
              <p>Upload your resume to discover matched internships.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {recommendations.map((opp, idx) => (
                <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}
                  style={{ background: 'rgba(255,255,255,0.04)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  {/* Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1rem', lineHeight: 1.3 }}>{opp.role}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        <Briefcase size={13} /> {opp.company}
                        {opp.location && <><MapPin size={13} style={{ marginLeft: '6px' }} /> {opp.location}</>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '50px' }}>
                      <span style={{ fontSize: '1.3rem', fontWeight: 800, color: getScoreColor(opp.match_score) }}>{opp.match_score}%</span>
                      <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: getScoreColor(opp.match_score), background: getScoreBg(opp.match_score), padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>{opp.eligibility}</span>
                    </div>
                  </div>

                  {/* Matched Skills */}
                  {opp.matched_skills?.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
                        {opp.matched_skills.slice(0, 6).map((s, i) => (
                          <span key={i} style={{ fontSize: '0.65rem', background: 'rgba(34,197,94,0.2)', color: '#86efac', padding: '2px 7px', borderRadius: '8px' }}>✓ {s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Skills */}
                  {opp.missing_skills?.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
                        {opp.missing_skills.slice(0, 4).map((s, i) => (
                          <span key={i} style={{ fontSize: '0.65rem', background: 'rgba(245,158,11,0.15)', color: '#fbbf24', padding: '2px 7px', borderRadius: '8px' }}>△ {s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Rationale */}
                  {opp.rationale && (
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '8px 0', lineHeight: 1.4, fontStyle: 'italic' }}>
                      "{opp.rationale}"
                    </p>
                  )}

                  {/* Source + Apply */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
                    <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', background: 'rgba(255,255,255,0.08)', padding: '3px 8px', borderRadius: '4px', color: 'var(--text-secondary)' }}>
                      {opp.source}
                    </span>
                    {opp.application_url ? (
                      <a href={opp.application_url} target="_blank" rel="noreferrer"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'var(--accent)', color: 'white', padding: '6px 14px', borderRadius: '6px', textDecoration: 'none', fontSize: '0.8rem', fontWeight: 600 }}>
                        <ExternalLink size={12} /> Apply
                      </a>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>No link</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.aside>
    </div>
  );
}

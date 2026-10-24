import { useState, useEffect, useRef } from 'react';
import {
  Upload, Send, Briefcase, MapPin, Loader2, ExternalLink,
  Search, ChevronRight, GraduationCap, FileText, Activity,
  MessageSquare, Check, AlertCircle, Building2, RefreshCw
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API = 'http://localhost:8000/api/v1';

interface ProjectItem {
  name: string;
  description?: string;
  technologies?: string[];
}

interface ParsedProfile {
  resume_id?: string;
  name?: string;
  email?: string;
  skills: string[];
  skills_display?: string[];
  inferred_roles: string[];
  education: any[];
  cgpa?: number;
  projects: ProjectItem[];
  experience: string[];
}

interface Recommendation {
  rank?: number;
  opportunity_id?: string;
  company: string;
  role: string;
  role_category?: string;
  location?: string;
  work_mode?: string;
  stipend?: string;
  stipend_numeric?: number;
  duration?: string;
  description: string;
  application_url?: string;
  source: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  eligibility: string;
  rationale: string;
}

interface ChatItem {
  id: number;
  type: 'agent' | 'user';
  text: string;
}

const SUGGESTED_PROMPTS = [
  "Which one pays me well?",
  "The 2nd one gives how much stipend?",
  "Is the 1st one a full stack role?",
  "Compare #1 and #2 for my profile",
  "What skills am I missing for #3?"
];

export function App() {
  const [messages, setMessages] = useState<ChatItem[]>([
    {
      id: 1,
      type: 'agent',
      text: "Welcome to **InternPilot**. Upload your resume (`.pdf` or `.txt`) in the left panel to parse your technical profile and fetch live internship opportunities via the API & MCP connector. Once loaded, you can ask questions about any numbered listing (`#1`, `#2`, `#3`...), compare stipends, or check role requirements."
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [profile, setProfile] = useState<ParsedProfile | null>(null);
  const [resumeId, setResumeId] = useState<string | undefined>(undefined);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [agentTrace, setAgentTrace] = useState<string[]>([]);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'pipeline_running' | 'completed' | 'failed'>('idle');
  const [sessionId, setSessionId] = useState<string>('session-portal-101');
  const [studentId] = useState('student-live-101');
  const [activeTab, setActiveTab] = useState<'chat' | 'trace'>('chat');
  const [selectedRank, setSelectedRank] = useState<number | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const executeDiscovery = async (uploadedResumeId?: string, parsedProfile?: ParsedProfile) => {
    setStatus('pipeline_running');
    try {
      const res = await fetch(`${API}/workflows/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          resume_id: uploadedResumeId || resumeId,
          session_id: sessionId
        })
      });
      if (!res.ok) throw new Error('Workflow request failed');
      const data = await res.json();

      const recs: Recommendation[] = data.recommendations || [];
      const trace: string[] = data.agent_trace || [];
      setRecommendations(recs);
      setAgentTrace(trace);
      if (data.resume_profile && !parsedProfile) {
        setProfile(data.resume_profile);
      }
      setStatus('completed');

      if (recs.length > 0) {
        const top1 = recs[0];
        const highestPay = [...recs].sort((a, b) => (b.stipend_numeric || 0) - (a.stipend_numeric || 0))[0];
        setMessages(prev => [
          ...prev,
          {
            id: Date.now(),
            type: 'agent',
            text:
              `Fetched and ranked **${recs.length} live internship listings** (` +
              `\`#1\` to \`#${recs.length}\`) via the MCP API Connector:\n\n` +
              `- **Top Match (#1):** ${top1.role} at **${top1.company}** — **${top1.match_score}% Match** (${top1.stipend || 'Competitive'})\n` +
              `- **Highest Stipend (#${highestPay.rank || 1}):** ${highestPay.role} at **${highestPay.company}** — **${highestPay.stipend}**\n\n` +
              `You can ask about any numbered card on the right (for example: *"The 2nd one gives how much stipend?"* or *"Is the 1st one a full stack role?"*).`
          }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          { id: Date.now(), type: 'agent', text: 'Discovery finished, but no live API listings were returned for this query.' }
        ]);
      }
    } catch (err) {
      console.error(err);
      setStatus('failed');
      setMessages(prev => [
        ...prev,
        { id: Date.now(), type: 'agent', text: 'Unable to complete opportunity discovery. Please verify the backend server and API credentials.' }
      ]);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setStatus('uploading');
    setMessages(prev => [
      ...prev,
      { id: Date.now(), type: 'agent', text: `Uploading and extracting profile from **${file.name}**...` }
    ]);

    const formData = new FormData();
    formData.append('student_id', studentId);
    formData.append('session_id', sessionId);
    formData.append('file', file);

    try {
      const response = await fetch(`${API}/resumes/upload`, { method: 'POST', body: formData });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed (${response.status})`);
      }
      const data = await response.json();

      const parsed: ParsedProfile = data.parsed_profile;
      setProfile(parsed);
      setResumeId(data.resume_id);

      const skillList = parsed?.skills_display || parsed?.skills || [];
      const roleList = parsed?.inferred_roles || [];

      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'agent',
          text:
            `Profile extracted for **${parsed?.name || 'Candidate'}** (${skillList.length} technical skills, ${roleList.length} role tracks). Querying live internship providers via MCP...`
        }
      ]);

      await executeDiscovery(data.resume_id, parsed);
    } catch (error: any) {
      console.error(error);
      setStatus('failed');
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'agent',
          text: `Failed to process **${file.name}**: ${error?.message || 'Check backend server status.'}`
        }
      ]);
    } finally {
      e.target.value = '';
    }
  };

  const sendQuery = async (queryText: string) => {
    if (!queryText.trim() || isSending) return;
    const text = queryText.trim();
    setActiveTab('chat');
    setMessages(prev => [...prev, { id: Date.now(), type: 'user', text }]);
    setInputText('');
    setIsSending(true);

    try {
      const res = await fetch(`${API}/agent/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          student_id: studentId,
          resume_id: resumeId
        })
      });
      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);
      if (data.opportunities && data.opportunities.length > 0) {
        setRecommendations(data.opportunities);
      }
      if (data.resume_profile && !profile) {
        setProfile(data.resume_profile);
      }
      if (data.agent_trace && data.agent_trace.length > 0) {
        setAgentTrace(data.agent_trace);
      }
      setMessages(prev => [
        ...prev,
        { id: Date.now(), type: 'agent', text: data.response || "Request processed." }
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        { id: Date.now(), type: 'agent', text: "Connection error. Please ensure the backend server is running on port 8000." }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendQuery(inputText);
  };

  const displaySkills = profile?.skills_display || profile?.skills || [];

  return (
    <div className="portal-shell">
      {/* TOP NAVIGATION BAR */}
      <header className="portal-topbar">
        <div className="topbar-brand">
          <div className="brand-mark">IP</div>
          <div>
            <h1>InternPilot</h1>
            <span>Candidate Placement & Opportunity Portal</span>
          </div>
        </div>
        <div className="topbar-status">
          <span className="status-indicator">
            <span className={`dot ${status === 'pipeline_running' ? 'amber' : 'green'}`} />
            MCP & Live API Connected
          </span>
        </div>
      </header>

      {/* MAIN 3-COLUMN WORKSPACE */}
      <div className="portal-grid">
        {/* LEFT PANEL: Candidate Resume & Extracted Profile */}
        <aside className="panel sidebar-panel">
          <div className="panel-header">
            <h2><FileText size={16} /> Candidate Profile</h2>
          </div>

          <div className="panel-body">
            <label className="upload-box">
              <Upload size={20} className="upload-icon" />
              <span className="upload-title">
                {status === 'uploading' ? 'Parsing Resume...' : 'Upload Resume'}
              </span>
              <span className="upload-subtitle">PDF or TXT format (Max 10MB)</span>
              <input
                type="file"
                accept=".pdf,.txt,.docx"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
                disabled={status === 'uploading' || status === 'pipeline_running'}
              />
            </label>

            {profile ? (
              <div className="profile-details">
                <div className="candidate-header-card">
                  <div className="candidate-name">{profile.name || 'Candidate'}</div>
                  {profile.email && <div className="candidate-email">{profile.email}</div>}
                  {profile.cgpa && (
                    <div className="cgpa-badge">
                      <GraduationCap size={13} /> CGPA: {profile.cgpa} / 10
                    </div>
                  )}
                </div>

                {displaySkills.length > 0 && (
                  <div className="profile-block">
                    <div className="block-label">Technical Skills ({displaySkills.length})</div>
                    <div className="tag-cloud">
                      {displaySkills.slice(0, 24).map((s, i) => (
                        <span key={i} className="tech-chip">{s}</span>
                      ))}
                      {displaySkills.length > 24 && (
                        <span className="tech-chip muted">+{displaySkills.length - 24} more</span>
                      )}
                    </div>
                  </div>
                )}

                {profile.inferred_roles?.length > 0 && (
                  <div className="profile-block">
                    <div className="block-label">Eligible Role Tracks</div>
                    <ul className="role-track-list">
                      {profile.inferred_roles.map((r, i) => (
                        <li key={i}><ChevronRight size={13} /> {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {profile.projects?.length > 0 && (
                  <div className="profile-block">
                    <div className="block-label">Key Projects ({profile.projects.length})</div>
                    <div className="project-list">
                      {profile.projects.slice(0, 4).map((p, i) => (
                        <div key={i} className="project-item">
                          <div className="project-title">{p.name}</div>
                          {p.technologies && p.technologies.length > 0 && (
                            <div className="project-tech">{p.technologies.slice(0, 5).join(', ')}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => executeDiscovery(resumeId, profile)}
                  disabled={status === 'pipeline_running'}
                  className="btn-secondary-full"
                >
                  {status === 'pipeline_running' ? (
                    <><Loader2 size={14} className="spin" /> Fetching Live Listings...</>
                  ) : (
                    <><RefreshCw size={14} /> Refresh Opportunities</>
                  )}
                </button>
              </div>
            ) : (
              <div className="empty-hint">
                Upload a resume to automatically extract skills, academic metrics, and match live internships.
              </div>
            )}
          </div>
        </aside>

        {/* CENTER PANEL: Career Advisor Query Console & MCP Activity Log */}
        <main className="panel center-panel">
          <div className="panel-header">
            <div>
              <h2><MessageSquare size={16} /> Career Advisor & Query Console</h2>
            </div>
            <div className="tab-group">
              <button
                type="button"
                onClick={() => setActiveTab('chat')}
                className={`tab-pill ${activeTab === 'chat' ? 'active' : ''}`}
              >
                Query Console
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('trace')}
                className={`tab-pill ${activeTab === 'trace' ? 'active' : ''}`}
              >
                <Activity size={12} /> MCP & System Log ({agentTrace.length})
              </button>
            </div>
          </div>

          {activeTab === 'chat' ? (
            <>
              <div className="conversation-stream">
                {messages.map((msg) => (
                  <div key={msg.id} className={`chat-row ${msg.type}`}>
                    <div className="chat-sender-label">
                      {msg.type === 'agent' ? 'Advisor' : 'You'}
                    </div>
                    <div className="chat-card">
                      {msg.type === 'agent' ? <ReactMarkdown>{msg.text}</ReactMarkdown> : msg.text}
                    </div>
                  </div>
                ))}

                {(status === 'pipeline_running' || isSending) && (
                  <div className="chat-row agent">
                    <div className="chat-sender-label">Advisor</div>
                    <div className="chat-card loading-row">
                      <Loader2 size={15} className="spin" />
                      <span>
                        {status === 'pipeline_running'
                          ? 'Querying live APIs via MCP and scoring eligibility...'
                          : 'Analyzing your question against resume and internship data...'}
                      </span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {recommendations.length > 0 && (
                <div className="prompt-bar">
                  <span className="prompt-bar-label">Quick Queries:</span>
                  <div className="prompt-pills">
                    {SUGGESTED_PROMPTS.map((q, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className="prompt-pill"
                        onClick={() => sendQuery(q)}
                        disabled={isSending}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <form className="query-form" onSubmit={handleSend}>
                <input
                  type="text"
                  placeholder="Ask about stipends, #1 or #2 details, full-stack roles, or missing skills..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isSending}
                />
                <button type="submit" disabled={isSending || !inputText.trim()}>
                  <Send size={15} /> Send
                </button>
              </form>
            </>
          ) : (
            <div className="log-stream">
              {agentTrace.length === 0 ? (
                <div className="empty-hint">
                  No workflow logs recorded yet. Upload a resume to view MCP and API execution logs.
                </div>
              ) : (
                agentTrace.map((entry, i) => (
                  <div key={i} className="log-item">
                    <span className="log-index">{String(i + 1).padStart(2, '0')}</span>
                    <span className="log-text">{entry}</span>
                  </div>
                ))
              )}
            </div>
          )}
        </main>

        {/* RIGHT PANEL: Ranked Live Internships (#1..#N) */}
        <aside className="panel listings-panel">
          <div className="panel-header">
            <h2><Briefcase size={16} /> Matched Internships</h2>
            {recommendations.length > 0 && (
              <span className="count-badge">{recommendations.length} Live Matches</span>
            )}
          </div>

          <div className="listings-scroll">
            {recommendations.length === 0 ? (
              <div className="empty-listings">
                <Search size={36} className="empty-icon" />
                <p className="empty-title">No Internships Loaded</p>
                <p className="empty-desc">
                  Upload your resume on the left to fetch and score live internships via the MCP API Connector.
                </p>
              </div>
            ) : (
              recommendations.map((opp, idx) => {
                const rankNum = opp.rank || idx + 1;
                const isSelected = selectedRank === rankNum;
                const scoreClass =
                  opp.match_score >= 70 ? 'score-high' : opp.match_score >= 45 ? 'score-mid' : 'score-low';

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedRank(rankNum)}
                    className={`listing-card ${isSelected ? 'selected' : ''}`}
                  >
                    <div className="listing-top">
                      <div className="listing-title-group">
                        <span className="listing-rank">#{rankNum}</span>
                        <div>
                          <h3 className="listing-role">{opp.role}</h3>
                          <div className="listing-company">
                            <Building2 size={13} />
                            <span>{opp.company}</span>
                            {opp.location && (
                              <>
                                <span className="sep">•</span>
                                <MapPin size={12} />
                                <span>{opp.location}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className={`score-pill ${scoreClass}`}>
                        <span className="score-num">{opp.match_score}%</span>
                        <span className="score-label">{opp.eligibility}</span>
                      </div>
                    </div>

                    {/* Stipend, Category & Work Mode Metadata */}
                    <div className="listing-meta-row">
                      {opp.stipend && (
                        <span className="badge badge-stipend">{opp.stipend}</span>
                      )}
                      {opp.role_category && (
                        <span className="badge badge-category">{opp.role_category}</span>
                      )}
                      {opp.work_mode && (
                        <span className="badge badge-mode">{opp.work_mode.toUpperCase()}</span>
                      )}
                    </div>

                    {/* Matched Skills */}
                    {opp.matched_skills?.length > 0 && (
                      <div className="skill-group">
                        <div className="skill-pills">
                          {opp.matched_skills.slice(0, 6).map((s, i) => (
                            <span key={i} className="pill-match">
                              <Check size={10} /> {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Skills */}
                    {opp.missing_skills?.length > 0 && (
                      <div className="skill-group">
                        <div className="skill-pills">
                          {opp.missing_skills.slice(0, 4).map((s, i) => (
                            <span key={i} className="pill-gap">
                              <AlertCircle size={10} /> {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Rationale */}
                    {opp.rationale && (
                      <p className="listing-rationale">{opp.rationale}</p>
                    )}

                    {/* Footer */}
                    <div className="listing-footer">
                      <span className="source-tag">
                        {opp.source === 'mock' ? 'Verified Listing' : opp.source}
                      </span>

                      <div className="footer-actions">
                        <button
                          type="button"
                          className="btn-ask"
                          onClick={(e) => {
                            e.stopPropagation();
                            sendQuery(`Give me a full breakdown of internship #${rankNum} (${opp.role} at ${opp.company}), including stipend and whether it fits my resume.`);
                          }}
                        >
                          Ask about #{rankNum}
                        </button>

                        {opp.application_url && (
                          <a
                            href={opp.application_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="btn-apply"
                          >
                            Apply <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
import { useState } from 'react';
import { Upload, Send, Bot, User, Briefcase, MapPin, DollarSign } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function App() {
  const [messages, setMessages] = useState([
    { id: 1, type: 'agent', text: "Hello! I'm InternPilot. I can help you find, evaluate, and apply to internships. Have you uploaded your resume yet?" }
  ]);
  const [inputText, setInputText] = useState('');

  const [sessionId, setSessionId] = useState<string | undefined>(undefined);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    
    const textToSend = inputText;
    setMessages(prev => [...prev, { id: Date.now(), type: 'user', text: textToSend }]);
    setInputText('');
    
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
      
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        type: 'agent', 
        text: data.response || "Sorry, I couldn't understand that."
      }]);
    } catch (error) {
      console.error('Error communicating with backend:', error);
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
        text: `Successfully uploaded ${file.name} and extracted your profile. I am now proactively searching for opportunities that match your skills...` 
      }]);
      
      // Proactively trigger the agent to search for jobs based on the new resume
      try {
        const agentResponse = await fetch('http://localhost:8000/api/v1/agent/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: "I just uploaded my resume. Please search for internships that match my skills.", session_id: sessionId, student_id: 'demo-student-123' })
        });
        const agentData = await agentResponse.json();
        if (agentData.session_id && !sessionId) {
          setSessionId(agentData.session_id);
        }
        setMessages(prev => [...prev, { 
          id: Date.now(), 
          type: 'agent', 
          text: agentData.response || "I couldn't find any matching opportunities right now."
        }]);
      } catch (err) {
        console.error('Proactive search failed:', err);
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
                  {msg.text}
                </div>
              </motion.div>
            ))}
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
        </div>
        <div className="opp-list">
          <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--text-secondary)' }}>
            <Briefcase size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
            <p>Opportunities will appear here once the agent starts searching.</p>
          </div>
        </div>
      </motion.aside>
    </div>
  );
}

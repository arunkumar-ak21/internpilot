const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function App() {
  return (
    <main>
      <p className="eyebrow">InternPilot</p>
      <h1>Your internship workflow, built one verified step at a time.</h1>
      <p className="description">
        The platform foundation is online. Profile, agent, discovery, and tracking
        capabilities will appear here as their backend milestones are verified.
      </p>
      <p className="api-status">API target: {apiBaseUrl}</p>
    </main>
  );
}

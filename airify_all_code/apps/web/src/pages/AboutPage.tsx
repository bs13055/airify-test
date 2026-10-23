export function AboutPage() {
  return (
    <div className="card">
      <h2>About Airify</h2>
      <p style={{ marginTop: 12 }}>Airify is a <strong>Personal PM2.5 Exposure Intelligence Platform</strong>.</p>
      <p style={{ marginTop: 8, fontSize: '0.9rem', color: '#555' }}>
        One shared prediction + exposure core serves several audiences. This V1 demo uses mock data
        to explore whether people find local PM2.5 exposure intelligence and practical, non-medical
        guidance useful.
      </p>

      <h3 style={{ marginTop: 16 }}>Platform paths</h3>
      <div className="platform-grid">
        <div className="platform-card">
          <span className="platform-status">Demo V1</span>
          <h4>Data for Health</h4>
          <ul>
            <li>Health App (mobile-first)</li>
            <li>PM2.5 exposure / estimated inhaled intake</li>
            <li>ADD-style daily awareness</li>
            <li>Timeline + preventive guidance</li>
          </ul>
        </div>
        <div className="platform-card">
          <span className="platform-status">Demo V1</span>
          <h4>Data for Developer</h4>
          <ul>
            <li>Developer Portal</li>
            <li>API Playground + sample response</li>
            <li>Model Hub</li>
            <li>Dataset Catalog</li>
          </ul>
        </div>
        <div className="platform-card">
          <span className="platform-status">Future</span>
          <h4>Data for City · Research · Validation</h4>
          <ul>
            <li>Data for City (planned)</li>
            <li>Data for Research (planned)</li>
            <li>Validation Evidence (MAE/RMSE — pending)</li>
          </ul>
        </div>
      </div>

      <h3 style={{ marginTop: 16 }}>What this is</h3>
      <ul style={{ marginTop: 8, paddingLeft: 20, fontSize: '0.85rem', color: '#555' }}>
        <li>General environmental guidance</li>
        <li>PM2.5 risk awareness tool</li>
        <li>Product feedback prototype</li>
        <li>A/B testing platform</li>
      </ul>
      <h3 style={{ marginTop: 16 }}>What this is NOT</h3>
      <ul style={{ marginTop: 8, paddingLeft: 20, fontSize: '0.85rem', color: '#555' }}>
        <li>Not medical advice or diagnosis</li>
        <li>Not a validated prediction engine</li>
        <li>Not official pollution authority data</li>
        <li>Not production ready</li>
      </ul>
      <div className="disclaimer" style={{ marginTop: 16 }}>
        <p>This version uses mock data only. Live provider integration is not implemented.
        PM2.5 prediction is not implemented. This is not medical advice.</p>
      </div>
    </div>
  );
}

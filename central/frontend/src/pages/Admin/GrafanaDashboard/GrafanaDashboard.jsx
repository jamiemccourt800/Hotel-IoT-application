const GrafanaDashboard = () => {
  const baseUrl = process.env.REACT_APP_GRAFANA_URL || "http://localhost:3000";

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      <iframe
        src={`${baseUrl}/d-solo/6f573f89-9000-43f7-9459-2b5817b8abe8/temperature-overview?orgId=1&panelId=1&from=now-6h&to=now&theme=light`}
        title="Temperature Overview"
        width="100%"
        height="350"
        frameBorder="0"
      />

      <iframe
        src={`${baseUrl}/d-solo/adqhlmx/light-brightness-overview?orgId=1&from=1764604263660&to=1764625863660&timezone=browser&panelId=panel-1&__feature.dashboardSceneSolo=true`}
         width="100%" height="350" frameborder="0"
      />
      
      <iframe 
        src={`${baseUrl}/d-solo/adqhlmx/light-brightness-overview?orgId=1&from=1764604263660&to=1764625863660&timezone=browser&panelId=panel-2&__feature.dashboardSceneSolo=true`}
         width="100%" height="350" frameborder="0"
      />
    </div>
  )
}

export default GrafanaDashboard;

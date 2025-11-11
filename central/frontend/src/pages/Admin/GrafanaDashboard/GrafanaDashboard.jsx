import React from 'react'

const GrafanaDashboard = () => {
  return (
    <div style={{height: "80vh"}}>
         <iframe
        src="http://localhost:3000/d/6f573f89-9000-43f7-9459-2b5817b8abe8/temperature-overview?orgId=1&from=now-6h&to=now&timezone=browser&refresh=5s&kiosk"
        title="Temperature Overview"
        width="100%"
        height="100%"
        frameBorder="0"
      />
    </div>
  )
}

export default GrafanaDashboard

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
// Ant Design CSS'i şu şekilde import et (yeni sürümlerde)
import 'antd/dist/antd'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
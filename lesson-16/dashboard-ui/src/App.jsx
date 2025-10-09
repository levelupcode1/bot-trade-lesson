/**
 * Main App Component
 * Figma 디자인을 실제 동작하는 React 앱으로 구현
 */

import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <div className="app">
      <Dashboard />
    </div>
  );
}

export default App;


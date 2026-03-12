import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { CaseForm } from "./pages/CaseForm";

interface ApiResponse {
  message: string;
}

function App() {
  const [message, setMessage] = useState("");

  // TODO: remove after backend and database set-up
  useEffect(() => {
    fetch("http://localhost:8000")
      .then(res => res.json())
      .then((data: ApiResponse) => setMessage(data.message));
  }, []);

  const mainPage = (
    <div>
      <h1>TRIBOT</h1>
      <p>{message}</p>
    </div>
  );

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={mainPage} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/new-case" element={<CaseForm />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { CaseForm } from "./pages/CaseForm";
import Layout from "./Layout";

interface ApiResponse {
  message: string;
}

function App() {
  // TODO: remove after backend and database set-up
  useEffect(() => {
    fetch("http://localhost:8000")
      .then(res => res.json())
      .then((data: ApiResponse) => console.log(data.message));
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="new-case" element={<CaseForm />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

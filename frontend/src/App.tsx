import { useEffect, useState } from "react";

interface ApiResponse {
  message: string;
}

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000")
      .then(res => res.json())
      .then((data: ApiResponse) => setMessage(data.message));
  }, []);

  return (
    <div>
      <h1>TRIBOT</h1>
      <p>{message}</p>
    </div>
  );
}

export default App;

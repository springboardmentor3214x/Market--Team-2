import { useEffect, useState } from "react";
import api from "../services/api";

function ResearchHistory() {

  const [history, setHistory] = useState([]);

  useEffect(() => {

    api.get("/research-history")
      .then(response => {
        setHistory(response.data);
      })
      .catch(error => {
        console.log(error);
      });

  }, []);

  return (
    <div>
      <h2>Research History</h2>

      {history.map((item) => (
        <div key={item.id}>
          <h3>{item.company_name}</h3>
          <p>{item.stock_symbol}</p>
          <p>{item.created_at}</p>
        </div>
      ))}

    </div>
  );
}

export default ResearchHistory;
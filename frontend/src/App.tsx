import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import AuditPage from "./pages/AuditPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/audit/:taskId" element={<AuditPage />} />
      </Routes>
    </Layout>
  );
}

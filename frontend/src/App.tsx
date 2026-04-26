import { ReactElement } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { CaseForm } from "./pages/CaseForm";
import { LoginPage } from "./pages/LoginPage";
import Layout from "./Layout";
import { UserRole } from "./types/user";
import { getDecodedToken, isAuthenticated } from "./utils/auth";
import { UsersTable } from "./components/UsersTable";
import { Metrics } from "./pages/Metrics";

const RoleRestriction = ({ role, children }: { role: UserRole, children: ReactElement }): ReactElement => {
  if (getDecodedToken()?.role !== role) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

const RequireAuth = (): ReactElement => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

const RedirectIfAuthenticated = ({ children }: { children: ReactElement }): ReactElement => {
  if (isAuthenticated()) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

const HomeRedirect = (): ReactElement => (
  <Navigate to={isAuthenticated() ? "/dashboard" : "/login"} replace />
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={(
            <RedirectIfAuthenticated>
              <LoginPage />
            </RedirectIfAuthenticated>
          )}
        />
        <Route element={<RequireAuth />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/new-case" element={<RoleRestriction role={UserRole.Clinician}><CaseForm /></RoleRestriction>} />
            <Route path="/users" element={<RoleRestriction role={UserRole.Admin}><UsersTable /></RoleRestriction>} />
            <Route path="/metrics" element={<RoleRestriction role={UserRole.Researcher}><Metrics /></RoleRestriction>} />
          </Route>
        </Route>

        <Route path="/" element={<HomeRedirect />} />
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

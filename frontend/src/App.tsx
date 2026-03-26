import { ReactElement } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { CaseForm } from "./pages/CaseForm";
import { LoginPage } from "./pages/LoginPage";
import { CreateAccountPage } from "./pages/CreateAccountPage";
import Layout from "./Layout";

const isAuthenticated = (): boolean => Boolean(localStorage.getItem("access_token"));

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
        <Route
          path="/create-account"
          element={(
            <RedirectIfAuthenticated>
              <CreateAccountPage />
            </RedirectIfAuthenticated>
          )}
        />

        <Route element={<RequireAuth />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/new-case" element={<CaseForm />} />
          </Route>
        </Route>

        <Route path="/" element={<HomeRedirect />} />
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

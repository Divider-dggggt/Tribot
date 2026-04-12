import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider } from "@mui/material/styles";
import App from "./App";
import { Provider } from "react-redux";
import { store } from "./store";
import { appTheme } from "./theme";

ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
).render(
  <Provider store={store}>
    <ThemeProvider theme={appTheme}>
      <App />
    </ThemeProvider>
  </Provider>
);

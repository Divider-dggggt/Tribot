import { PropsWithChildren, ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { ThemeProvider } from "@mui/material/styles";
import { Provider } from "react-redux";
import { store } from "../src/store";
import { appTheme } from "../src/theme";

const AllProviders = ({ children }: PropsWithChildren): ReactElement => (
  <Provider store={store}>
    <ThemeProvider theme={appTheme}>
      {children}
    </ThemeProvider>
  </Provider>
);

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: AllProviders, ...options });

export * from "@testing-library/react";
export { customRender as render };

# Frontend File Structure

```text
frontend/                                                # frontend application root
├── src/                                                 # production source code
│   ├── App.tsx                                          # router entry and auth guards
│   ├── Layout.tsx                                       # global layout shell
│   ├── main.tsx                                         # React bootstrap entry
│   ├── theme.ts                                         # global MUI theme
│   ├── components/                                      # reusable UI/business components
│   │   ├── AuthLogo.tsx                                 # auth page brand logo
│   │   ├── AuthTransitionOverlay.tsx                    # auth loading transition overlay
│   │   ├── BrandIcon.tsx                                # reusable brand icon
│   │   ├── CaseSummary.tsx                              # case detail and triage summary view
│   │   ├── CreateUserForm.tsx                           # create-user dialog form
│   │   ├── DeleteUserConfirmation.tsx                   # deactivate-user confirmation dialog
│   │   ├── EditUserForm.tsx                             # edit-user dialog form
│   │   ├── FloatingTextField.tsx                        # shared text-field wrapper
│   │   ├── OverrideDialog.tsx                           # ATS override dialog
│   │   ├── PasswordField.tsx                            # password input with visibility toggle
│   │   ├── ResetPasswordDialog.tsx                      # reset-password dialog
│   │   ├── UndoOverrideDialog.tsx                       # undo-override dialog
│   │   └── UsersTable.tsx                               # user management table
│   ├── pages/                                           # route-level page modules
│   │   ├── CaseForm.tsx                                 # submit new triage case
│   │   ├── Dashboard.tsx                                # dashboard and case listing
│   │   ├── LoginPage.tsx                                # user sign-in page
│   │   └── Metrics.tsx                                  # model metrics page
│   ├── types/                                           # TypeScript domain models
│   │   ├── case.ts                                      # case-related types
│   │   ├── triage.ts                                    # triage-related types
│   │   └── user.ts                                      # user and role types
│   └── utils/                                           # shared helper functions/constants
│       ├── auth.ts                                      # auth/session/token helpers
│       ├── buttonStyles.ts                              # shared button style tokens
│       ├── color.ts                                     # color mapping helpers
│       ├── constants.ts                                 # API and app constants
│       ├── date.ts                                      # date format and parse helpers
│       └── layout.ts                                    # shared layout constants
├── test/                                                # automated tests
│   ├── auth-helpers.ts                                  # auth setup helpers for tests
│   ├── setup.ts                                         # Vitest global setup
│   ├── test-utils.tsx                                   # shared test render helpers
│   ├── components/                                      # component test specs
│   │   ├── AuthLogo.test.tsx                            # AuthLogo component tests
│   │   ├── PasswordField.test.tsx                       # PasswordField component tests
│   │   └── UsersTable.test.tsx                          # UsersTable component tests
│   ├── pages/                                           # page test specs
│   │   ├── CaseForm.test.tsx                            # CaseForm page tests
│   │   ├── Dashboard.test.tsx                           # Dashboard page tests
│   │   └── LoginPage.test.tsx                           # LoginPage page tests
│   └── e2e/                                             # Playwright end-to-end tests
│       ├── auth.spec.ts                                 # auth flow E2E scenarios
│       ├── case-summary-override.spec.ts                # case summary and override scenarios
│       ├── coverage-fixture.ts                          # E2E coverage collection fixture
│       ├── create-case.spec.ts                          # create-case E2E scenario
│       ├── helpers.ts                                   # shared E2E helper utilities
│       └── layout-account-metrics.spec.ts               # layout/account/metrics scenarios
├── public/                                              # static public assets
│   └── favicon.svg                                      # browser tab icon
├── package.json                                         # scripts and dependency declarations
├── vite.config.ts                                       # Vite + Vitest configuration
├── playwright.config.ts                                 # Playwright configuration
├── tsconfig.json                                        # TypeScript compiler config
├── Dockerfile                                           # frontend container build
└── README.md                                            # testing and usage documentation
```


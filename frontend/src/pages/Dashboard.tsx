import React, { ReactElement, useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { 
  Alert, 
  Snackbar, 
  SnackbarCloseReason, 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
} from "@mui/material";
import { ATSLevel } from "../types/triage";
import { useSelector } from "react-redux";
import { getTriageCases } from "../store/triage/triageSlice";
import { CaseSummary } from "../components/CaseSummary";
import { getPriorityColor } from "../utils/color";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import { parseCaseDateTime } from "../utils/date";
import { UserRole } from "../types/user";
import { getDecodedToken } from "../utils/auth";
import { API_BASE_URL } from "../utils/constants";
import { CaseApiResponse } from "../types/case";

// Simple Plus Icon
const PlusIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

const SortIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="4" y1="7" x2="14" y2="7"></line>
    <line x1="4" y1="12" x2="18" y2="12"></line>
    <line x1="4" y1="17" x2="10" y2="17"></line>
    <polyline points="18 5 20 3 22 5"></polyline>
    <line x1="20" y1="3" x2="20" y2="13"></line>
  </svg>
);

type SortOption = "severity" | "createdTime" | "alphabetical";

const getCaseTimestamp = (date: string, fallbackOrder: number): number => {
  const parsedTimestamp = parseCaseDateTime(date);
  return Number.isNaN(parsedTimestamp) ? fallbackOrder : parsedTimestamp;
};

const getNextSortOption = (currentSortOption: SortOption): SortOption => {
  if (currentSortOption === "severity") {
    return "createdTime";
  }
  if (currentSortOption === "createdTime") {
    return "alphabetical";
  }
  return "severity";
};

const getSortLabel = (sortOption: SortOption): string => {
  if (sortOption === "severity") {
    return "Severity Level";
  }
  if (sortOption === "createdTime") {
    return "Creation Time";
  }
  return "Alphabetical";
};

const getNameSortGroup = (name: string): number => {
  const firstChar = name.trim().charAt(0);
  if (/^[a-z]$/i.test(firstChar)) {
    return 0;
  }
  if (/^\d$/.test(firstChar)) {
    return 1;
  }
  return 2;
};

const compareCaseNameWithPriority = (aName: string, bName: string): number => {
  const aTrimmedName = aName.trim();
  const bTrimmedName = bName.trim();
  const groupDifference = getNameSortGroup(aTrimmedName) - getNameSortGroup(bTrimmedName);

  if (groupDifference !== 0) {
    return groupDifference;
  }

  return aTrimmedName.localeCompare(bTrimmedName, undefined, {
    sensitivity: "base",
    numeric: true,
  });
};

export const Dashboard = (): ReactElement => {
  const location = useLocation();
  const navigate = useNavigate();
  const signedInAccount = localStorage.getItem("user_email") ?? "Dr. Smith";
  const userRole = getDecodedToken()?.role;
  const [searchParams] = useSearchParams();
  const [snackOpen, setSnackOpen] = useState<boolean>(false);
  const [snackMessage, setSnackMessage] = useState<string>("");
  const [snackSeverity, setSnackSeverity] = useState<'success' | 'info' | 'warning' | 'error'>("success");
  const [sortOption, setSortOption] = useState<SortOption>("severity");
  const [caseView, setCaseView] = useState<string>("open-cases");
  const triageCases = useSelector(getTriageCases);
  const sortedTriageCases = [...triageCases]
    .map((item, originalIndex) => ({ item, originalIndex }))
    .sort((a, b) => {
      if (sortOption === "severity") {
        return a.item.priority - b.item.priority;
      }
      if (sortOption === "createdTime") {
        const aTimestamp = getCaseTimestamp(a.item.date, a.originalIndex);
        const bTimestamp = getCaseTimestamp(b.item.date, b.originalIndex);
        return bTimestamp - aTimestamp;
      }
      const nameCompareResult = compareCaseNameWithPriority(a.item.name, b.item.name);
      return nameCompareResult !== 0 ? nameCompareResult : a.originalIndex - b.originalIndex;
    })
    .map(({ item }) => item);

  useEffect(() => {
    const fetchCases = async (): Promise<void> => {
      const accessToken = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/cases${caseView === "resolved-cases" ? "/resolved" : ""}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
      const cases = await response.json() as CaseApiResponse[];
      console.log(cases); // TODO: set state for cases and phase out redux selector
    };

    fetchCases();
  }, [caseView]);

  useEffect(() => {
    if (location.state?.message) {
      setSnackMessage(location.state.message);
      setSnackSeverity(location.state.severity || "success");
      setSnackOpen(true);
      window.history.replaceState({}, "", `${location.pathname}${location.search}`);
    }
  }, [location.pathname, location.search, location.state]);

  const handleSnackClose = (
    event?: React.SyntheticEvent | Event,
    reason?: SnackbarCloseReason,
  ) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackOpen(false);
  };

  const handleSortClick = () => {
    setSortOption((previousSortOption) => getNextSortOption(previousSortOption));
  };

  const selectedCaseIdParam = Number(searchParams.get("case"));
  const selectedCase = sortedTriageCases.find(c => c.caseId === selectedCaseIdParam);

  const successSnackbar = (
    <Snackbar open={snackOpen} autoHideDuration={4000} onClose={handleSnackClose}>
      <Alert onClose={handleSnackClose} severity={snackSeverity} sx={{ width: '100%' }}>
        {snackMessage}
      </Alert>
    </Snackbar>
  );

  if (selectedCase !== undefined) {
    return (
      <>
        <CaseSummary
          case={selectedCase}
          onBack={() => navigate("/dashboard")}
        />
        {successSnackbar}
      </>
    );
  }

  return (
    <Box sx={{ maxWidth: PAGE_CONTENT_MAX_WIDTH, mx: "auto" }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Welcome back, {signedInAccount}
        </Typography>
      </Box>

      {userRole === UserRole.Clinician && <Button 
        variant="contained" 
        fullWidth 
        size="large"
        onClick={() => navigate('/new-case')}
        sx={{ 
          bgcolor: '#9333ea', // Purple-600
          '&:hover': { bgcolor: '#7e22ce' }, // Purple-700
          py: 2,
          mb: 4,
          borderRadius: 2,
          textTransform: 'none',
          fontSize: '1.1rem',
          fontWeight: 'bold'
        }}
      >
        <PlusIcon />
        Create New Case
      </Button>}

      <ToggleButtonGroup
        value={caseView}
        onChange={(e: React.MouseEvent<HTMLElement>, newCaseView: string | null) => {
          if (newCaseView === null) return;
          setCaseView(newCaseView);
        }}
        exclusive
      >
        <ToggleButton value="open-cases">
          Open
        </ToggleButton>
        <ToggleButton value="resolved-cases">
          Resolved
        </ToggleButton>
      </ToggleButtonGroup>

      <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid #e5e7eb', display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 2 }}>
            <Box>
              <Typography variant="h6" fontWeight="bold">
                {caseView === "open-cases" ? "Open Cases" : "Resolved Cases"}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Latest patient triage assessments
              </Typography>
            </Box>
            <Tooltip title={`Current: ${getSortLabel(sortOption)}`}>
              <IconButton
                size="small"
                onClick={handleSortClick}
                aria-label="sort cases"
                sx={{
                  border: "1px solid #e5e7eb",
                  borderRadius: 1.5,
                  color: "#6b7280",
                  "&:hover": {
                    bgcolor: "#f9fafb",
                  },
                }}
              >
                <SortIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <TableContainer>
            <Table sx={{ minWidth: 700 }} aria-label="cases table">
              <TableHead>
                <TableRow sx={{ bgcolor: "#faf5ff" }}>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>
                    Patient
                  </TableCell>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>
                    Created
                  </TableCell>
                  <TableCell sx={{ color: "#6b7280", fontWeight: 700, borderBottomColor: "#e5e7eb" }}>
                    Severity
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedTriageCases.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} sx={{ py: 6, textAlign: "center", color: "#6b7280" }}>
                      No cases yet
                    </TableCell>
                  </TableRow>
                )}
                {sortedTriageCases.map((item, index) => {
                  const atsPriority = item.priority;
                  return (
                    <TableRow
                      key={`${item.id},${index}`}
                      onClick={() => {
                        navigate({ pathname: "/dashboard", search: `?case=${item.caseId}` });
                      }}
                      sx={{
                        cursor: "pointer",
                        "&:hover, &.MuiTableRow-hover:hover": { bgcolor: "#f5f3ff" },
                        "&:hover > *, &.MuiTableRow-hover:hover > *": { bgcolor: "#f5f3ff" },
                        "&:last-child td, &:last-child th": { border: 0 },
                      }}
                    >
                      <TableCell component="th" scope="row" sx={{ py: 1.8 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#111827" }}>
                          {item.name}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "#9ca3af" }}>
                          {item.id}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ color: "#6b7280", whiteSpace: "nowrap" }}>
                        {item.date}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={ATSLevel[atsPriority]}
                          size="small"
                          sx={{
                            bgcolor: getPriorityColor(atsPriority).bg,
                            color: getPriorityColor(atsPriority).color,
                            fontWeight: "bold",
                            borderRadius: 1.5,
                            px: 1,
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {successSnackbar}
    </Box>
  );
};

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
  CircularProgress,
} from "@mui/material";
import { ATSLevel } from "../types/triage";
import { CaseSummary } from "../components/CaseSummary";
import { getPriorityColor } from "../utils/color";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import { formatCaseDateTime, parseCaseDateTime } from "../utils/date";
import { UserRole } from "../types/user";
import { fetchWithAuth, getDecodedToken } from "../utils/auth";
import { API_BASE_URL } from "../utils/constants";
import { DashboardCaseObject } from "../types/case";
import AddIcon from "@mui/icons-material/Add";
import SortRoundedIcon from "@mui/icons-material/SortRounded";

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
  const isViewingDashboard = location.search === "";
  const navigate = useNavigate();
  const signedInAccount = localStorage.getItem("user_email") ?? "Dr. Smith";
  const userRole = getDecodedToken()?.role;
  const [searchParams] = useSearchParams();
  const [snackOpen, setSnackOpen] = useState<boolean>(false);
  const [snackMessage, setSnackMessage] = useState<string>("");
  const [snackSeverity, setSnackSeverity] = useState<'success' | 'info' | 'warning' | 'error'>("success");
  const [sortOption, setSortOption] = useState<SortOption>("severity");
  const [caseView, setCaseView] = useState<string>("open-cases");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [triageCases, setTriageCases] = useState<DashboardCaseObject[]>([]);
  const sortedTriageCases = [...triageCases]
    .map((item, originalIndex) => ({ item, originalIndex }))
    .sort((a, b) => {
      if (sortOption === "severity") {
        return a.item.ats_classification - b.item.ats_classification;
      }
      if (sortOption === "createdTime") {
        const aTimestamp = getCaseTimestamp(a.item.created_at, a.originalIndex);
        const bTimestamp = getCaseTimestamp(b.item.created_at, b.originalIndex);
        return bTimestamp - aTimestamp;
      }
      const nameCompareResult = compareCaseNameWithPriority(a.item.name, b.item.name);
      return nameCompareResult !== 0 ? nameCompareResult : a.originalIndex - b.originalIndex;
    })
    .map(({ item }) => item);

  useEffect(() => {
    const fetchCases = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const response = await fetchWithAuth(`${API_BASE_URL}/cases${caseView === "resolved-cases" ? "?resolved=true" : ""}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        const cases = await response.json() as DashboardCaseObject[];
        setTriageCases(cases);
      } finally {
        setIsLoading(false);
      }
    };

    if (isViewingDashboard) {
      fetchCases();
    }
  }, [caseView, isViewingDashboard]);

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

  const selectedCaseIdParam = searchParams.get("case");

  const successSnackbar = (
    <Snackbar open={snackOpen} autoHideDuration={4000} onClose={handleSnackClose}>
      <Alert onClose={handleSnackClose} severity={snackSeverity} sx={{ width: '100%' }}>
        {snackMessage}
      </Alert>
    </Snackbar>
  );

  if (selectedCaseIdParam != null && !isNaN(Number(selectedCaseIdParam))) {
    return (
      <>
        <CaseSummary
          caseId={Number(selectedCaseIdParam)}
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
          py: 2,
          mb: 4,
          borderRadius: 2,
          fontSize: '1.1rem',
          fontWeight: 'bold'
        }}
      >
        <AddIcon sx={{ mr: 1 }} />
        Create New Case
      </Button>}

      <ToggleButtonGroup
        value={caseView}
        onChange={(e: React.MouseEvent<HTMLElement>, newCaseView: string | null) => {
          if (newCaseView === null) return;
          setCaseView(newCaseView);
        }}
        exclusive
        sx={{
          mb: 2.5,
          p: 0.5,
          border: "1px solid #e5e7eb",
          borderRadius: 2,
          bgcolor: "#fff",
          "& .MuiToggleButtonGroup-grouped": {
            border: 0,
            borderRadius: 1.5,
            px: 2.5,
            py: 1,
            letterSpacing: "0.01em",
          },
          "& .MuiToggleButtonGroup-grouped:not(:first-of-type)": {
            borderLeft: "1px solid #e5e7eb",
            marginLeft: 0,
          },
        }}
      >
        <ToggleButton value="open-cases">
          Open
        </ToggleButton>
        <ToggleButton value="resolved-cases">
          Resolved
        </ToggleButton>
      </ToggleButtonGroup>

      <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
        <CardContent
          sx={{
            p: 0,
            "&:last-child": {
              pb: 0,
            },
          }}
        >
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
                }}
              >
                <SortRoundedIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          </Box>
          {isLoading && <Box 
            display="flex"
            justifyContent="center"
            alignItems="center"
            sx={{ p: 4 }}
          >
            <CircularProgress />
          </Box>}
          {!isLoading && <TableContainer>
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
                  const atsPriority = item.ats_classification - 1;
                  return (
                    <TableRow
                      key={`${item.medicare_number},${index}`}
                      hover
                      onClick={() => {
                        navigate({ pathname: "/dashboard", search: `?case=${item.case_id}` });
                      }}
                      sx={{
                        cursor: "pointer",
                        "&:last-child td, &:last-child th": { border: 0 },
                      }}
                    >
                      <TableCell component="th" scope="row" sx={{ py: 1.8 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#111827" }}>
                          {item.name}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "#9ca3af" }}>
                          {item.medicare_number}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ color: "#6b7280", whiteSpace: "nowrap" }}>
                        {formatCaseDateTime(new Date(item.created_at))}
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
          </TableContainer>}
        </CardContent>
      </Card>

      {successSnackbar}
    </Box>
  );
};

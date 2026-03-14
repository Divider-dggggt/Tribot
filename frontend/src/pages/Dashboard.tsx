import React, { ReactElement, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { 
  Alert, 
  Snackbar, 
  SnackbarCloseReason, 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider
} from "@mui/material";

// Simple Plus Icon
const PlusIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

type AtsLevel = "ATS-1" | "ATS-2" | "ATS-3" | "ATS-4" | "ATS-5";
type LegacyPriority = "HIGH" | "MEDIUM" | "LOW";
type CasePriority = AtsLevel | LegacyPriority;

interface RecentCase {
  id: number;
  name: string;
  date: string;
  priority: CasePriority;
}

const legacyPriorityToAts: Record<LegacyPriority, AtsLevel> = {
  HIGH: "ATS-1",
  MEDIUM: "ATS-3",
  LOW: "ATS-5",
};

const atsOrder: Record<AtsLevel, number> = {
  "ATS-1": 1,
  "ATS-2": 2,
  "ATS-3": 3,
  "ATS-4": 4,
  "ATS-5": 5,
};

const toAtsLevel = (priority: CasePriority): AtsLevel => {
  if (priority in legacyPriorityToAts) {
    return legacyPriorityToAts[priority as LegacyPriority];
  }
  return priority as AtsLevel;
};

// Mock Data
const recentCases: RecentCase[] = [
  { id: 1, name: 'Sarah Johnson', date: '2026-03-03 at 14:32', priority: 'ATS-1' },
  { id: 2, name: 'Michael Chen', date: '2026-03-03 at 13:15', priority: 'ATS-3' },
  { id: 3, name: 'Emma Williams', date: '2026-03-02 at 16:45', priority: 'ATS-5' },
  { id: 4, name: 'James Brown', date: '2026-03-02 at 11:20', priority: 'ATS-2' },
  { id: 5, name: 'Olivia Davis', date: '2026-03-01 at 09:40', priority: 'ATS-4' },
];

export const Dashboard = (): ReactElement => {
  const location = useLocation();
  const navigate = useNavigate();
  const [snackOpen, setSnackOpen] = useState<boolean>(false);
  const [snackMessage, setSnackMessage] = useState<string>("");
  const [snackSeverity, setSnackSeverity] = useState<'success' | 'info' | 'warning' | 'error'>("success");
  const sortedRecentCases = [...recentCases].sort(
    (a, b) => atsOrder[toAtsLevel(a.priority)] - atsOrder[toAtsLevel(b.priority)]
  );

  useEffect(() => {
    if (location.state?.message) {
      setSnackMessage(location.state.message);
      setSnackSeverity(location.state.severity || "success");
      setSnackOpen(true);
      window.history.replaceState({}, "");
    }
  }, [location.state]);

  const handleSnackClose = (
    event?: React.SyntheticEvent | Event,
    reason?: SnackbarCloseReason,
  ) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackOpen(false);
  };

  const getPriorityColor = (priority: AtsLevel) => {
    switch (priority) {
      case 'ATS-1': return { bg: '#fee2e2', color: '#dc2626' };
      case 'ATS-2': return { bg: '#ffedd5', color: '#ea580c' };
      case 'ATS-3': return { bg: '#fef3c7', color: '#d97706' };
      case 'ATS-4': return { bg: '#dcfce7', color: '#16a34a' };
      case 'ATS-5': return { bg: '#dbeafe', color: '#2563eb' };
      default: return { bg: '#f3f4f6', color: '#374151' };
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Welcome back, Dr. Smith
        </Typography>
      </Box>

      <Button 
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
      </Button>

      <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid #e5e7eb' }}>
            <Typography variant="h6" fontWeight="bold">
              Recent Cases
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Latest patient triage assessments
            </Typography>
          </Box>
          <List disablePadding>
            {sortedRecentCases.map((item, index) => {
              const atsPriority = toAtsLevel(item.priority);
              return (
              <React.Fragment key={item.id}>
                <ListItem sx={{ py: 2, px: 3 }}>
                  <ListItemText 
                    primary={
                      <Typography variant="subtitle1" fontWeight="medium">
                        {item.name}
                      </Typography>
                    }
                    secondary={
                      <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 6 }}>
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        {item.date}
                      </Typography>
                    } 
                  />
                  <Chip 
                    label={atsPriority} 
                    size="small"
                    sx={{ 
                      bgcolor: getPriorityColor(atsPriority).bg, 
                      color: getPriorityColor(atsPriority).color,
                      fontWeight: 'bold',
                      borderRadius: 1,
                      px: 1
                    }} 
                  />
                </ListItem>
                {index < sortedRecentCases.length - 1 && <Divider />}
              </React.Fragment>
            )})}
          </List>
        </CardContent>
      </Card>

      <Snackbar open={snackOpen} autoHideDuration={4000} onClose={handleSnackClose}>
        <Alert onClose={handleSnackClose} severity={snackSeverity} sx={{ width: '100%' }}>
          {snackMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

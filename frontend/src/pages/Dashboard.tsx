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
  ListItemButton,
  ListItemText,
  Chip,
  Divider
} from "@mui/material";
import { ATSLevel } from "../types/triage";
import { useSelector } from "react-redux";
import { getTriageCases } from "../store/triage/triageSlice";
import { CaseSummary } from "../components/CaseSummary";
import { getPriorityColor } from "../utils/color";

// Simple Plus Icon
const PlusIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

export const Dashboard = (): ReactElement => {
  const location = useLocation();
  const navigate = useNavigate();
  const [snackOpen, setSnackOpen] = useState<boolean>(false);
  const [snackMessage, setSnackMessage] = useState<string>("");
  const [snackSeverity, setSnackSeverity] = useState<'success' | 'info' | 'warning' | 'error'>("success");
  const [selectedCaseIdx, setSelectedCaseIdx] = useState<number | undefined>();
  const triageCases = useSelector(getTriageCases);
  const sortedTriageCases = [...triageCases].sort(
    (a, b) => a.priority - b.priority
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

  if (selectedCaseIdx !== undefined) {
    return <CaseSummary case={sortedTriageCases[selectedCaseIdx]} />;
  }

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
          {sortedTriageCases.length === 0 && <Typography
            variant="body2"
            sx={{ marginLeft: 2, marginTop: 2 }}
          >
            No cases yet
          </Typography>}
          <List disablePadding>
            {sortedTriageCases.map((item, index) => {
              const atsPriority = item.priority;
              return (
              <React.Fragment key={`${item.id},${index}`}>
                <ListItemButton
                  onClick={() => {
                    setSelectedCaseIdx(index);
                  }}
                  sx={{ py: 2, px: 3 }}
                >
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
                    label={ATSLevel[atsPriority]} 
                    size="small"
                    sx={{ 
                      bgcolor: getPriorityColor(atsPriority).bg, 
                      color: getPriorityColor(atsPriority).color,
                      fontWeight: 'bold',
                      borderRadius: 1,
                      px: 1
                    }} 
                  />
                </ListItemButton>
                {index < sortedTriageCases.length - 1 && <Divider />}
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

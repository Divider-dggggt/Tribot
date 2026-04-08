import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Divider, Grid, Stack, Typography } from "@mui/material";
import React, { ReactElement, useEffect, useState } from "react";
import { ATSLevel, TriageCase } from "../types/triage";
import { getPriorityColor } from "../utils/color";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import { API_BASE_URL } from "../utils/constants";
import { CaseObject } from "../types/case";
import { formatCaseDateTime } from "../utils/date";
import { getDecodedToken } from "../utils/auth";
import { UserRole } from "../types/user";
import { OverrideDialog } from "./OverrideDialog";

interface CaseSummaryProps {
  caseId: number;
  onBack: () => void;
}

const ArrowLeftIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ marginRight: 8 }}
  >
    <line x1="19" y1="12" x2="5" y2="12"></line>
    <polyline points="12 19 5 12 12 5"></polyline>
  </svg>
);

const parseAtsToLevel = (atsClassification: number): ATSLevel => {
  const boundedAts = Math.min(5, Math.max(1, Math.round(atsClassification)));
  return (boundedAts - 1) as ATSLevel;
};

export const CaseSummary = (props: CaseSummaryProps): ReactElement => {
  const { caseId, onBack } = props;
  const [triageCase, setTriageCase] = useState<CaseObject | undefined>();
  const userRole = getDecodedToken()?.role;
  const [isOverriding, setIsOverriding] = useState<boolean>(false);

  useEffect(() => {
    const fetchTriageCase = async (): Promise<void> => {
      const accessToken = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/cases/${caseId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });

      const caseResponse = await response.json() as CaseObject;
      setTriageCase(caseResponse);
    };

    fetchTriageCase();
  }, [caseId, triageCase == null]);

  if (triageCase == null) {
    return <CircularProgress />;
  }

  const triageCasePriority = parseAtsToLevel(triageCase.ats_classification);
  const priorityColor = getPriorityColor(triageCasePriority);
  const confidencePercentage = Math.round((triageCase.confidence_score ?? 0) * 100);
  const hasSafetyOverride = triageCase.severity_flagged;
  const flaggedKeywordsText = triageCase.severity_flags.map(flag => flag.flag_reason).join(",");
  const hasFlaggedKeywords = flaggedKeywordsText.length > 0;
  const atsLabel = ATSLevel[triageCasePriority];

  return (
    <Box sx={{ maxWidth: PAGE_CONTENT_MAX_WIDTH, mx: "auto" }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 4 }}
      >
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
            Triage Result
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Case summary and AI severity assessment
          </Typography>
        </Box>
        <Button
          variant="outlined"
          onClick={onBack}
          sx={{
            px: 2,
            py: 1,
            borderRadius: 2,
            fontWeight: "bold",
          }}
        >
          <ArrowLeftIcon />
          Back to Dashboard
        </Button>
      </Stack>

      <Card elevation={0} sx={{ border: "1px solid #e5e7eb", borderRadius: 2, mb: 3 }}>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                Patient Name
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {triageCase.name}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                Medicare Card Number
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {triageCase.medicare_number}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                Assessment Time
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {formatCaseDateTime(new Date(triageCase.created_at))}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card elevation={0} sx={{ border: "1px solid #e5e7eb", borderRadius: 2 }}>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
            AI Predicted Severity
          </Typography>
          <Box sx={{ display: "flex", justifyContent: "center", mb: 4 }}>
            <Card
              elevation={0}
              sx={{
                width: { xs: "100%", sm: 480 },
                backgroundColor: priorityColor.bg,
                border: `2px solid ${priorityColor.color}33`,
                borderRadius: 3,
                textAlign: "center",
                px: { xs: 3, sm: 5 },
                py: { xs: 3.5, sm: 4.5 },
                boxShadow: "0 12px 28px rgba(124, 58, 237, 0.12)",
              }}
            >
              <Typography
                variant="subtitle1"
                sx={{ color: priorityColor.color, fontWeight: "bold", mb: 1 }}
              >
                Severity Level
              </Typography>
              <Typography
                variant="h2"
                fontWeight="bold"
                sx={{ color: priorityColor.color, fontSize: { xs: "2.4rem", sm: "3.2rem" } }}
              >
                {atsLabel}
              </Typography>
              <Chip
                label={triageCase.clinician_override_at != null
                  ? "Clinician Override"
                  : (triageCase.severity_flagged ? "Safety Rule Override" : `Confidence ${confidencePercentage}%`)}
                sx={{
                  mt: 2,
                  fontWeight: "bold",
                  bgcolor: "#ffffffcc",
                  color: priorityColor.color,
                }}
              />
            </Card>
          </Box>
          <Alert
            severity={hasSafetyOverride ? "warning" : "info"}
            sx={{
              mb: 2,
              borderRadius: 2,
              border: hasSafetyOverride ? "1px solid #fcd34d" : "1px solid #bfdbfe",
            }}
          >
            {triageCase.clinician_override_at != null
              ? "Clinician override applied to this case."
              : (
                hasSafetyOverride
                  ? "Safety rule override applied to this case."
                  : "No safety rule override was applied."
              )
            }
            {hasFlaggedKeywords ? ` Trigger indicators: ${flaggedKeywordsText}` : ""}
          </Alert>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 1.5 }}>
            SOAP Summary
          </Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ whiteSpace: "pre-line", lineHeight: 1.7, mb: 3 }}
          >
            {triageCase.soap_summary.trim() || "No SOAP summary is available."}
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 1.5 }}>
            Case Details
          </Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ whiteSpace: "pre-line", lineHeight: 1.7 }}
          >
            {triageCase.case_details}
          </Typography>
        </CardContent>
      </Card>

      {userRole === UserRole.Clinician && <Button
        variant="outlined" 
        fullWidth 
        size="large"
        sx={{ 
          py: 2,
          mt: 4,
          borderRadius: 2,
          fontSize: '1.1rem',
          fontWeight: 'bold'
        }}
        onClick={() => {
          setIsOverriding(true);
        }}
      >
        Override
      </Button>}
      <Button 
        variant="contained" 
        fullWidth 
        size="large"
        onClick={() => {
          const accessToken = localStorage.getItem("access_token");
          void fetch(`${API_BASE_URL}/cases/${triageCase.case_id}/${triageCase.resolved_at == null ? "resolve" : "reopen"}`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            },
          }).then(() => {
            onBack();
          });
        }}
        sx={{ 
          py: 2,
          mt: 4,
          borderRadius: 2,
          fontSize: '1.1rem',
          fontWeight: 'bold'
        }}
      >
        {triageCase.resolved_at == null ? "Resolve" : "Reopen"}
      </Button>
      <OverrideDialog
        open={isOverriding}
        onClose={() => {
          setIsOverriding(false);
        }}
        onSuccess={() => {
          setTriageCase(undefined);
        }}
        initialValue={triageCasePriority}
        caseId={triageCase.case_id}
      />
    </Box>
  );
};

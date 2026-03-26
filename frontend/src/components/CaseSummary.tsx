import { Alert, Box, Button, Card, CardContent, Chip, Divider, Grid, Stack, Typography } from "@mui/material";
import React, { ReactElement } from "react";
import { ATSLevel, TriageCase } from "../types/triage";
import { getPriorityColor } from "../utils/color";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";

interface CaseSummaryProps {
  case: TriageCase;
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

export const CaseSummary = (props: CaseSummaryProps): ReactElement => {
  const { case: triageCase, onBack } = props;
  const priorityColor = getPriorityColor(triageCase.priority);
  const confidencePercentage = Math.round((triageCase.confidence ?? 0) * 100);
  const hasSafetyOverride = Boolean(triageCase.safetyOverride);
  const flaggedKeywordsText = triageCase.flaggedKeywords?.trim() ?? "";
  const hasFlaggedKeywords = flaggedKeywordsText.length > 0;
  const atsLabel = ATSLevel[triageCase.priority];

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
            color: "#7c3aed",
            borderColor: "#c4b5fd",
            px: 2,
            py: 1,
            borderRadius: 2,
            textTransform: "none",
            fontWeight: "bold",
            "&:hover": {
              borderColor: "#a78bfa",
              bgcolor: "#f5f3ff",
            },
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
                Patient ID
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {triageCase.id}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                Assessment Time
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {triageCase.date}
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
                label={`Confidence ${confidencePercentage}%`}
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
            {hasSafetyOverride
              ? "Safety rule override applied to this case."
              : "No safety rule override was applied."}
            {hasFlaggedKeywords ? ` Trigger indicator: ${flaggedKeywordsText}` : ""}
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
            {triageCase.soapSummary.trim() || "No SOAP summary is available."}
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
            {triageCase.details}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

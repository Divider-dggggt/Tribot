import { Box, Card, CardContent, Grid, Typography } from "@mui/material";
import React, { ReactElement } from "react";
import { ATSLevel, TriageCase } from "../types/triage";
import { getPriorityColor } from "../utils/color";

interface CaseSummaryProps {
  case: TriageCase;
}

export const CaseSummary = (props: CaseSummaryProps): ReactElement => {
  const { case: triageCase } = props;

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Triage Result
        </Typography>
      </Box>
      <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2, mb: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={3}>
            <Grid>
              Patient: <b>{triageCase.name}</b>
            </Grid>
            <Grid>
              Patient ID: <b>{triageCase.id}</b>
            </Grid>
            <Grid>
              Date: <b>{triageCase.date}</b>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              AI Predicted Severity
            </Typography>
            <Card
              sx={{
                maxWidth: 300,
                backgroundColor: getPriorityColor(triageCase.priority).bg,
                color: getPriorityColor(triageCase.priority).color
                }}
              >
              <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                <Typography variant="h5" fontWeight="bold" component="div">
                  {ATSLevel[triageCase.priority]}
                </Typography>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ mb: 4 }}>
            {triageCase.details}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

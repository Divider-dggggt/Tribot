import { useEffect, useState, type ReactElement } from "react";
import { API_BASE_URL } from "../utils/constants";
import { PAGE_CONTENT_MAX_WIDTH } from "../utils/layout";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";

export const Metrics = (): ReactElement => {
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
            Metrics
          </Typography>
        </Box>
      </Stack>
      <Card elevation={0} sx={{ border: "1px solid #e5e7eb", borderRadius: 2 }}>
        <CardContent
          sx={{
            p: 0,
            "&:last-child": {
              pb: 0,
            },
          }}
        >
          <Box sx={{ px: 3, py: 2.5, borderBottom: "1px solid #e5e7eb" }}>
            <Typography variant="h6" fontWeight="bold">
              Confusion Matrix
            </Typography>
            <Typography variant="body2" color="text.secondary">
              TODO: content here
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

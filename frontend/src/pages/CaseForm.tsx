import React, { ReactElement } from "react";
import { useForm } from "react-hook-form";
import { TextField, Button } from '@mui/material';
import { useNavigate } from "react-router-dom";

export const CaseForm = (): ReactElement => {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const navigate = useNavigate();
  const onSubmit = (data: Record<string, string>) => {
    console.log(data)
    navigate("/", { state: { message: "Successfully created case", severity: "success" } });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <TextField
        label="Patient ID"
        {...register("patientID", { required: "Required" })}
        error={!!errors.patientID}
        helperText={errors.patientID?.message as string}
      />
      <TextField
        label="Patient Name"
        {...register("patientName", { required: "Required" })}
        error={!!errors.patientName}
        helperText={errors.patientName?.message as string}
      />
      <TextField
        label="Symptom Description"
        {...register("symptoms", { required: "Required" })}
        multiline
        rows={10}
        error={!!errors.symptoms}
        helperText={errors.symptoms?.message as string}
      />
      <Button type="submit" variant="contained">Submit for Triage</Button>
    </form>
  );
};

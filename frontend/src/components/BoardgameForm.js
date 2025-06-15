import React, { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';

const BoardgameForm = ({ open, onClose, onSubmit, initialData }) => {
  const getInitialFormData = () => ({
    name: '',
    editor_name: '',
    num_players_min: '',
    num_players_max: '',
    age_min: '',
    time_duration_mean: '',
    labelsInput: '', // For comma-separated string
  });

  const [formData, setFormData] = useState(getInitialFormData());
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (open) { // Reset form and errors when dialog opens
      if (initialData) {
        setFormData({
          name: initialData.name || '',
          editor_name: initialData.editor_name || '',
          num_players_min: initialData.num_players_min !== undefined ? String(initialData.num_players_min) : '',
          num_players_max: initialData.num_players_max !== undefined ? String(initialData.num_players_max) : '',
          age_min: initialData.age_min !== undefined ? String(initialData.age_min) : '',
          time_duration_mean: initialData.time_duration_mean !== undefined ? String(initialData.time_duration_mean) : '',
          labelsInput: initialData.labels ? initialData.labels.join(', ') : '',
        });
      } else {
        setFormData(getInitialFormData());
      }
      setErrors({}); // Clear errors when dialog opens or initialData changes
    }
  }, [initialData, open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) { // Clear error for field when user starts typing
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    const { name, editor_name, num_players_min, num_players_max, age_min, time_duration_mean } = formData;

    // Required fields
    if (!name.trim()) newErrors.name = 'Name is required.';
    if (!editor_name.trim()) newErrors.editor_name = 'Editor Name is required.';
    if (!num_players_min.trim()) newErrors.num_players_min = 'Min Players is required.';
    if (!num_players_max.trim()) newErrors.num_players_max = 'Max Players is required.';
    if (!age_min.trim()) newErrors.age_min = 'Min Age is required.';

    // Numeric parsing
    const parsedNumPlayersMin = parseInt(num_players_min, 10);
    const parsedNumPlayersMax = parseInt(num_players_max, 10);
    const parsedAgeMin = parseInt(age_min, 10);
    const parsedTimeDurationMean = time_duration_mean ? parseInt(time_duration_mean, 10) : undefined;

    // Numeric validation
    if (num_players_min.trim() && (isNaN(parsedNumPlayersMin) || parsedNumPlayersMin <= 0)) {
      newErrors.num_players_min = 'Min Players must be a number greater than 0.';
    }
    if (num_players_max.trim() && (isNaN(parsedNumPlayersMax) || parsedNumPlayersMax <= 0)) {
      newErrors.num_players_max = 'Max Players must be a number greater than 0.';
    }
    if (num_players_min.trim() && num_players_max.trim() && !isNaN(parsedNumPlayersMin) && !isNaN(parsedNumPlayersMax) && parsedNumPlayersMax < parsedNumPlayersMin) {
      newErrors.num_players_max = 'Max Players must be greater than or equal to Min Players.';
    }
    if (age_min.trim() && (isNaN(parsedAgeMin) || parsedAgeMin < 0)) {
      newErrors.age_min = 'Min Age must be a non-negative number.';
    }
    if (time_duration_mean.trim() && (isNaN(parsedTimeDurationMean) || parsedTimeDurationMean <= 0)) {
      newErrors.time_duration_mean = 'Average Playtime must be a number greater than 0, if provided.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0; // Return true if no errors
  };

  const handleSubmit = () => {
    if (!validateForm()) {
      return; // Validation failed, do not submit
    }

    const gameData = {
      name: formData.name.trim(),
      editor_name: formData.editor_name.trim(),
      num_players_min: parseInt(formData.num_players_min, 10),
      num_players_max: parseInt(formData.num_players_max, 10),
      age_min: parseInt(formData.age_min, 10),
      time_duration_mean: formData.time_duration_mean ? parseInt(formData.time_duration_mean, 10) : undefined,
      labels: formData.labelsInput.split(',').map(label => label.trim()).filter(label => label),
    };
    onSubmit(gameData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{initialData ? 'Edit Boardgame' : 'Add New Boardgame'}</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              autoFocus
              margin="dense"
              name="name"
              label="Name"
              type="text"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleChange}
              required
              error={!!errors.name}
              helperText={errors.name}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              margin="dense"
              name="editor_name"
              label="Editor Name"
              type="text"
              fullWidth
              variant="outlined"
              value={formData.editor_name}
              onChange={handleChange}
              required
              error={!!errors.editor_name}
              helperText={errors.editor_name}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              margin="dense"
              name="num_players_min"
              label="Min Players"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.num_players_min}
              onChange={handleChange}
              required
              error={!!errors.num_players_min}
              helperText={errors.num_players_min}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              margin="dense"
              name="num_players_max"
              label="Max Players"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.num_players_max}
              onChange={handleChange}
              required
              error={!!errors.num_players_max}
              helperText={errors.num_players_max}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              margin="dense"
              name="age_min"
              label="Min Age"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.age_min}
              onChange={handleChange}
              required
              error={!!errors.age_min}
              helperText={errors.age_min}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              margin="dense"
              name="time_duration_mean"
              label="Average Playtime (minutes)"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.time_duration_mean}
              onChange={handleChange}
              error={!!errors.time_duration_mean}
              helperText={errors.time_duration_mean}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              margin="dense"
              name="labelsInput"
              label="Labels (comma-separated)"
              type="text"
              fullWidth
              variant="outlined"
              value={formData.labelsInput}
              onChange={handleChange}
              // No specific validation for labels in this iteration, but can be added
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          {initialData ? 'Save Changes' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BoardgameForm;

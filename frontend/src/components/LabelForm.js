import React, { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
// For a basic color input, we can use TextField type="color" or a more advanced picker
// For simplicity, using TextField for hex color string for now.

const LabelForm = ({ open, onClose, onSubmit, initialData }) => {
  const getInitialFormData = () => ({
    name: '',
    // color field removed
  });

  const [formData, setFormData] = useState(getInitialFormData());

  useEffect(() => {
    if (open) { // Reset form when dialog opens
        if (initialData) {
        setFormData({
            name: initialData.name || '',
            // color field removed
        });
        } else {
        setFormData(getInitialFormData());
        }
    }
  }, [initialData, open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    if (!formData.name || !formData.name.trim()) {
      alert('Label name is required and cannot be empty.'); // Basic validation
      return;
    }
    // Color validation removed
    onSubmit({ name: formData.name.trim() }); // Only submit name
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>{initialData ? 'Edit Label' : 'Add New Label'}</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              autoFocus
              margin="dense"
              name="name"
              label="Label Name"
              type="text"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </Grid>
          {/* Grid item for color removed */}
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

export default LabelForm;

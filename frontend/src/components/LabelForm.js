import React, { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
// For a basic color input, we can use TextField type="color" or a more advanced picker
// For simplicity, using TextField for hex color string for now.

const LabelForm = ({ open, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState({
    name: '',
    color: '#ffffff', // Default to white
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        color: initialData.color || '#ffffff',
      });
    } else {
      setFormData({
        name: '',
        color: '#ffffff',
      });
    }
  }, [initialData, open]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    if (!formData.name) {
      alert('Label name is required'); // Basic validation
      return;
    }
    // Basic color validation (hex format)
    if (!/^#[0-9A-F]{6}$/i.test(formData.color)) {
        alert('Color must be a valid hex code (e.g., #RRGGBB)');
        return;
    }
    onSubmit(formData);
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
          <Grid item xs={12}>
            <TextField
              margin="dense"
              name="color"
              label="Color (hex, e.g., #FF5733)"
              type="text" // Using text for hex input. Could use type="color" for a native picker.
              fullWidth
              variant="outlined"
              value={formData.color}
              onChange={handleChange}
              required
              InputLabelProps={{
                shrink: true,
              }}
            />
            {/* Simple color preview */}
            <Box sx={{width: '100%', height: 30, backgroundColor: formData.color, mt: 1, border: '1px solid #ccc'}} />
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

export default LabelForm;

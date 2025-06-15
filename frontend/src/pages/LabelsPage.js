import React, { useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';
import LabelList from '../components/LabelList';
import LabelForm from '../components/LabelForm';
import labelService from '../services/labelService';
import Typography from '@mui/material/Typography';

const LabelsPage = () => {
  const [formOpen, setFormOpen] = useState(false);
  const [editingLabel, setEditingLabel] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [error, setError] = useState(null);

  const handleOpenForm = (label = null) => {
    setEditingLabel(label);
    setFormOpen(true);
    setError(null);
  };

  const handleCloseForm = () => {
    setFormOpen(false);
    setEditingLabel(null);
  };

  const refreshLabels = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const handleSubmitForm = async (labelData) => {
    setError(null);
    try {
      if (editingLabel && editingLabel.name) { // Check for name to signify editing
        await labelService.updateLabel(editingLabel.name, labelData);
      } else {
        await labelService.createLabel(labelData);
      }
      refreshLabels();
      handleCloseForm();
    } catch (err) {
      console.error("Submit error:", err.response || err.message || err);
      setError(err.response?.data?.detail || err.message || 'Failed to save label.');
    }
  };

  const handleDeleteLabel = async (name) => { // Changed id to name
    setError(null);
    if (window.confirm('Are you sure you want to delete this label?')) {
      try {
        await labelService.deleteLabel(name); // Use name
        refreshLabels();
      } catch (err) {
        console.error("Delete error:", err.response || err.message || err);
        setError(err.response?.data?.detail || err.message || 'Failed to delete label.');
      }
    }
  };

  return (
    <Box sx={{ mt: 2, position: 'relative' }}>
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error: {error}
        </Typography>
      )}
      <LabelList
        onEdit={(label) => handleOpenForm(label)}
        onDelete={handleDeleteLabel}
        refreshTrigger={refreshTrigger}
      />
      <LabelForm
        open={formOpen}
        onClose={handleCloseForm}
        onSubmit={handleSubmitForm}
        initialData={editingLabel}
      />
      <Fab
        color="secondary" // Using secondary color for this FAB
        aria-label="add label"
        onClick={() => handleOpenForm()}
        sx={{
          position: 'fixed',
          bottom: (theme) => theme.spacing(2),
          right: (theme) => theme.spacing(2),
        }}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default LabelsPage;

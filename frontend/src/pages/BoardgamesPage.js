import React, { useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';
import BoardgameList from '../components/BoardgameList';
import BoardgameForm from '../components/BoardgameForm';
import boardgameService from '../services/boardgameService';
import Typography from '@mui/material/Typography'; // For error messages

const BoardgamesPage = () => {
  const [formOpen, setFormOpen] = useState(false);
  const [editingBoardgame, setEditingBoardgame] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0); // To trigger list refresh
  const [error, setError] = useState(null);

  const handleOpenForm = (boardgame = null) => {
    setEditingBoardgame(boardgame);
    setFormOpen(true);
    setError(null); // Clear previous errors
  };

  const handleCloseForm = () => {
    setFormOpen(false);
    setEditingBoardgame(null);
  };

  const refreshBoardgames = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const handleSubmitForm = async (boardgameData) => {
    setError(null);
    try {
      if (editingBoardgame && editingBoardgame.name) { // Check for name to signify editing
        await boardgameService.updateBoardgame(editingBoardgame.name, boardgameData);
      } else {
        await boardgameService.createBoardgame(boardgameData);
      }
      refreshBoardgames();
      handleCloseForm();
    } catch (err) {
      console.error("Submit error:", err.response || err.message || err);
      setError(err.response?.data?.detail || err.message || 'Failed to save boardgame.');
    }
  };

  const handleDeleteBoardgame = async (name) => { // Changed id to name
    setError(null);
    if (window.confirm('Are you sure you want to delete this boardgame?')) {
      try {
        await boardgameService.deleteBoardgame(name); // Use name
        refreshBoardgames();
      } catch (err) {
        console.error("Delete error:", err.response || err.message || err);
        setError(err.response?.data?.detail || err.message || 'Failed to delete boardgame.');
      }
    }
  };

  return (
    <Box sx={{ mt: 2, position: 'relative' }}>
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Erreur: {error}
        </Typography>
      )}
      <BoardgameList
        onEdit={(boardgame) => handleOpenForm(boardgame)}
        onDelete={handleDeleteBoardgame}
        refreshTrigger={refreshTrigger}
      />
      <BoardgameForm
        open={formOpen}
        onClose={handleCloseForm}
        onSubmit={handleSubmitForm}
        initialData={editingBoardgame}
      />
      <Fab
        color="primary"
        aria-label="add boardgame"
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

export default BoardgamesPage;

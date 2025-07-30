import React, { useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';
import BoardgameList from '../components/BoardgameList';
import BoardgameForm from '../components/BoardgameForm';
import gameService from '../services/gameService'; // Utilise le service API FastAPI
import Typography from '@mui/material/Typography';
import { useSession } from '@supabase/auth-helpers-react'; // Si tu utilises supabase-auth-helpers

const BoardgamesPage = () => {
  const [formOpen, setFormOpen] = useState(false);
  const [editingBoardgame, setEditingBoardgame] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [error, setError] = useState(null);

  // Récupère le token utilisateur Supabase
  const session = useSession();
  const token = session?.access_token;

  const handleOpenForm = (boardgame = null) => {
    setEditingBoardgame(boardgame);
    setFormOpen(true);
    setError(null);
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
      if (editingBoardgame && editingBoardgame.id) {
        await gameService.updateGame(editingBoardgame.id, boardgameData, token);
      } else {
        await gameService.createGame(boardgameData, token);
      }
      refreshBoardgames();
      handleCloseForm();
    } catch (err) {
      console.error("Submit error:", err.response || err.message || err);
      setError(err.response?.data?.detail || err.message || 'Failed to save boardgame.');
    }
  };

  const handleDeleteBoardgame = async (id) => {
    setError(null);
    if (window.confirm('Are you sure you want to delete this boardgame?')) {
      try {
        await gameService.deleteGame(id, token);
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
        onEdit={handleOpenForm}
        onDelete={handleDeleteBoardgame}
        refreshTrigger={refreshTrigger}
        token={token}
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
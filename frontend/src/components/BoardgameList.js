import React, { useEffect, useState } from 'react';
import Grid from '@mui/material/Grid';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import boardgameService from '../services/boardgameService';
import BoardgameCard from './BoardgameCard';

const BoardgameList = ({ onEdit, onDelete, refreshTrigger }) => {
  const [boardgames, setBoardgames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBoardgames = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await boardgameService.getAllBoardgames();
        setBoardgames(response.data);
      } catch (err) {
        setError(err.message || 'Failed to fetch boardgames');
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchBoardgames();
  }, [refreshTrigger]);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">Error: {error}</Typography>;
  }

  if (boardgames.length === 0) {
    return <Typography>No boardgames found. Add some!</Typography>;
  }

  return (
    <Grid container spacing={3}>
      {boardgames.map((boardgame) => (
        <Grid item key={boardgame.id} xs={12} sm={6} md={4} lg={3}>
          <BoardgameCard boardgame={boardgame} onEdit={onEdit} onDelete={onDelete} />
        </Grid>
      ))}
    </Grid>
  );
};

export default BoardgameList;

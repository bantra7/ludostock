import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

const BoardgameCard = ({ boardgame, onEdit, onDelete }) => {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography gutterBottom variant="h5" component="h2">
          {boardgame.name}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Editor: {boardgame.editor_name}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          Players: {boardgame.num_players_min} - {boardgame.num_players_max}
        </Typography>
        <Typography color="text.secondary">
          Min Age: {boardgame.age_min}
        </Typography>
        {boardgame.time_duration_mean && (
          <Typography color="text.secondary">
            Avg Playtime: {boardgame.time_duration_mean} min
          </Typography>
        )}
        {/* Labels could be displayed here if desired, e.g., boardgame.labels.map(l => l.name).join(', ') */}
      </CardContent>
      <CardActions>
        <IconButton size="small" onClick={() => onEdit(boardgame)}>
          <EditIcon />
        </IconButton>
        <IconButton size="small" onClick={() => onDelete(boardgame.name)}> {/* Changed to boardgame.name */}
          <DeleteIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default BoardgameCard;

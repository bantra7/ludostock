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
        <Typography>
          {boardgame.description}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          Players: {boardgame.min_players} - {boardgame.max_players}
        </Typography>
        <Typography color="text.secondary">
          Year: {boardgame.year_published}
        </Typography>
      </CardContent>
      <CardActions>
        <IconButton size="small" onClick={() => onEdit(boardgame)}>
          <EditIcon />
        </IconButton>
        <IconButton size="small" onClick={() => onDelete(boardgame.id)}>
          <DeleteIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default BoardgameCard;

import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import Box from '@mui/material/Box';

const LabelCard = ({ label, onEdit, onDelete }) => {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography gutterBottom variant="h6" component="h2">
          {label.name}
        </Typography>
        {/* Color display removed as it's not part of the current Label model */}
      </CardContent>
      <CardActions>
        <IconButton size="small" onClick={() => onEdit(label)}>
          <EditIcon />
        </IconButton>
        <IconButton size="small" onClick={() => onDelete(label.name)}> {/* Changed to label.name */}
          <DeleteIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default LabelCard;

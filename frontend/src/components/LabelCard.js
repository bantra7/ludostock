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
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Color:
          </Typography>
          <Box
            sx={{
              width: 20,
              height: 20,
              backgroundColor: label.color || '#ccc', // Default color if none provided
              border: '1px solid #888',
              borderRadius: '4px',
            }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            ({label.color})
          </Typography>
        </Box>
      </CardContent>
      <CardActions>
        <IconButton size="small" onClick={() => onEdit(label)}>
          <EditIcon />
        </IconButton>
        <IconButton size="small" onClick={() => onDelete(label.id)}>
          <DeleteIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default LabelCard;

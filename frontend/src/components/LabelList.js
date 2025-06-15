import React, { useEffect, useState } from 'react';
import Grid from '@mui/material/Grid';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import labelService from '../services/labelService';
import LabelCard from './LabelCard';

const LabelList = ({ onEdit, onDelete, refreshTrigger }) => {
  const [labels, setLabels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLabels = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await labelService.getAllLabels();
        setLabels(response.data);
      } catch (err) {
        setError(err.message || 'Failed to fetch labels');
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchLabels();
  }, [refreshTrigger]);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">Error: {error}</Typography>;
  }

  if (labels.length === 0) {
    return <Typography>No labels found. Add some!</Typography>;
  }

  return (
    <Grid container spacing={3}>
      {labels.map((label) => (
        <Grid item key={label.name} xs={12} sm={6} md={4} lg={3}> {/* Changed key to label.name */}
          <LabelCard label={label} onEdit={onEdit} onDelete={onDelete} />
        </Grid>
      ))}
    </Grid>
  );
};

export default LabelList;

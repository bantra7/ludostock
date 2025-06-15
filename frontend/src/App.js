import React, { useState } from 'react';
import Container from '@mui/material/Container';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Header from './components/Header';
import BoardgamesPage from './pages/BoardgamesPage';
import LabelsPage from './pages/LabelsPage'; // Import LabelsPage

function App() {
  const [selectedTab, setSelectedTab] = useState(0);

  const handleChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  return (
    <>
      <Header />
      <Container>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={selectedTab} onChange={handleChange} aria-label="basic tabs example">
            <Tab label="Boardgames" />
            <Tab label="Labels" />
          </Tabs>
        </Box>
        <Box sx={{ p: 3 }}>
          {selectedTab === 0 && <BoardgamesPage />}
          {selectedTab === 1 && <LabelsPage />}
        </Box>
      </Container>
    </>
  );
}

export default App;

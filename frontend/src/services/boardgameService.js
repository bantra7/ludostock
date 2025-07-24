import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api'; // Assuming backend runs on port 8000

const boardgameService = {
  getAllBoardgames: () => {
    return axios.get(`${API_BASE_URL}/boardgames/`);
  },

  createBoardgame: (boardgameData) => {
    return axios.post(`${API_BASE_URL}/boardgames/`, boardgameData); // Added trailing slash
  },

  updateBoardgame: (id, boardgameData) => {
    return axios.put(`${API_BASE_URL}/boardgames/${id}`, boardgameData);
  },

  deleteBoardgame: (id) => {
    return axios.delete(`${API_BASE_URL}/boardgames/${id}`);
  },
};

export default boardgameService;

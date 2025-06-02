import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api'; // Assuming backend runs on port 8000

const boardgameService = {
  getAllBoardgames: () => {
    return axios.get(`${API_BASE_URL}/boardgames`);
  },

  createBoardgame: (boardgameData) => {
    return axios.post(`${API_BASE_URL}/boardgames`, boardgameData);
  },

  updateBoardgame: (id, boardgameData) => {
    return axios.put(`${API_BASE_URL}/boardgames/${id}`, boardgameData);
  },

  deleteBoardgame: (id) => {
    return axios.delete(`${API_BASE_URL}/boardgames/${id}`);
  },
};

export default boardgameService;

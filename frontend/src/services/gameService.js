import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/games';

const gameService = {
  getAllGames: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getGame: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createGame: (gameData, token) => {
    return axios.post(`${API_BASE_URL}/`, gameData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateGame: (id, gameData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, gameData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteGame: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default gameService;
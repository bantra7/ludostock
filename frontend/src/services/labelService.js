import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api'; // Assuming backend runs on port 8000

const labelService = {
  getAllLabels: () => {
    return axios.get(`${API_BASE_URL}/labels`);
  },

  createLabel: (labelData) => {
    return axios.post(`${API_BASE_URL}/labels`, labelData);
  },

  updateLabel: (id, labelData) => {
    return axios.put(`${API_BASE_URL}/labels/${id}`, labelData);
  },

  deleteLabel: (id) => {
    return axios.delete(`${API_BASE_URL}/labels/${id}`);
  },
};

export default labelService;

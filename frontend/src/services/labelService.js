import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api'; // Assuming backend runs on port 8000

const labelService = {
  getAllLabels: () => {
    return axios.get(`${API_BASE_URL}/labels`);
  },

  createLabel: (labelData) => {
    return axios.post(`${API_BASE_URL}/labels/`, labelData); // Added trailing slash for consistency
  },

  updateLabel: (name, labelData) => { // Changed id to name
    return axios.put(`${API_BASE_URL}/labels/${name}`, labelData); // Use name in URL
  },

  deleteLabel: (name) => { // Changed id to name
    return axios.delete(`${API_BASE_URL}/labels/${name}`); // Use name in URL
  },
};

export default labelService;

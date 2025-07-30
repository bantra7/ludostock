import axios from 'axios';

const API_BASE_URL = 'https://ludostock-backend-1015299081216.europe-west1.run.app/api/editors';

const editorService = {
  getAllEditors: (token) => {
    return axios.get(`${API_BASE_URL}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  getEditor: (id, token) => {
    return axios.get(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  createEditor: (editorData, token) => {
    return axios.post(`${API_BASE_URL}/`, editorData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  updateEditor: (id, editorData, token) => {
    return axios.put(`${API_BASE_URL}/${id}`, editorData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  deleteEditor: (id, token) => {
    return axios.delete(`${API_BASE_URL}/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default editorService;
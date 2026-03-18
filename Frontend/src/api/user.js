import axios from 'axios'

export function registerApi(data) {
  return axios.post('http://localhost:8000/register', data)
}

export function loginApi(data) {
  return axios.post('http://localhost:8000/login', data)
}
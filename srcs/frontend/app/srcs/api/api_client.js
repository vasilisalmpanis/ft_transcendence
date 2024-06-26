import { API_ENDPOINT, WS_ENDPOINT } from "../conf/content_en.js";
import WebsocketClient from "./websocket_client.js";

/**
 * Represents an API client for making HTTP requests
 * to the backend server pong.
 * @class
 */
class ApiClient {
  constructor (baseUrl) {
    this.baseUrl = new URL(baseUrl);
    this.route = null;
    this.headers = {
      Accept: 'application/json',
    };
    if (localStorage.getItem('access_token')) {
      this.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
    }
    if (localStorage.getItem('refresh_token')) {
      this.refresh_token = localStorage.getItem('refresh_token');
    }
      
    // dev only
  }

  async checkStatus (response) {
    if (!response.ok) {
      const errorData = await response;
      let errorMessage = `Error: ${response.status} ${response.statusText}`;
      if (errorData.message) {
        errorMessage += ` - ${errorData.message}`;
      }
      throw new Error(errorMessage);
    }
  }

  async proceedResponse(response) {
    let data = await response.json();
    if (response.ok)
      return data;
    else
    {
      if (data.Error)
      return {error: data.Error};
      else if (data.status)
        return {error: data.status};
      return {error: response.status}
    }
  }

  async sendRequest (path, method, body, query, headers = {}) {
    /* Makes request and returns reponse object with all its fields */
    if (!path.startsWith('/'))
      path = '/' + path;
    const url = new URL(this.baseUrl + path);
    let params = {
      method,
      headers: {...this.headers, ...headers},
    };
    if (body) {
      if (body instanceof FormData)
        params.body = body;
      else {
        params.body = JSON.stringify(body);
        params.headers['Content-Type'] = 'application/json';
      }
    }
    else
      params.headers['Content-Type'] = 'application/json';
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }
    try {
      let response = await fetch(url, params);
      while (response.status === 401 && path !== '/auth/refresh' && path !== '/2fa/verify' && path !== '/auth/verify') {
        const refresh = await this.refresh();
        if (refresh === undefined)
          return {error: "Failed to login"}
        if (refresh.error === 'User not active' || refresh.error === 'Invalid signature') {
          this.unauthorize();
          this.route('/signin');
          return {error: 401};
        }
        params = {
          method,
          headers: {...this.headers, ...headers},
        };
        response = await fetch(url, params);
        break ; // dont know if really needed but certainly while loop is not the best solution
      }
      return await this.proceedResponse(response);
    } catch (error) {
      // this.route('/signin');
      return {error: error.message};
    }
  }

  async get (path, query) {
    return await this.sendRequest(path, 'GET', null, query);
  }

  async post (path, body, query, headers) {
    return await this.sendRequest(path, 'POST', body, query, headers);
  }

  async put (path, body, query) {
    return await this.sendRequest(path, 'PUT', body, query);
  }

  async delete (path, body, query) {
    return await this.sendRequest(path, 'DELETE', body, query);
  }

  async authorize (payload, query = null, tfa = false) {
    let response_body;
    if ("access_token" in payload)
      response_body = payload;
    else {
      response_body = await this.sendRequest('auth', 'POST', payload, query);
    }
    if (response_body.error)
      return response_body;
    const access_token = response_body.access_token;
    const refresh_token = response_body.refresh_token;
    this.headers['Authorization'] = `Bearer ${access_token}`;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('2fa', tfa);
    if (!JSON.parse(atob(access_token.split(".")[1]))["is_authenticated"])
      return {"ok": "2fa"}
    const me = await this.get("/users/me");
    if (me.error)
      return me;
    localStorage.setItem("me", JSON.stringify(me));
    new WebsocketClient(`${WS_ENDPOINT}/ws/chat/dm/`, access_token);
    return {"ok": "true"};
  }

  unauthorize () {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('me');
    localStorage.removeItem('2fa');
    if (WebsocketClient.has(`${WS_ENDPOINT}/ws/chat/dm/`)) {
      new WebsocketClient(`${WS_ENDPOINT}/ws/chat/dm/`).close();
    }
  }

  async logout () {
    const response = await this.sendRequest('logout', 'POST', null, null);
    this.unauthorize();
    return response;
  }

  async refresh ()
  {
    if (this.refresh_token === undefined) {
      return ;
    }
    this.headers['Authorization'] = `Bearer ${this.refresh_token}`;
    const response = await this.sendRequest('/auth/refresh', 'GET', null, null);
    if (response.error)
    {
      return response;
    }
    const access_token = response.access_token;
    // dev only
    if (typeof localStorage === 'undefined') {
      this.headers['Authorization'] = `Bearer ${access_token}`;
      return response;
    }
    let test = localStorage.setItem('access_token', access_token);
    this.headers['Authorization'] = `Bearer ${access_token}`;
    if (WebsocketClient.has(`${WS_ENDPOINT}/ws/chat/dm/`)) {
      new WebsocketClient(`${WS_ENDPOINT}/ws/chat/dm/`).reconnect(access_token);
    }
    return response;
  }

  async second_factor (code) {
    const response = await this.sendRequest('/auth/verify', 'POST', { "2fa_code" : code }, null);
    if (response.error)
      return response;
    const access_token = response.access_token;
    const refresh_token = response.refresh_token;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    this.headers['Authorization'] = `Bearer ${access_token}`;
    localStorage.setItem('2fa', true);
    const me = await this.get("/users/me");
    if (me.error)
      return me;
    localStorage.setItem("me", JSON.stringify(me));
    return response;
  }
  authorized() {
    return (
      (
        localStorage.getItem('access_token')
        || localStorage.getItem('refresh_token')
      ) && localStorage.getItem('me')
      ? true
      : false
    );
  }
};

export const apiClient = new ApiClient(API_ENDPOINT);

export default ApiClient;

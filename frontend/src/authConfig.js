// authConfig.js
export const msalConfig = {
  auth: {
    clientId: "22cc761a-2721-484b-be1f-e67d5a6e8460",                    // SPA app
    authority:
      "https://login.microsoftonline.com/74331905-fced-4292-b083-b1acc5ef1de8",
    redirectUri: "http://localhost:8080",
  },
};

export const loginRequest = {
  scopes: ["api://5c35d885-cbef-4291-bd8c-23f6f1c1eea0/access_as_user"],  // API app
};

import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app";
import "./styles.css";
import "@home-voice-studio/ui/styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

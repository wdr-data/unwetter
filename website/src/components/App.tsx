import React from "react";
import AppBar from "@material-ui/core/es/AppBar";
import Button from "@material-ui/core/es/Button";
import Toolbar from "@material-ui/core/es/Toolbar";
import Typography from "@material-ui/core/es/Typography";
import { Router, RouteComponentProps } from "@reach/router";

import styles from "./App.module.scss";
import Events from "./maps/Events";

const App: React.FC = () => {
  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography className={styles.white} variant="h6">
            UWA Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      <Router>
        <Events path="/events/*" />
      </Router>
    </>
  );
};

export default App;

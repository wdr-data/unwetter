import React from "react";
import AppBar from "@material-ui/core/es/AppBar";
import Toolbar from "@material-ui/core/es/Toolbar";
import Typography from "@material-ui/core/es/Typography";
import { Router } from "@reach/router";

import styles from "./App.module.scss";
import Events from "./maps/Events";

const App: React.FC = () => {
  return (
    <>
      <AppBar position="static">
        <Toolbar className={styles.appBar}>
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

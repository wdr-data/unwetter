import React, { useState, useCallback } from "react";
import Button from "@material-ui/core/es/Button";
import Paper from "@material-ui/core/es/Paper";
import TextField from "@material-ui/core/es/TextField";
import Grid from "@material-ui/core/es/Grid";
import classNames from "classnames";
import moment from "moment";

import { RouteComponentProps } from "@reach/router";

import styles from "./Events.module.scss";
import { useFormField } from "../hooks/form";

const Events: React.FC<RouteComponentProps> = () => {
  const [date, changeDateHandler] = useFormField("");
  const [time, changeTimeHandler] = useFormField("");

  const [events, setEvents] = useState([]);

  const refreshMap = useCallback(async () => {
    const m = moment(`${date}T${time}`, "");
    const timestamp = m.format("X");
    setEvents(
      await (await fetch(`/api/v1/events/current?at=${timestamp}`)).json()
    );
  }, [date, time]);

  return (
    <div className={styles.configurator}>
      <Grid container spacing={3}>
        <Grid item xs={6}>
          <Paper className={classNames(styles.paper, styles.marginBottom)}>
            <TextField
              label="Datum"
              margin="normal"
              type="date"
              InputLabelProps={{
                shrink: true
              }}
              onChange={changeDateHandler}
            />
            <TextField
              label="Zeit"
              margin="normal"
              type="time"
              InputLabelProps={{
                shrink: true
              }}
              onChange={changeTimeHandler}
            />
            <br />
          </Paper>
          <Paper className={styles.paper}>
            <TextField label="Titel" margin="normal" /> <br />
            <TextField label="Untertitel" margin="normal" /> <br />
          </Paper>
        </Grid>
        <Grid item xs={6}>
          <Paper className={styles.paper}>
            <img
              className={classNames(styles.image, styles.marginBottom)}
              src={`/map?id=${events.map((ev: any) => ev.id).join("&id=")}`}
              alt="Map of the event"
            />
            <Button color="secondary" variant="contained" onClick={refreshMap}>
              Refresh
            </Button>
            <Button color="primary" variant="contained">
              Download
            </Button>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper className={styles.paper}>foo</Paper>
        </Grid>
      </Grid>
    </div>
  );
};

export default Events;

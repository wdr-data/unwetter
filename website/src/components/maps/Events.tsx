import React, { useState, useCallback, useRef, useLayoutEffect } from "react";
import Button from "@material-ui/core/es/Button";
import Paper from "@material-ui/core/es/Paper";
import TextField from "@material-ui/core/es/TextField";
import Grid from "@material-ui/core/es/Grid";
import classNames from "classnames";
import moment from "moment";
import queryString from "query-string";

import { RouteComponentProps } from "@reach/router";

import styles from "./Events.module.scss";
import { useFormField } from "../hooks/form";

const Events: React.FC<RouteComponentProps> = () => {
  const [date, changeDateHandler, setDate] = useFormField("");
  const [time, changeTimeHandler, setTime] = useFormField("");

  const [text, changeTextHandler] = useFormField("Hallo Welt");
  const [corner, changeCornerHandler] = useFormField("se");
  const [size, changeSizeHandler] = useFormField("50");

  const dateRef = useRef<HTMLInputElement>();
  const timeRef = useRef<HTMLInputElement>();

  const [events, setEvents] = useState([]);

  const refreshMap = useCallback(async () => {
    const m = moment(`${date}T${time}`, "");
    const timestamp = m.format("X");
    setEvents(
      await (await fetch(`/api/v1/events/current?at=${timestamp}`)).json()
    );
  }, [date, time, setEvents]);

  const mapQuery = queryString.stringify({
    id: events.map((ev: any) => ev.id),
    text,
    corner,
    size
  });

  useLayoutEffect(() => {
    if (dateRef.current && timeRef.current) {
      const now = moment();
      const dateString = now.format("YYYY-MM-DD");
      const timeString = now.format("hh:mm");

      dateRef.current.value = dateString;
      setDate(dateString);

      timeRef.current.value = timeString;
      setTime(timeString);

      const fetchEvents = async () => {
        const timestamp = now.format("X");
        setEvents(
          await (await fetch(`/api/v1/events/current?at=${timestamp}`)).json()
        );
      };
      fetchEvents();
    }
  }, [setDate, setTime]);

  return (
    <div className={styles.configurator}>
      <Grid container spacing={3}>
        <Grid item xs={6}>
          <Paper className={classNames(styles.paper, styles.marginBottom)}>
            <TextField
              label="Datum"
              margin="normal"
              type="date"
              inputRef={dateRef}
              InputLabelProps={{
                shrink: true
              }}
              onChange={changeDateHandler}
            />
            <TextField
              label="Zeit"
              margin="normal"
              type="time"
              inputRef={timeRef}
              InputLabelProps={{
                shrink: true
              }}
              onChange={changeTimeHandler}
            />
            <br />
          </Paper>
          <Paper className={styles.paper}>
            <TextField
              label="Text"
              margin="normal"
              multiline
              onChange={changeTextHandler}
            />{" "}
            <br />
            <TextField
              label="Ecke"
              margin="normal"
              onChange={changeCornerHandler}
            />{" "}
            <br />
            <TextField
              label="Größe"
              margin="normal"
              onChange={changeSizeHandler}
            />{" "}
            <br />
          </Paper>
        </Grid>
        <Grid item xs={6}>
          <Paper className={styles.paper}>
            <img
              className={classNames(styles.image, styles.marginBottom)}
              src={`/map?${mapQuery}`}
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

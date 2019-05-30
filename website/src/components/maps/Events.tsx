import React, { useState, useCallback, useRef, useLayoutEffect } from "react";
import Button from "@material-ui/core/es/Button";
import Paper from "@material-ui/core/es/Paper";
import TextField from "@material-ui/core/es/TextField";
import Grid from "@material-ui/core/es/Grid";
import Select from "@material-ui/core/es/Select";
import MenuItem from "@material-ui/core/es/MenuItem";
import classNames from "classnames";
import moment from "moment";
import queryString from "query-string";

import { RouteComponentProps } from "@reach/router";

import styles from "./Events.module.scss";
import { useFormField } from "../hooks/form";

const Events: React.FC<RouteComponentProps> = () => {
  const [date, changeDateHandler, setDate] = useFormField("");
  const [time, changeTimeHandler, setTime] = useFormField("");

  const [text, changeTextHandler] = useFormField("");
  const [corner, changeCornerHandler] = useFormField("se");
  const [size, changeSizeHandler] = useFormField("100");

  const [mapQuery, setMapQuery] = useState("");

  const dateRef = useRef<HTMLInputElement>();
  const timeRef = useRef<HTMLInputElement>();

  const [, setEvents] = useState([]);

  const refreshMap = useCallback(async () => {
    const m = moment(`${date}T${time}`, "");
    const timestamp = m.format("X");
    const events = await (await fetch(
      `/api/v1/events/current?at=${timestamp}`
    )).json();
    setEvents(events);
    setMapQuery(
      queryString.stringify({
        id: events.map((ev: any) => ev.id),
        text,
        corner,
        size
      })
    );
  }, [date, time, text, corner, size]);

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
            <Button color="secondary" variant="contained" onClick={refreshMap}>
              Refresh
            </Button>
          </Paper>
          <Paper className={styles.paper}>
            <TextField
              label="Text"
              margin="normal"
              multiline
              onChange={changeTextHandler}
            />
            <br />
            <Select
              label="Ecke"
              margin="normal"
              onChange={changeCornerHandler}
              value={corner}
            >
              <MenuItem value="nw">Oben Links</MenuItem>
              <MenuItem value="sw">Unten Links</MenuItem>
              <MenuItem value="se">Unten Rechts</MenuItem>
            </Select>
            <br />
            <TextField
              label="Größe"
              margin="normal"
              type="number"
              defaultValue={size}
              onChange={changeSizeHandler}
            />
            <br />
            <Button color="secondary" variant="contained" onClick={refreshMap}>
              Refresh
            </Button>
          </Paper>
        </Grid>
        <Grid item xs={6}>
          <Paper className={styles.paper}>
            <img
              className={classNames(styles.image, styles.marginBottom)}
              src={`/map?${mapQuery}`}
              alt="Map of the event"
            />
            <a href={`/map?${mapQuery}`} download>
              <Button color="primary" variant="contained">
                Download
              </Button>
            </a>
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
};

export default Events;

import React, {
  useState,
  useCallback,
  useRef,
  useLayoutEffect,
  useEffect
} from "react";
import Button from "@material-ui/core/es/Button";
import Checkbox from "@material-ui/core/es/Checkbox";
import Paper from "@material-ui/core/es/Paper";
import TextField from "@material-ui/core/es/TextField";
import FormHelperText from "@material-ui/core/es/FormHelperText";
import FormControl from "@material-ui/core/es/FormControl";
import Grid from "@material-ui/core/es/Grid";
import Select from "@material-ui/core/es/Select";
import Snackbar from "@material-ui/core/es/Snackbar";
import SnackbarContent from "@material-ui/core/es/SnackbarContent";
import Table from "@material-ui/core/es/Table";
import TableBody from "@material-ui/core/es/TableBody";
import TableCell from "@material-ui/core/es/TableCell";
import TableHead from "@material-ui/core/es/TableHead";
import TableRow from "@material-ui/core/TableRow";
import MenuItem from "@material-ui/core/es/MenuItem";
import classNames from "classnames";
import moment from "moment";
import queryString from "query-string";

import { RouteComponentProps } from "@reach/router";

import styles from "./Events.module.scss";
import { useFormField } from "../hooks/form";
import { Typography } from "@material-ui/core";

const Events: React.FC<RouteComponentProps> = () => {
  const [date, changeDateHandler, setDate] = useFormField("");
  const [time, changeTimeHandler, setTime] = useFormField("");

  const [text, changeTextHandler, setText] = useFormField("");
  const [corner, changeCornerHandler] = useFormField("sw");
  const [size, changeSizeHandler] = useFormField("100");

  const [mapQuery, setMapQuery] = useState("");
  const [initialLoadingComplete, setInitialLoadingComplete] = useState(false);

  const [linkedEventId, setLinkedEventId] = useState("");
  const [eventNotFoundOpen, setEventNotFoundOpen] = React.useState(false);

  const dateRef = useRef<HTMLInputElement>();
  const timeRef = useRef<HTMLInputElement>();
  const textRef = useRef<HTMLTextAreaElement>();

  const [events, setEvents] = useState<any[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<any[]>([]);

  const isSelected = useCallback(
    event => filteredEvents.findIndex(fev => fev === event) !== -1,
    [filteredEvents]
  );

  const toggleEvent = useCallback(
    event => {
      let filteredEventsNew;

      if (isSelected(event)) {
        filteredEventsNew = filteredEvents.filter(fev => fev !== event);
      } else {
        filteredEventsNew = filteredEvents.concat([event]);
      }

      setFilteredEvents(filteredEventsNew);

      setMapQuery(
        queryString.stringify({
          id: filteredEventsNew.map((ev: any) => ev.id),
          text,
          corner,
          size
        })
      );
    },
    [filteredEvents, isSelected, text, corner, size]
  );

  const refreshMap = useCallback(async () => {
    setMapQuery(
      queryString.stringify({
        id: filteredEvents.map((ev: any) => ev.id),
        text,
        corner,
        size
      })
    );
  }, [filteredEvents, text, corner, size]);

  const refreshEvents = useCallback(async () => {
    const m = moment(`${date}T${time}`, "");
    const timestamp = m.format("X");
    const events = await (await fetch(
      `/api/v1/events/current?at=${timestamp}`
    )).json();

    setEvents(events);
    setFilteredEvents(events);

    setMapQuery(
      queryString.stringify({
        id: events.map((ev: any) => ev.id),
        text,
        corner,
        size
      })
    );
  }, [date, time, text, corner, size]);

  // Querystring parsing
  useEffect(() => {
    const qs = queryString.parse(window.location.search);

    if (qs && qs.id && typeof qs.id === "string") {
      setLinkedEventId(qs.id);
    }
  }, [setLinkedEventId]);

  // Initial page setup
  useLayoutEffect(() => {
    if (initialLoadingComplete) {
      return;
    }
    if (dateRef.current && timeRef.current) {
      const now = moment();
      const dateString = now.format("YYYY-MM-DD");
      const timeString = now.format("HH:mm");

      dateRef.current.value = dateString;
      setDate(dateString);

      timeRef.current.value = timeString;
      setTime(timeString);

      const fetchEvents = async () => {
        const timestamp = now.format("X");
        const events = (await (await fetch(
          `/api/v1/events/current?at=${timestamp}`
        )).json()) as any[];

        setEvents(events);
        setFilteredEvents(events);

        // Draw initial map
        let localText;

        if (linkedEventId && textRef.current) {
          const linkedEvent = events.find(ev => ev.id === linkedEventId);
          if (!linkedEvent) {
            setEventNotFoundOpen(true);
            setInitialLoadingComplete(true);
            return;
          }
          const warnText = linkedEvent.headline.replace("vor ", "vor\n");
          textRef.current.value = warnText;
          setText(warnText);
          localText = warnText;
        }

        setMapQuery(
          queryString.stringify({
            id: events.map((ev: any) => ev.id),
            text: localText,
            corner,
            size
          })
        );

        setInitialLoadingComplete(true);
      };

      fetchEvents();
    }
  }, [
    setDate,
    setTime,
    linkedEventId,
    corner,
    size,
    text,
    setText,
    setEventNotFoundOpen,
    initialLoadingComplete,
    setInitialLoadingComplete
  ]);

  const handleEventNotFoundClose = useCallback(
    (event: React.SyntheticEvent | React.MouseEvent, reason?: string) => {
      if (reason === "clickaway") {
        return;
      }

      setEventNotFoundOpen(false);
    },
    [setEventNotFoundOpen]
  );

  return (
    <div className={styles.configurator}>
      <Grid container spacing={3}>
        <Grid item xs={6}>
          <Paper className={styles.paper}>
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
            <Button
              color="secondary"
              variant="contained"
              onClick={refreshEvents}
            >
              Refresh
            </Button>
          </Paper>
          <Paper className={styles.paper}>
            <Grid container spacing={2}>
              <Grid item xs={9}>
                <FormControl fullWidth>
                  <TextField
                    inputRef={textRef}
                    margin="normal"
                    multiline
                    onChange={changeTextHandler}
                  />
                  <FormHelperText>Text</FormHelperText>
                </FormControl>
              </Grid>

              <Grid item xs={3}>
                <FormControl fullWidth>
                  <Select
                    label="Ecke"
                    onChange={changeCornerHandler}
                    value={corner}
                  >
                    <MenuItem value="nw">Oben Links</MenuItem>
                    <MenuItem value="sw">Unten Links</MenuItem>
                    <MenuItem value="se">Unten Rechts</MenuItem>
                  </Select>
                  <FormHelperText>Ausrichtung</FormHelperText>
                </FormControl>
                <br />

                <FormControl fullWidth>
                  <TextField
                    margin="normal"
                    type="number"
                    defaultValue={size}
                    onChange={changeSizeHandler}
                  />
                  <FormHelperText>Schriftgröße</FormHelperText>
                </FormControl>
              </Grid>
            </Grid>
            <br />
            <Button color="secondary" variant="contained" onClick={refreshMap}>
              Refresh
            </Button>
          </Paper>
          <Paper className={styles.paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">Sichtbar</TableCell>
                  <TableCell>Titel</TableCell>
                  <TableCell>Gültigkeit</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {events.map(event => {
                  const isItemSelected = isSelected(event);
                  return (
                    <TableRow
                      hover
                      onClick={() => toggleEvent(event)}
                      role="checkbox"
                      tabIndex={-1}
                      key={event.id}
                      selected={isItemSelected}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox checked={isItemSelected} />
                      </TableCell>
                      <TableCell scope="row" padding="none">
                        {event.headline}
                      </TableCell>
                      <TableCell>
                        {moment.unix(event.onset).format("HH:mm")} -{" "}
                        {moment.unix(event.expires).format("HH:mm")}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
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
        <Grid item xs={12}>
          <Paper className={styles.paper}>
              <Typography variant="h6" component="h1">Unwetter-Warnassistent</Typography>
              <Typography>Ein Produkt des Newsrooms, entwicktelt vom HackingStudio <span role="img" aria-label="Rakete">🚀</span> — <a href="https://www.wdr.de/k/uwa">Informationen &amp; Kontakt</a></Typography>
          </Paper>
          </Grid>
      </Grid>
      <Snackbar
        anchorOrigin={{
          vertical: "top",
          horizontal: "center"
        }}
        open={eventNotFoundOpen}
        onClose={handleEventNotFoundClose}
        autoHideDuration={6000}
      >
        <SnackbarContent
          className={styles.error}
          message={<span>Meldung nicht mehr gültig!</span>}
        />
      </Snackbar>
    </div>
  );
};

export default Events;

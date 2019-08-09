import React, { useState, useCallback, useRef, useLayoutEffect, useEffect } from "react";
import Button from "@material-ui/core/es/Button";
import Checkbox from "@material-ui/core/es/Checkbox";
import Paper from "@material-ui/core/es/Paper";
import TextField from "@material-ui/core/es/TextField";
import FormHelperText from "@material-ui/core/es/FormHelperText";
import FormControl from "@material-ui/core/es/FormControl";
import FormControlLabel from "@material-ui/core/es/FormControlLabel";
import Grid from "@material-ui/core/es/Grid";
import Snackbar from "@material-ui/core/es/Snackbar";
import SnackbarContent from "@material-ui/core/es/SnackbarContent";
import Select from "@material-ui/core/es/Select";
import MenuItem from "@material-ui/core/es/MenuItem";
import Table from "@material-ui/core/es/Table";
import TableBody from "@material-ui/core/es/TableBody";
import TableCell from "@material-ui/core/es/TableCell";
import TableHead from "@material-ui/core/es/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/es/Typography";
import classNames from "classnames";
import moment from "moment";
import queryString from "query-string";

import { RouteComponentProps } from "@reach/router";

import styles from "./Events.module.scss";
import { useFormField } from "../hooks/form";
import Loader from "../util/Loader";

const Events: React.FC<RouteComponentProps> = () => {
  const [date, changeDateHandler_, setDate] = useFormField("");
  const [time, changeTimeHandler_, setTime] = useFormField("");

  const [title, changeTitleHandler] = useFormField("Amtliche Unwetterwarnung");
  const [titleSize, changeTitleSizeHandler] = useFormField("125");

  const [subtitle, changeSubtitleHandler, setSubtitle] = useFormField("");
  const [subtitleSize, changeSubtitleSizeHandler] = useFormField("100");

  const [mode, changeModeHandler] = useFormField("wide");

  const [mapQuery, setMapQuery] = useState("");
  const [mapLoading, setMapLoading] = useState(true);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [initialLoadingComplete, setInitialLoadingComplete] = useState(false);

  const [autoRefresh, setAutoRefresh] = useState(true);
  const changeAutoRefreshHandler = useCallback(ev => setAutoRefresh(JSON.parse(ev.target.value)), []);

  const changeDateHandler = useCallback(
    ev => {
      setAutoRefresh(false);
      changeDateHandler_(ev);
    },
    [changeDateHandler_]
  );

  const changeTimeHandler = useCallback(
    ev => {
      setAutoRefresh(false);
      changeTimeHandler_(ev);
    },
    [changeTimeHandler_]
  );

  const [eventNotFoundOpen, setEventNotFoundOpen] = React.useState(false);

  const dateRef = useRef<HTMLInputElement>();
  const timeRef = useRef<HTMLInputElement>();
  const titleRef = useRef<HTMLTextAreaElement>();
  const subtitleRef = useRef<HTMLTextAreaElement>();

  const [events, setEvents] = useState<any[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<any[]>([]);
  const [disabledEvents, setDisabledEvents] = useState<any[]>([]);

  const onMapLoad = useCallback(() => setMapLoading(false), [setMapLoading]);

  const doMapRefresh = useCallback(
    (theEvents, theDisabledEvents, theSubtitle = null) => {
      if (theSubtitle === null) {
        theSubtitle = subtitle;
      }
      const localMapQuery = queryString.stringify({
        id: theEvents.map((ev: any) => ev.id),
        disabled: theDisabledEvents.map((ev: any) => ev.id),
        title,
        titleSize,
        subtitle: theSubtitle,
        subtitleSize,
        mode
      });

      setMapQuery(localMapQuery);

      if (localMapQuery !== mapQuery) {
        setMapLoading(true);
      }
    },
    [mapQuery, title, titleSize, subtitle, subtitleSize, mode]
  );

  const doEventsRefresh = useCallback(
    async (at, notify = false) => {
      setEventsLoading(true);

      const headers = new Headers();
      headers.append("Pragma", "no-cache");
      headers.append("Cache-Control", "no-cache");

      const init = {
        method: "GET",
        headers
      };

      const req = new Request(`/api/v1/events/current?at=${at}`, {
        cache: "no-cache"
      });

      const newEvents = await (await fetch(req, init)).json();
      const existingIds = events.map(e => e.id);

      if (notify) {
        for (const newEvent of newEvents) {
          if (existingIds.includes(newEvent.id)) {
            continue;
          }
          if (["Minor", "Moderate"].includes(newEvent.severity)) {
            continue;
          }
          if (newEvent["msg_type"] === "Alert" || newEvent["special_type"] === "UpdateAlert") {
            new Notification(`Neue Meldung`, { body: newEvent["event"] });
          } else if (newEvent["msg_type"] === "Cancel") {
            new Notification(`Eine Meldung wurde zurückgezogen`, { body: newEvent.event });
          } else {
            for (const changeSet of newEvent["has_changes"]) {
              if (changeSet["changed_minor"]) {
                new Notification(`Aktualisierung`, { body: newEvent.event });
                continue;
              }
            }
          }
        }
      }

      setEvents(newEvents);
      setFilteredEvents(newEvents);
      setDisabledEvents([]);
      setEventsLoading(false);
      return newEvents;
    },
    [events, setEvents, setFilteredEvents, setEventsLoading]
  );

  const isSelected = useCallback(event => filteredEvents.findIndex(fev => fev === event) !== -1, [filteredEvents]);

  const toggleEvent = useCallback(
    event => {
      let filteredEventsNew;
      let disabledEventsNew;

      if (isSelected(event)) {
        filteredEventsNew = filteredEvents.filter(fev => fev !== event);
        if (["Severe", "Extreme"].includes(event.severity)) {
          disabledEventsNew = disabledEvents.concat([event]);
        }
      } else {
        filteredEventsNew = filteredEvents.concat([event]);
        disabledEventsNew = disabledEvents.filter(fev => fev !== event);
      }

      setFilteredEvents(filteredEventsNew);
      if (disabledEventsNew !== undefined) {
        setDisabledEvents(disabledEventsNew);
      }
      doMapRefresh(filteredEventsNew, disabledEventsNew || []);
    },
    [filteredEvents, disabledEvents, isSelected, doMapRefresh]
  );

  const refreshMap = useCallback(async () => doMapRefresh(filteredEvents, disabledEvents), [
    filteredEvents,
    disabledEvents,
    doMapRefresh
  ]);

  const refreshEvents = useCallback(
    async (notify = false) => {
      const m = moment(`${date}T${time}`);
      const at = m.format("X");
      const events = await doEventsRefresh(at, notify);

      doMapRefresh(events, []);
    },
    [date, time, doMapRefresh, doEventsRefresh]
  );

  // Auto refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        if (!dateRef.current || !timeRef.current) {
          return;
        }

        const now = moment();
        const dateString = now.format("YYYY-MM-DD");
        const timeString = now.format("HH:mm");

        dateRef.current.value = dateString;
        setDate(dateString);

        timeRef.current.value = timeString;
        setTime(timeString);

        refreshEvents(true);
      }, 1000 * 60);
      return () => {
        clearInterval(interval);
      };
    }
  }, [autoRefresh, dateRef, timeRef, setDate, setTime, refreshEvents]);

  // Initial page setup
  useEffect(() => {
    Notification.requestPermission();
  }, []);

  useLayoutEffect(() => {
    if (initialLoadingComplete) {
      return;
    }

    if (!dateRef.current || !timeRef.current) {
      return;
    }

    const qs = queryString.parse(window.location.search);
    let linkedEventId;

    if (qs && qs.id && typeof qs.id === "string") {
      linkedEventId = qs.id;
    }

    const now = moment();
    const dateString = now.format("YYYY-MM-DD");
    const timeString = now.format("HH:mm");

    dateRef.current.value = dateString;
    setDate(dateString);

    timeRef.current.value = timeString;
    setTime(timeString);

    const fetchEvents = async () => {
      const at = now.format("X");
      const events = await doEventsRefresh(at);

      // Draw initial map
      let localText = "Bitte Text einfügen";

      if (titleRef.current) {
        titleRef.current.value = title;
      }

      if (linkedEventId && subtitleRef.current) {
        const linkedEvent = events.find(ev => ev.id === linkedEventId);
        if (!linkedEvent) {
          setEventNotFoundOpen(true);
          setSubtitle(localText);
          subtitleRef.current.value = localText;
          doMapRefresh(events, localText);
          return;
        }
        const warnText = linkedEvent.headline.replace("vor ", "vor\n");
        subtitleRef.current.value = warnText;
        setSubtitle(warnText);
        localText = warnText;
      } else if (subtitleRef && subtitleRef.current) {
        setSubtitle(localText);
        subtitleRef.current.value = localText;
      }

      doMapRefresh(events, [], localText);
    };

    setInitialLoadingComplete(true);
    fetchEvents();
  }, [
    setDate,
    setTime,
    titleRef,
    title,
    setSubtitle,
    setEventNotFoundOpen,
    initialLoadingComplete,
    setInitialLoadingComplete,
    doMapRefresh,
    doEventsRefresh
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
            <Typography variant="h5">Zeitpunkt der Meldung</Typography>
            <Typography variant="subtitle1">
              Zeigt alle Meldungen des DWD zum ausgewähltem Zeitpunkt mit Stufe 2, 3 oder 4 auf der Karte an
            </Typography>
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
            <FormControlLabel
              control={<Checkbox checked={autoRefresh} onChange={changeAutoRefreshHandler} value={!autoRefresh} />}
              label="Automatisch aktualisieren"
            />
            <br />
            <Button color="secondary" variant="contained" onClick={() => refreshEvents()}>
              Anwenden
            </Button>
            {eventsLoading ? <Loader /> : <></>}
          </Paper>
          <Paper className={styles.paper}>
            <Typography variant="h5">Tafeltext anpassen</Typography>
            <Grid container spacing={2}>
              <Grid item xs={9}>
                <FormControl fullWidth>
                  <TextField inputRef={titleRef} margin="normal" onChange={changeTitleHandler} />
                  <FormHelperText>Titel</FormHelperText>
                </FormControl>
                <FormControl fullWidth>
                  <TextField inputRef={subtitleRef} margin="normal" onChange={changeSubtitleHandler} />
                  <FormHelperText>Untertitel</FormHelperText>
                </FormControl>
              </Grid>

              <Grid item xs={3}>
                <FormControl fullWidth>
                  <TextField margin="normal" type="number" defaultValue={titleSize} onChange={changeTitleSizeHandler} />
                  <FormHelperText>Schriftgröße Titel</FormHelperText>
                </FormControl>
                <FormControl fullWidth>
                  <TextField
                    margin="normal"
                    type="number"
                    defaultValue={subtitleSize}
                    onChange={changeSubtitleSizeHandler}
                  />
                  <FormHelperText>Schriftgröße Untertitel</FormHelperText>
                </FormControl>
              </Grid>
            </Grid>
            <br />
            <Button color="secondary" variant="contained" onClick={refreshMap}>
              Anwenden
            </Button>
            <Select label="Format" onChange={changeModeHandler} value={mode}>
              <MenuItem value="wide">16:9</MenuItem>
              <MenuItem value="square">Quadratisch</MenuItem>
            </Select>
          </Paper>
          <Paper className={styles.paper}>
            <Typography variant="h5">Meldungen</Typography>
            <Typography variant="subtitle1">Einzelne Meldungen können aus der Karte ausgeschlossen werden</Typography>
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
                        {moment.unix(event.onset).format("HH:mm")} - {moment.unix(event.expires).format("HH:mm")}
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
              className={classNames(
                styles.image,
                styles.marginBottom,
                mapLoading || eventsLoading || !initialLoadingComplete ? styles.mapLoading : ""
              )}
              src={`/map?${mapQuery}`}
              alt="Map of the event"
              onLoad={onMapLoad}
            />
            {!mapLoading && !eventsLoading && initialLoadingComplete ? (
              <a href={`/map?${mapQuery}`} download className={styles.downloadButton}>
                <Button color="primary" variant="contained">
                  Download
                </Button>
              </a>
            ) : (
              <Loader />
            )}
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper className={styles.paper}>
            <Typography variant="h6" component="h1">
              Unwetter-Warnassistent
            </Typography>
            <Typography>
              Ein Produkt des Newsrooms, entwickelt vom HackingStudio{" "}
              <span role="img" aria-label="Rakete">
                🚀
              </span>{" "}
              — <a href="https://www.wdr.de/k/uwa">Informationen &amp; Kontakt</a>
            </Typography>
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
        <SnackbarContent className={styles.error} message={<span>Meldung nicht mehr gültig!</span>} />
      </Snackbar>
    </div>
  );
};

export default Events;

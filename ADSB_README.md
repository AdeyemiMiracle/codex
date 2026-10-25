# AeroScope ADS-B Altitude Lab

A desktop Python application for finding altitude reports for an aircraft in an
ADS-B message log, listing the observations, and plotting altitude over time.

## Run

From this directory, install the Python dependency and launch the application:

```powershell
python -m pip install -r requirements.txt
python adsb_simulation.py
```

The application initially looks for the original `0116.txt` file at its
configured local path. If the file is elsewhere, use **Browse** to select it.
You can also provide a log path on the command line:

```powershell
python adsb_simulation.py --log "C:\path\to\0116.txt"
```

Enter an aircraft's six-character hexadecimal ICAO address, then choose
**Decode aircraft**. The results table lists each matching timestamp, altitude,
type code, Q bit, and ADS-B frame. Choose **View altitude graph** to open the
aircraft's altitude-versus-time plot.

## Message selection and decoding

- Only the first 400 non-empty messages in the selected file are searched.
- The log format is whitespace-separated, with the message field in column 7.
- The 112-bit ADS-B frame is read from character 15 of that message field.
- The ICAO address is extracted from hexadecimal characters 17–22 of the frame.
- Only type codes 9–18 and 20–22 are included.
- The 12-bit altitude field is extracted from ME bits 9–20. With Q=1, altitude
  is decoded in 25-foot increments (`N × 25 − 1,000 ft`). With Q=0, the
  Gillham/Gray-code altitude is decoded in 100-foot increments.

## Tests

Run the decoder tests with:

```powershell
python -m unittest discover -s tests -v
```

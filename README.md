# dataplex

A multiplexing server for aggregation, analysis and distribution of real-time data and sensor inputs, designed for data-driven performance and sonification.

Sources are multiplexed and aggregated onto a synchronous shared clock, so that each dataframe contains the latest available readings from all sources.

## Concepts

A dataplex session comprises of one or more **sources** and one or more **destinations**.

Supported sources:

- local audio input
- webcam (built-in iSight or external USB)
- Peet Bros Ultimeter weather station range
- Campbell Scientific BWS-200 weather station
- CSV log file

Supported destinations:

- Standard terminal output (stdout)
- CSV log file
- Open Sound Control (OSC) server
- [JSON Datagram Protocol](https://pypi.org/project/jdp/) (JDP) server

## Requirements

### Source: Serial inputs

Including Ultimeter 2100 and BWS-200 weather stations.

```
pip3 install pyserial
```

### Source: Audio

```
brew install portaudio
pip3 install pyaudio
```

### Source: Webcam

```
brew install numpy scipy opencv
pip3 install opencv-python
```

## Usage

dataplex is configured with a .json config file. To run the server:

```
python3 -m dataplex.server -c config/config.json
```

## Background

dataplex was originally created in 2010 for the sound installation [Variable 4](https://jones-bulley.com/variable4/), and has been gradually updated since. It is named in homage to [Ryoji Ikeda](https://raster-media.net/shop/dataplex-2001-05).

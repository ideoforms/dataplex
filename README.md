# dataplex

A multiplexing server for aggregation and distribution of real-time data and sensor inputs.

Supported sources:

- audio in
- webcam (built-in iSight or external USB)
- Peet Bros Ultimeter weather station range
- Campbell Scientific BWS-200 weather station

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

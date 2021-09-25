# SensAI: Sensor-based Atmospheric Intelligence

**SensAI** is a Python package that provides a framework for collecting atmospheric data. Currently using the [EmpAIR](https://www.empa.ch/web/s405/empair) sensor for data collection. The goal of this repository to learn how to collect, interpret and visual the logged data. 

<div align="center">
`Disclaimer: Nothing artificial here.`
</div>

## Installation

Simply install using `conda` environment:

    conda env create -f environment.yml

## Setup

Modify the `sensai/config.yml` file to your liking.

## Usage

### 1. Running logger

    python log.py

### 2. Running web interface:
    
    bokeh serve --show app.py --port 5006 --allow-websocket-origin=<public_ip>

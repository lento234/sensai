# SensAI: Sensor-based Accurate Interpretation

**SensAI** is a Python package that provides a framework for interpreting sensor data. Currently using the [EmpAIR](https://www.empa.ch/web/s405/empair) sensor for data collection. The goal of this repository to learn how to collect, interpret and visual the logged data.

## Installation

Simply install using `conda` environment:

    conda env create -f environment.yml

## Setup

Modify the `sensai/config.yml` file to your liking.

## Usage

### 1. Running logger

    python log.py

### 2. Running web interface:
    
    bokeh serve --show main.py

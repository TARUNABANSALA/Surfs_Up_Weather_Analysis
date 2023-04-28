# Import the dependencies.
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
# reflect an existing database into a new model
Base.prepare(autoload_with=engine)
# reflect the tables
print(Base.classes.keys())
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station
# Create our session (link) from Python to the DB
# session = Session(engine)
#################################################
# Flask Setup
#################################################
app = Flask(__name__)
#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the Climate Data (Honolulu, Hawaii) API!<br/>"
        f"Available Routes:<br/>"
        f"STATIC ROUTES<br/>"
        f"/api/v1.0/precipitation_route/precipitation<br/>"
        f"/api/v1.0/precipitation_route/precipitation/last_year_data<br/>"
        f"/api/v1.0/station_routes<br/>"
        f"/api/v1.0/tobs_route/most_active_station<br/>"
        f"/api/v1.0/tobs_route/most_active_station_last_year_data<br/>"
        f"DYNAMIC ROUTES<br/>"
        f"/api/v1.0/measurement_data/start_date/<start_date><br/>"
        f"/api/v1.0/date_range_data/start_date/<start_date>/end_date/<end_date>"
    )
# A precipitation route that:Returns json with the date as the key and the value as the precipitation
@app.route("/api/v1.0/precipitation_route/precipitation")
def precipitation():
    session = Session(engine)
    results = session.query(Measurement.date, Measurement.prcp).all()
    session.close()
    output = []
    for date, prcp in results: 
        precipitation_data = {}
        precipitation_data[date] = prcp
        output.append(precipitation_data)
    return jsonify(output)

# A precipitation route that:Only returns the jsonified precipitation data for the last year in the database
@app.route("/api/v1.0/precipitation_route/precipitation/last_year_data")
def last_year_data():
    session = Session(engine)
# Starting from the most recent data point in the database. 
    max_date_str = session.query(func.max(Measurement.date)).scalar()
    max_date = datetime.strptime(max_date_str, '%Y-%m-%d').date()
    print(max_date)
# Calculate the date one year from the last date in data set.
    one_year_ago = max_date - timedelta(days=365)
    print(one_year_ago)
    results = session.query(Measurement.date, Measurement.prcp)\
                 .filter(Measurement.date >= one_year_ago)\
                 .all()
    session.close()
    output = []
    for date, prcp in results: 
        last_year_data = {}
        last_year_data[date] = prcp
        output.append(last_year_data)
    return jsonify(output)

# A stations route that:Returns jsonified data of all of the stations in the database 
@app.route("/api/v1.0/station_routes")
def station_routes():
    session = Session(engine)
    results = session.query(Station.station).distinct().all()
    session.close()
    output = []
    for row in results:
        output.append(row._asdict())
    return jsonify(output)

# A tobs route that:Returns jsonified data for the most active station (USC00519281)
@app.route("/api/v1.0/tobs_route/most_active_station")
def most_active_station():
    session = Session(engine)
    results = session.query(Measurement.station, func.count().label('observation_count')).\
        group_by(Measurement.station).\
        order_by(func.count().desc())
# Extracting the most active station from results query and assigning only the station part to a "most_active_station" variable 
    most_active_station_row = results.first()
    most_active_station = most_active_station_row.station
    most_active_station_details = session.query(Measurement.station, Measurement.prcp, Measurement.tobs)\
        .filter(Measurement.station == most_active_station)\
        .all()
    session.close()
    output = []
    for station, prcp, tobs in most_active_station_details: 
        most_active_station_data = {}
        most_active_station_data['station'] = station
        most_active_station_data['prcp'] = float(prcp)
        most_active_station_data['tobs'] = float(tobs)
        output.append(most_active_station_data)
    return jsonify(output)

# A tobs route that: Only returns the jsonified data for the last year of data 
@app.route("/api/v1.0/tobs_route/most_active_station_last_year_data")
def most_active_station_last_year_data():
    session = Session(engine)
    most_active_station_id = 'USC00519281'
# Define the start and end date for the query
    max_date_str = session.query(func.max(Measurement.date)).scalar()
    max_date = datetime.strptime(max_date_str, '%Y-%m-%d').date()
# Calculate the date one year from the last date in data set.
    one_year_ago = max_date - timedelta(days=365)
# Query the last 12 months of temperature observation data for the most active station
    results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active_station_id)\
            .filter(Measurement.date >= one_year_ago)\
            .all()
    session.close()
    output = []
    for date, tobs in results: 
        most_active_station_data_last_year_data = {}
        most_active_station_data_last_year_data['date'] = date
        most_active_station_data_last_year_data['tobs'] = float(tobs)
        output.append(most_active_station_data_last_year_data)
    return jsonify(output)

# API Dynamic Route
# A start route that: Accepts the start date as a parameter from the URL
# Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset
@app.route("/api/v1.0/measurement_data/start_date/<start_date>")
def measurement_data(start_date):
        session = Session(engine)
        results = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))\
                 .filter(Measurement.date >= start_date)\
                 .all()
        session.close()
        output = []
        for min_temp, max_temp, avg_temp in results:
            temp_data = {}
            temp_data["minimum_temperature"] = min_temp
            temp_data["maximum_temperature"] = max_temp
            temp_data["average_temperature"] = avg_temp
            output.append(temp_data)
        return jsonify(output)
    
# A start/end route that:Accepts the start and end dates as parameters from the URL 
# Returns the min, max, and average temperatures calculated from the given start date to the given end date 
@app.route("/api/v1.0/date_range_data/start_date/<start_date>/end_date/<end_date>")
def date_range_data(start_date, end_date):
    session = Session(engine)
    results = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)) \
                     .filter(Measurement.date >= start_date) \
                     .filter(Measurement.date <= end_date) \
                     .all()
    session.close()
    output = []
    for min_temp, max_temp, avg_temp in results:
        temp_data = {}
        temp_data["minimum_temperature"] = min_temp
        temp_data["maximum_temperature"] = max_temp
        temp_data["average_temperature"] = avg_temp
        output.append(temp_data)
    return jsonify(output)

if __name__ == '__main__':
    app.run(debug=True)
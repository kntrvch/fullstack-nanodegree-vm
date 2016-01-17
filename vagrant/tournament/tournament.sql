-- Table definitions for the tournament project.

CREATE DATABASE tournament;

CREATE TABLE players ( id SERIAL,
                       name VARCHAR,
                       wins INTEGER,
                       matches INTEGER );

CREATE TABLE matches ( id SERIAL,
                       winner INTEGER,
                       loser INTEGER );
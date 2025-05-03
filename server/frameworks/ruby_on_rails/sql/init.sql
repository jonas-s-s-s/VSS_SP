CREATE TABLE sample_data
(
    id    SERIAL PRIMARY KEY,
    title TEXT NOT NULL
);

INSERT INTO sample_data (title)
VALUES ('Hello World'),
       ('Postgres'),
       ('Dockerized App'),
       ('Sample Data Entry');
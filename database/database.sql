DROP DATABASE Automata;
CREATE DATABASE Automata;

use Automata;

DROP TABLE Recent;
CREATE TABLE Recent (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id bigint,
    fa_name VARCHAR(255),
    states VARCHAR(255),
    alphabets VARCHAR(255),
    initial_state VARCHAR(255),
    final_states VARCHAR(255),
    transitions VARCHAR(255),
    updated_at DATE
);


CREATE DATABASE Automata;

use Automata;

CREATE TABLE History (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    fa_name VARCHAR(255),
    state VARCHAR(255),
    alphabet VARCHAR(255),
    initial_state VARCHAR(255),
    final_state VARCHAR(255),
    transition VARCHAR(255),
    updated_at DATE
);


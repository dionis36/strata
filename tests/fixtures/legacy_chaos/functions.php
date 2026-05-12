<?php
// Legacy procedural functions
require_once 'config.php';

function connect_db() {
    global $db_connection; // Requirement 3C
    $db_connection = mysql_connect(DB_HOST, DB_USER, DB_PASS); // Requirement 6 & 14
    return $db_connection;
}

function get_user($id) {
    global $db_connection;
    $sql = "SELECT * FROM users WHERE id = " . $id;
    return mysql_query($sql, $db_connection);
}
